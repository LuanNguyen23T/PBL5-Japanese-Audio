"""
Test: So sánh gen audio CÓ và KHÔNG có reference audio (giọng mẫu)

Kịch bản:
  Case A — Chỉ dùng model tải sẵn, không có reference audio
  Case B — Dùng model tải sẵn + reference audio (clone ngữ điệu)
  Case C — Không có model → báo lỗi rõ ràng (không thể gen)

Chạy lệnh:
  docker compose run --rm sbvits2 python test_reference_audio.py

Kết quả lưu tại:
  output/test_no_ref.wav    ← Case A
  output/test_with_ref.wav  ← Case B (nếu có file mẫu)
"""

import os
import io
import time
from pathlib import Path

import soundfile as sf
import numpy as np
import warnings
warnings.filterwarnings("ignore")
os.environ["PYTHONWARNINGS"] = "ignore"

def ok(msg):  print(f"  ✅ {msg}")
def info(msg): print(f"  ℹ️  {msg}")
def err(msg):  print(f"  ❌ {msg}")
def sep(title=""):
    print()
    print("=" * 60)
    if title: print(f"  {title}")
    print("=" * 60)

# ==============================================================
# CẤU HÌNH TEST
# ==============================================================

# Model đã tải về (thay bằng tên model bạn đã download_models.py)
TEST_MODEL = "jvnv-F1-jp"

# Text tiếng Nhật muốn test
TEST_TEXT = "おはようございます。今日もよろしくお願いします。"

# (Tuỳ chọn) Đường dẫn tới file audio mẫu để clone ngữ điệu
# Để None nếu chỉ muốn test Case A và Case C
REFERENCE_AUDIO_PATH = None  # hoặc "/app/output/multi_speaker_test.wav"

# ==============================================================

def load_model(model_holder, model_name: str):
    """Tải model từ thư mục /app/models/<model_name>"""
    model_dir = Path("/app/models") / model_name
    model_files = list(model_dir.glob("*.safetensors")) + list(model_dir.glob("*.pt"))
    if not model_files:
        raise FileNotFoundError(
            f"Không tìm thấy file model trong '{model_dir}'.\n"
            f"  → Hãy chạy: python download_models.py trước."
        )
    return model_holder.get_model(model_name, str(model_files[0]))


def synthesize(tts_model, text: str, ref_path=None, style_weight=1.0) -> tuple:
    """Gọi inference và trả về (sample_rate, audio_array)"""
    from style_bert_vits2.constants import Languages
    has_ref = ref_path is not None
    return tts_model.infer(
        text=text,
        language=Languages.JP,
        speaker_id=0,
        reference_audio_path=ref_path,
        sdp_ratio=0.2,
        style="Neutral",
        style_weight=style_weight,
        pitch_scale=1.0,
        intonation_scale=1.2 if has_ref else 1.0,
        noise=0.6,
        noise_w=0.8,
        length=1.0,
    )


def save_wav(audio, sr, path: str):
    max_amp = np.abs(audio).max()
    if max_amp > 1.0:
        audio = (audio / max_amp) * 0.95
    sf.write(path, audio, sr)
    size_kb = os.path.getsize(path) / 1024
    ok(f"Đã lưu: {path}  ({size_kb:.1f} KB)")


def main():
    sep("Style-Bert-VITS2 — Reference Audio Test")
    print(f"  Model  : {TEST_MODEL}")
    print(f"  Text   : {TEST_TEXT}")
    print(f"  Ref    : {REFERENCE_AUDIO_PATH or '(không có)'}")

    try:
        from style_bert_vits2.tts_model import TTSModelHolder
        from style_bert_vits2.nlp import bert_models
        from style_bert_vits2.constants import Languages
    except ImportError as e:
        err(f"Chưa cài style-bert-vits2: {e}")
        return

    # Pre-load BERT
    info("Đang tải BERT models...")
    try:
        bert_models.load_tokenizer(Languages.JP, "ku-nlp/deberta-v2-large-japanese-char-wwm")
        bert_models.load_model(Languages.JP, "ku-nlp/deberta-v2-large-japanese-char-wwm")
        ok("BERT models loaded.")
    except Exception as e:
        err(f"Không tải được BERT: {e}")
        return

    model_holder = TTSModelHolder(Path("/app/models"), "cpu")
    os.makedirs("/app/output", exist_ok=True)

    # ─────────────────────────────────────────────────────────
    sep("CASE A — Chỉ dùng model (không có reference audio)")
    # ─────────────────────────────────────────────────────────
    info("Giải thích: Giọng ra hoàn toàn dựa vào model đã tải. Style mặc định = Neutral.")
    try:
        tts_model = load_model(model_holder, TEST_MODEL)
        t0 = time.time()
        sr, audio = synthesize(tts_model, TEST_TEXT, ref_path=None, style_weight=1.0)
        ok(f"Tổng hợp xong trong {time.time()-t0:.1f}s")
        save_wav(audio, sr, "/app/output/test_no_ref.wav")
    except FileNotFoundError as e:
        err(str(e))
    except Exception as e:
        err(f"Lỗi: {e}")
        import traceback; traceback.print_exc()

    # ─────────────────────────────────────────────────────────
    sep("CASE B — Model + Reference Audio (clone ngữ điệu)")
    # ─────────────────────────────────────────────────────────
    if REFERENCE_AUDIO_PATH and os.path.exists(REFERENCE_AUDIO_PATH):
        info(f"File mẫu: {REFERENCE_AUDIO_PATH}")
        info("Giải thích: model vẫn cần thiết, nhưng ngữ điệu sẽ học theo file mẫu (style_weight=5.0).")
        try:
            t0 = time.time()
            sr, audio = synthesize(tts_model, TEST_TEXT, ref_path=REFERENCE_AUDIO_PATH, style_weight=5.0)
            ok(f"Tổng hợp xong trong {time.time()-t0:.1f}s")
            save_wav(audio, sr, "/app/output/test_with_ref.wav")
            info("So sánh 2 file: test_no_ref.wav vs test_with_ref.wav để nghe sự khác biệt ngữ điệu.")
        except Exception as e:
            err(f"Lỗi Case B: {e}")
    else:
        info("CASE B bị bỏ qua — REFERENCE_AUDIO_PATH chưa được đặt hoặc file không tồn tại.")
        info("→ Để test: đặt REFERENCE_AUDIO_PATH trong file này trỏ tới file .wav bất kỳ.")

    # ─────────────────────────────────────────────────────────
    sep("CASE C — KHÔNG có model (chỉ có reference audio)")
    # ─────────────────────────────────────────────────────────
    info("Giải thích: Style-Bert-VITS2 BẮT BUỘC phải có model .safetensors.")
    info("Reference audio chỉ bổ sung ngữ điệu, không thể thay thế model.")
    fake_model = "model-khong-ton-tai"
    try:
        load_model(model_holder, fake_model)
        err("Lỗi logic: đáng lẽ phải raise exception!")
    except FileNotFoundError as e:
        ok(f"Đúng như kỳ vọng — hệ thống báo lỗi:\n       {e}")

    sep("KẾT LUẬN")
    print("  • Không có model → KHÔNG thể gen audio (Case C).")
    print("  • Có model, không có ref audio → Gen được, giọng theo model (Case A).")
    print("  • Có model + ref audio → Gen được, ngữ điệu học từ file mẫu (Case B).")
    print()


if __name__ == "__main__":
    main()
