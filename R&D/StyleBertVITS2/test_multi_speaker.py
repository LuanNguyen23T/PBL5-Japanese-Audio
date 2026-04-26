import os
import time
from pathlib import Path
import soundfile as sf
import numpy as np

# Suppress warnings
import warnings
warnings.filterwarnings("ignore")
os.environ["PYTHONWARNINGS"] = "ignore"

def info(msg): print(f"  ℹ️  {msg}")
def ok(msg): print(f"  ✅ {msg}")
def err(msg): print(f"  ❌ {msg}")

def main():
    print("="*60)
    print("  Style-Bert-VITS2 R&D: Multi-Speaker Script Test")
    print("="*60)

    try:
        from style_bert_vits2.tts_model import TTSModelHolder
        from style_bert_vits2.constants import Languages
        from style_bert_vits2.nlp import bert_models
    except ImportError as e:
        err(f"Failed to import style-bert-vits2: {e}")
        return

    # Pre-load BERT models to avoid path assertion errors
    info("Pre-loading BERT models...")
    try:
        bert_models.load_tokenizer(Languages.JP, "ku-nlp/deberta-v2-large-japanese-char-wwm")
        bert_models.load_model(Languages.JP, "ku-nlp/deberta-v2-large-japanese-char-wwm")
    except Exception as e:
        err(f"Failed to pre-load BERT models: {e}")
        return

    # Initialize model holder
    model_holder = TTSModelHolder(Path("/app/models"), "cpu")
    
    # Kịch bản test nhiều người nói (Mô phỏng Input từ người dùng)
    dialogues = [
        {"speaker": "Người dẫn chuyện", "text": "一番、学校で四人が話しています。この会話を聞いて、質問に答えてください。"},
        {"speaker": "男の子", "text": "先生、来週の遠足の持ち物は、もう決まりましたか。"},
        {"speaker": "先生", "text": "はい、お弁当と水筒、それから帽子を持ってきてください。暑くなるかもしれませんからね。"},
        {"speaker": "姉", "text": "先生、弟は食べ物のアレルギーがあるので、おやつは持っていかないほうがいいでしょうか。"},
        {"speaker": "先生", "text": "そうですね。心配なら、おやつは持ってこなくても大丈夫ですよ。その代わり、お弁当に食べられるものを入れてください。"},
        {"speaker": "おじいさん", "text": "私も当日は駅まで送っていこうと思っていますが、集合時間は何時ですか。"},
        {"speaker": "先生", "text": "朝八時半までに学校の前に集まってください。遅れないようにお願いします。"},
        {"speaker": "男の子", "text": "わかりました。ぼく、前の日に持ち物を全部準備します。"},
        {"speaker": "Người dẫn chuyện", "text": "男の子は、このあとまず何をしますか。"}
    ]

    # Cấu hình giọng đọc cho từng nhãn (Mô phỏng System Mapping)
    # Giả sử file test_output.wav là file audio người dùng upload để lấy "Ngữ điệu"
    dummy_reference_audio = "/app/output/test_output.wav"
    if not os.path.exists(dummy_reference_audio):
        dummy_reference_audio = None
        info("No reference audio found, running without style transfer.")

    speaker_config = {
        "Người dẫn chuyện": {
            "model_name": "jvnv-F1-jp", # Nữ chuẩn
            "style": "Neutral",
            "reference_audio": None,
            "sdp_ratio": 0.2,
            "pitch_scale": 1.0,
        },
        "男の子": {
            "model_name": "jp-extra-cool-young", # Bé trai trẻ
            "style": "Neutral",
            "reference_audio": None,
            "sdp_ratio": 0.2,
            "pitch_scale": 1.05, # Tăng pitch chút xíu cho ra dáng trẻ con hơn
        },
        "先生": {
            "model_name": "jvnv-F2-jp", # Nữ trầm, chững chạc
            "style": "Neutral",
            "reference_audio": None,
            "sdp_ratio": 0.2,
            "pitch_scale": 1.0,
        },
        "姉": {
            "model_name": "jp-extra-amazing", # Nữ dễ thương trẻ trung
            "style": "Neutral",
            "reference_audio": None,
            "sdp_ratio": 0.2,
            "pitch_scale": 1.0,
        },
        "おじいさん": {
            "model_name": "jvnv-M2-jp", # Nam trầm / Người già
            "style": "Neutral",
            "reference_audio": None,
            "sdp_ratio": 0.2,
            "pitch_scale": 0.95, # Giảm pitch cho giọng già hơn
        }
    }

    # Lưu cache các model đã load để không phải load lại nhiều lần
    loaded_models = {}

    all_audio_chunks = []
    sample_rate = 44100
    
    # Khoảng lặng giữa các câu thoại (0.5s)
    pause_duration = 0.5
    pause_audio = np.zeros(int(sample_rate * pause_duration), dtype=np.float32)

    t_start = time.time()

    for i, line in enumerate(dialogues):
        speaker = line["speaker"]
        text = line["text"]
        config = speaker_config[speaker]
        model_name = config["model_name"]

        info(f"[{speaker}] ({model_name}): {text}")

        # Load model nếu chưa load
        if model_name not in loaded_models:
            try:
                model_dir_path = Path("/app/models") / model_name
                model_files = list(model_dir_path.glob("*.safetensors")) + list(model_dir_path.glob("*.pt"))
                if not model_files:
                    err(f"No model file found for {model_name}")
                    return
                model_path_str = str(model_files[0])
                loaded_models[model_name] = model_holder.get_model(model_name, model_path_str)
            except Exception as e:
                err(f"Failed to load model {model_name}: {e}")
                return
        
        tts_model = loaded_models[model_name]

        # Generate Audio
        try:
            sr, audio = tts_model.infer(
                text=text,
                language=Languages.JP,
                speaker_id=0,
                reference_audio_path=config["reference_audio"],
                sdp_ratio=config["sdp_ratio"],
                style=config["style"],
                pitch_scale=config.get("pitch_scale", 1.0),
                noise=0.6,
                noise_w=0.8,
                length=1.0,
            )
            sample_rate = sr
            
            # CHÚ Ý: Đôi khi các style có cảm xúc mạnh (như Happy) sẽ có biên độ âm thanh quá lớn (> 1.0)
            # Điều này sẽ gây ra hiện tượng rè (clipping distortion) khi lưu bằng soundfile.
            # Chúng ta cần chuẩn hóa (normalize) từng đoạn audio trước khi ghép
            max_amp = np.abs(audio).max()
            if max_amp > 1.0:
                audio = (audio / max_amp) * 0.95
                
            all_audio_chunks.append(audio)
            
            # Thêm khoảng lặng sau câu thoại (trừ câu cuối)
            if i < len(dialogues) - 1:
                all_audio_chunks.append(pause_audio)
                
        except Exception as e:
            err(f"Synthesis failed for line {i}: {e}")
            import traceback
            traceback.print_exc()
            return

    # Gộp tất cả audio lại
    info("Merging audio clips...")
    merged_audio = np.concatenate(all_audio_chunks)
    
    # Chuẩn hóa (Normalize) lần cuối cho toàn bộ file ghép để loại bỏ hoàn toàn nhiễu rè do vỡ tiếng
    overall_max = np.abs(merged_audio).max()
    if overall_max > 1.0:
        merged_audio = (merged_audio / overall_max) * 0.95

    output_path = "/app/output/multi_speaker_test.wav"
    sf.write(output_path, merged_audio, sample_rate)
    
    total_time = time.time() - t_start
    ok(f"Multi-speaker synthesis complete! Total time: {total_time:.1f}s")
    ok(f"Saved to: {output_path}")

if __name__ == "__main__":
    main()
