import os
import io
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import soundfile as sf
import numpy as np

import warnings
warnings.filterwarnings("ignore")
os.environ["PYTHONWARNINGS"] = "ignore"

try:
    from style_bert_vits2.tts_model import TTSModelHolder
    from style_bert_vits2.constants import Languages
    from style_bert_vits2.nlp import bert_models
except ImportError as e:
    raise RuntimeError(f"Failed to import style-bert-vits2: {e}")

# Pre-load BERT models at startup
print("Pre-loading BERT models...")
try:
    bert_models.load_tokenizer(Languages.JP, "ku-nlp/deberta-v2-large-japanese-char-wwm")
    bert_models.load_model(Languages.JP, "ku-nlp/deberta-v2-large-japanese-char-wwm")
except Exception as e:
    print(f"Warning: Failed to pre-load BERT models: {e}")

# Initialize model holder globally
model_holder = TTSModelHolder(Path("/app/models"), "cpu")
loaded_models = {}

app = FastAPI(title="Style-Bert-VITS2 Multi-Speaker TTS API")

class DialogueLine(BaseModel):
    speaker: str
    text: str

class SpeakerConfig(BaseModel):
    model_name: str
    style: str = "Neutral"
    pitch_scale: float = 1.0
    sdp_ratio: float = 0.2
    reference_audio_path: Optional[str] = None

class TTSRequest(BaseModel):
    dialogues: List[DialogueLine]
    speaker_configs: Dict[str, SpeakerConfig]
    dialogue_pause: float = 0.5
    narrator_pause: float = 2.5

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/tts/multi-speaker")
def generate_multi_speaker_tts(request: TTSRequest):
    if not request.dialogues:
        raise HTTPException(status_code=400, detail="Dialogues cannot be empty.")

    all_audio_chunks = []
    sample_rate = 44100

    for i, line in enumerate(request.dialogues):
        speaker = line.speaker
        text = line.text
        
        if speaker not in request.speaker_configs:
            raise HTTPException(status_code=400, detail=f"Configuration for speaker '{speaker}' not found.")
            
        config = request.speaker_configs[speaker]
        model_name = config.model_name

        # Load model if not loaded
        if model_name not in loaded_models:
            try:
                model_dir_path = Path("/app/models") / model_name
                model_files = list(model_dir_path.glob("*.safetensors")) + list(model_dir_path.glob("*.pt"))
                if not model_files:
                    raise HTTPException(status_code=404, detail=f"No model file found for {model_name}")
                model_path_str = str(model_files[0])
                loaded_models[model_name] = model_holder.get_model(model_name, model_path_str)
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to load model {model_name}: {e}")
        
        tts_model = loaded_models[model_name]

        # Generate Audio
        try:
            ref_path = config.reference_audio_path
            temp_ref_file = None
            
            # If reference_audio_path is a URL, download it
            if ref_path and (ref_path.startswith("http://") or ref_path.startswith("https://")):
                print(f"Downloading reference audio from {ref_path}...")
                import httpx
                import tempfile
                
                resp = httpx.get(ref_path)
                if resp.status_code == 200:
                    temp_ref_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
                    temp_ref_file.write(resp.content)
                    temp_ref_file.close()
                    ref_path = temp_ref_file.name
                else:
                    print(f"Failed to download reference audio: {resp.status_code}")
                    ref_path = None

            # Kiểm tra xem style có tồn tại trong model không, nếu không thì fallback
            actual_style = config.style
            if hasattr(tts_model, "style2id") and actual_style not in tts_model.style2id:
                if "Neutral" in tts_model.style2id:
                    actual_style = "Neutral"
                elif tts_model.style2id:
                    actual_style = list(tts_model.style2id.keys())[0]
                else:
                    actual_style = "Neutral"

            # Khi có reference audio, tăng style_weight để ngữ điệu được học rõ hơn
            # Mặc định thư viện là 1.0 - không đủ để cảm nhận sự khác biệt
            has_ref_audio = ref_path is not None
            style_weight = 2.0 if has_ref_audio else 1.0

            sr, audio = tts_model.infer(
                text=text,
                language=Languages.JP,
                speaker_id=0,
                reference_audio_path=ref_path,
                sdp_ratio=config.sdp_ratio,
                style=actual_style,
                style_weight=style_weight,
                pitch_scale=config.pitch_scale,
                intonation_scale=1.1 if has_ref_audio else 1.0,
                noise=0.6,
                noise_w=0.6,
                length=1.0,
            )
            
            # Cleanup temp file
            if temp_ref_file:
                try:
                    os.unlink(temp_ref_file.name)
                except:
                    pass
            sample_rate = sr
            
            # Normalize to prevent clipping distortion
            max_amp = np.abs(audio).max()
            if max_amp > 1.0:
                audio = (audio / max_amp) * 0.95
                
            all_audio_chunks.append(audio)
            
            # Add pause between lines
            if i < len(request.dialogues) - 1:
                next_speaker = request.dialogues[i+1].speaker
                
                if speaker == "Người dẫn chuyện" or next_speaker == "Người dẫn chuyện":
                    pause_dur = request.narrator_pause
                else:
                    pause_dur = request.dialogue_pause
                    
                pause_audio = np.zeros(int(sample_rate * pause_dur), dtype=np.float32)
                all_audio_chunks.append(pause_audio)
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Synthesis failed for line {i}: {e}")

    # Merge audio clips
    if not all_audio_chunks:
        raise HTTPException(status_code=500, detail="Failed to generate any audio")
        
    merged_audio = np.concatenate(all_audio_chunks)
    
    # Final normalization
    overall_max = np.abs(merged_audio).max()
    if overall_max > 1.0:
        merged_audio = (merged_audio / overall_max) * 0.95

    # Write to buffer
    buffer = io.BytesIO()
    sf.write(buffer, merged_audio, sample_rate, format='WAV')
    buffer.seek(0)
    
    return StreamingResponse(buffer, media_type="audio/wav", headers={
        "Content-Disposition": f"attachment; filename=multi_speaker.wav"
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=7861)
