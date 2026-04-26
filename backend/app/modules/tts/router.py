"""
TTS Router — sử dụng Style-Bert-VITS2 Gradio API (cổng 7861).
Sử dụng 1 instance GradioClient duy nhất để giữ nguyên session_hash và state.
Lưu file WAV cục bộ, KHÔNG upload Cloudinary.
"""

import logging
import io
import os
import uuid
from datetime import datetime
import threading
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.security import get_current_user
from app.modules.users.models import User
from app.modules.tts.schemas import TTSGenerateRequest, TTSGenerateResponse
from pydub import AudioSegment
from gradio_client import Client as GradioClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tts", tags=["tts"])

# Style-Bert-VITS2 Gradio server (cổng 7861)
TTS_SERVICE_URL = "http://127.0.0.1:7861"

# Bell sound paths
_GENERATED_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "generated")
BELL_START_PATH = os.path.normpath(os.path.join(_GENERATED_DIR, "Bell_dau.wav"))
BELL_END_PATH = os.path.normpath(os.path.join(_GENERATED_DIR, "Bell_cuoi.wav"))

# Output directory for generated audio
OUTPUT_DIR = os.path.normpath(os.path.join(_GENERATED_DIR, "tts_output"))
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Thread pool for blocking gradio_client calls
_executor = ThreadPoolExecutor(max_workers=2)
_tts_lock = threading.Lock()

# Global GradioClient instance to maintain session_hash across requests
_gc_instance = None
_loaded_model_cache: dict = {"model_name": None, "model_path": None, "style": "Neutral", "speaker": None}

def _get_gc() -> GradioClient:
    global _gc_instance
    if _gc_instance is None:
        logger.info("Initializing GradioClient...")
        _gc_instance = GradioClient(TTS_SERVICE_URL)
    return _gc_instance

def _ensure_model_loaded(gc: GradioClient, model_name: str) -> dict:
    """Load model into SBV2 if not already loaded. Returns {style, speaker, model_path}."""
    global _loaded_model_cache

    if _loaded_model_cache["model_name"] == model_name:
        return _loaded_model_cache

    logger.info(f"Loading TTS model: {model_name}")

    files_result = gc.predict(model_name=model_name, api_name="/update_model_files_for_gradio")
    model_path = files_result["value"] if isinstance(files_result, dict) else files_result

    load_result = gc.predict(model_name=model_name, model_path_str=model_path, api_name="/get_model_for_gradio")

    styles_data = load_result[0]
    speaker_data = load_result[1]
    style = styles_data["value"] if isinstance(styles_data, dict) else "Neutral"
    speaker = speaker_data["value"] if isinstance(speaker_data, dict) else model_name

    _loaded_model_cache = {
        "model_name": model_name,
        "model_path": model_path,
        "style": style,
        "speaker": speaker,
    }

    logger.info(f"Model loaded: {model_name}, style={style}, speaker={speaker}")
    return _loaded_model_cache

def _generate_single_tts(
    gc: GradioClient,
    text: str,
    model_name: str,
    style: str = "Neutral",
    sdp_ratio: float = 0.2,
    pitch_scale: float = 1.0,
    reference_audio_path: str = None,
) -> str:
    """Generate TTS for a single text. Returns path to WAV file."""
    cache = _ensure_model_loaded(gc, model_name)

    result = gc.predict(
        model_name=model_name,
        model_path=cache["model_path"],
        text=text,
        language="JP",
        reference_audio_path=reference_audio_path,
        sdp_ratio=sdp_ratio,
        noise_scale=0.6,
        noise_scale_w=0.8,
        length_scale=1.0,
        line_split=True,
        split_interval=0.5,
        assist_text="",
        assist_text_weight=1.0,
        use_assist_text=False,
        style=style if style != "モデルをロードしてください" else cache["style"],
        style_weight=5.0,
        kata_tone_json_str="",
        use_tone=False,
        speaker=cache["speaker"],
        pitch_scale=pitch_scale,
        intonation_scale=1.0,
        api_name="/tts_fn",
    )

    if not result or len(result) < 2 or not result[1]:
        raise RuntimeError(f"TTS returned no audio: {result}")

    info = result[0]
    audio_path = result[1]
    logger.info(f"TTS single done: {info}")
    return audio_path

def _run_pipeline(request: TTSGenerateRequest) -> bytes:
    """Run the full multi-speaker TTS pipeline (blocking). Returns WAV bytes."""
    with _tts_lock:
        gc = _get_gc()
        audio_segments: list[AudioSegment] = []

        dialogue_pause_ms = int((request.dialogue_pause or 0.5) * 1000)
        narrator_pause_ms = int((request.narrator_pause or 2.5) * 1000)

        for i, line in enumerate(request.dialogues):
            if line.speaker == "__BELL_START__":
                if os.path.exists(BELL_START_PATH):
                    audio_segments.append(AudioSegment.from_wav(BELL_START_PATH))
                else:
                    logger.warning(f"Bell_dau not found: {BELL_START_PATH}")
                continue

            if line.speaker == "__BELL_END__":
                if os.path.exists(BELL_END_PATH):
                    audio_segments.append(AudioSegment.from_wav(BELL_END_PATH))
                else:
                    logger.warning(f"Bell_cuoi not found: {BELL_END_PATH}")
                continue

            cfg = request.speaker_configs.get(line.speaker)
            model_name = cfg.model_name if cfg else "jvnv-F1-jp"
            style = cfg.style if cfg else "Neutral"
            sdp_ratio = cfg.sdp_ratio if cfg else 0.2
            pitch_scale = cfg.pitch_scale if cfg else 1.0
            
            ref_path = None
            if cfg and cfg.reference_audio_url:
                filename = cfg.reference_audio_url.split("/")[-1]
                local_path = os.path.join(OUTPUT_DIR, filename)
                if os.path.exists(local_path):
                    ref_path = local_path

            logger.info(f"[{i+1}/{len(request.dialogues)}] speaker={line.speaker}, model={model_name}, text={line.text[:50]}")

            audio_path = _generate_single_tts(
                gc, text=line.text, model_name=model_name,
                style=style, sdp_ratio=sdp_ratio, pitch_scale=pitch_scale,
                reference_audio_path=ref_path
            )

            seg = AudioSegment.from_file(audio_path, format="wav")
            audio_segments.append(seg)

            if i < len(request.dialogues) - 1:
                is_narrator = line.speaker in ("Người dẫn chuyện", "Giọng câu hỏi")
                pause_ms = narrator_pause_ms if is_narrator else dialogue_pause_ms
                audio_segments.append(AudioSegment.silent(duration=pause_ms))

        if not audio_segments:
            raise RuntimeError("No audio segments generated")

        final = audio_segments[0]
        for seg in audio_segments[1:]:
            final += seg

        buf = io.BytesIO()
        final.export(buf, format="wav")
        return buf.getvalue()

@router.post("/generate-script", response_model=TTSGenerateResponse)
async def generate_script(
    request: TTSGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        audio_bytes = await loop.run_in_executor(_executor, _run_pipeline, request)

        # Save locally
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_id = uuid.uuid4().hex[:8]
        filename = f"{request.title or 'tts'}_{timestamp}_{file_id}.wav"
        filepath = os.path.join(OUTPUT_DIR, filename)

        seg = AudioSegment.from_file(io.BytesIO(audio_bytes), format="wav")
        seg.export(filepath, format="wav")
        logger.info(f"Audio saved: {filepath} ({os.path.getsize(filepath)} bytes)")

        file_url = f"/api/tts/audio/{filename}"

        return TTSGenerateResponse(
            audio_id=file_id,
            file_name=filename,
            file_url=file_url,
        )

    except Exception as exc:
        logger.error(f"TTS generation failed: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/audio/{filename}")
async def serve_audio(filename: str):
    """Serve generated audio file."""
    filepath = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(filepath, media_type="audio/wav", filename=filename)


@router.post("/upload-sample")
async def upload_sample(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Upload reference audio for style cloning."""
    try:
        if not file.filename.lower().endswith((".wav", ".mp3", ".m4a")):
            raise HTTPException(status_code=400, detail="Chỉ hỗ trợ file WAV, MP3, M4A")
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_id = uuid.uuid4().hex[:8]
        ext = os.path.splitext(file.filename)[1]
        filename = f"sample_{timestamp}_{file_id}{ext}"
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        with open(filepath, "wb") as f:
            f.write(await file.read())
            
        return {"file_url": f"/api/tts/audio/{filename}"}
    except Exception as exc:
        logger.error(f"Failed to upload sample: {exc}")
        raise HTTPException(status_code=500, detail="Upload failed")


@router.delete("/upload-sample/{filename}")
async def delete_sample(
    filename: str,
    current_user: User = Depends(get_current_user),
):
    """Delete uploaded reference audio."""
    try:
        # Validate filename to prevent path traversal
        if not filename.startswith("sample_") or ".." in filename or "/" in filename:
            raise HTTPException(status_code=400, detail="Invalid filename")
            
        filepath = os.path.join(OUTPUT_DIR, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            return {"message": "Deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="File not found")
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Failed to delete sample: {exc}")
        raise HTTPException(status_code=500, detail="Delete failed")


@router.get("/models")
async def list_available_models(
    current_user: User = Depends(get_current_user),
):
    """Fetch available models by scanning SBV2 model_assets directory."""
    try:
        import json
        
        # SBV2 directory path
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        sbv2_dir = os.path.normpath(os.path.join(backend_dir, "..", "Style-Bert-VITS2-Mac", "model_assets"))
        
        if not os.path.exists(sbv2_dir):
            logger.warning(f"SBV2 models dir not found: {sbv2_dir}")
            return {"models": []}

        model_list = []
        for entry in os.scandir(sbv2_dir):
            if entry.is_dir():
                cfg_path = os.path.join(entry.path, "config.json")
                if os.path.exists(cfg_path):
                    try:
                        with open(cfg_path, "r", encoding="utf-8") as f:
                            cfg = json.load(f)
                            styles = list(cfg.get("data", {}).get("style2id", {}).keys())
                            if not styles:
                                styles = ["Neutral"]
                            model_list.append({
                                "id": entry.name,
                                "model_id": entry.name,
                                "styles": styles,
                            })
                    except Exception as e:
                        logger.error(f"Error reading config for {entry.name}: {e}")

        return {"models": model_list}

    except Exception as exc:
        logger.error(f"Failed to list models: {exc}")
        raise HTTPException(status_code=500, detail="Failed to load models list")
