# 🎓 JLPT Audio Splitter - Hướng dẫn sử dụng

> Tách audio đề thi JLPT thành mondai và câu hỏi, tự động tạo script tiếng Nhật

## 🚀 Quick Start (3 bước)

### Bước 1: Cài đặt

```bash
# Cài FFmpeg
brew install ffmpeg

# Cài Python packages
pip install -r ../../requirements.txt

# Tạo file .env với API key (miễn phí)
echo "GOOGLE_API_KEY=your_key_here" > .env
```

Lấy API key miễn phí: https://makersuite.google.com/app/apikey

### Bước 2: Tách Audio

```bash
python3 audio_splitter.py input/jlpt_n2.mp3
```

Kết quả:
```
output/mondai/
├── mondai_1/
│   ├── mondai_1.mp3
│   └── questions/
│       ├── question_1.mp3
│       ├── question_2.mp3
│       └── ...
├── mondai_2/
│   └── ...
└── ...
```

### Bước 3: Tạo Script tiếng Nhật

```bash
python3 audio_to_text.py output/mondai --batch
```

Kết quả:
```
output/mondai/
├── mondai_1/
│   ├── mondai_1.mp3
│   ├── mondai_1.txt      ← Script mới
│   └── questions/
│       ├── question_1.mp3
│       ├── question_1.txt  ← Script mới
│       └── ...
└── ...
```

**Xong!** 🎉

---

## 📖 Chi tiết

### 1. audio_splitter.py - Tách Audio

**Cơ bản:**
```bash
python3 audio_splitter.py <file_audio>
```

**Ví dụ:**
```bash
python3 audio_splitter.py input/jlpt_n2.mp3
python3 audio_splitter.py input/jlpt_n2.mp3 my_output  # Chỉ định thư mục output
```

**Output:**
- `output/transcript.json` - Transcript đầy đủ
- `output/structure.json` - Cấu trúc mondai/questions
- `output/mondai/mondai_X/` - Các thư mục mondai
  - `mondai_X.mp3` - Audio mondai chính
  - `questions/` - Thư mục chứa questions
    - `question_Y.mp3` - Audio từng câu hỏi

**Thời gian:** File 49 phút → ~3 phút xử lý

### 2. audio_to_text.py - Tạo Script

**Chế độ 1: Convert tất cả (Khuyến nghị)**
```bash
python3 audio_to_text.py output/mondai --batch

# Chính xác hơn (chậm hơn)
python3 audio_to_text.py output/mondai --batch --model small
```

**Chế độ 2: Convert 1 file**
```bash
python3 audio_to_text.py <file.mp3>

# Ví dụ
python3 audio_to_text.py output/mondai/mondai_1/mondai_1.mp3
python3 audio_to_text.py output/mondai/mondai_1/questions/question_1.mp3
```

**Output:**
- File `.txt` tạo cùng chỗ với file `.mp3`
- Tên giống nhau, chỉ khác đuôi

**Thời gian:** 34 files → ~5-7 phút (model base)

### Whisper Models

| Model | Tốc độ | Độ chính xác | Dung lượng |
|-------|--------|--------------|------------|
| tiny | ⚡⚡⚡ | ⭐⭐ | 72MB |
| base | ⚡⚡ | ⭐⭐⭐ | 139MB ✅ Khuyến nghị |
| small | ⚡ | ⭐⭐⭐⭐ | 461MB |
| medium | 🐌 | ⭐⭐⭐⭐⭐ | 1.5GB |
| large | 🐌🐌 | ⭐⭐⭐⭐⭐ | 2.9GB |

---

## 💡 Use Cases

### Case 1: Chỉ cần tách audio
```bash
python3 audio_splitter.py input/jlpt_n2.mp3
# Xong! Có 34 file MP3 riêng biệt
```

### Case 2: Cần cả audio + script
```bash
python3 audio_splitter.py input/jlpt_n2.mp3
python3 audio_to_text.py output/mondai --batch
# Xong! Có 34 MP3 + 34 TXT
```

### Case 3: Tạo lại script (không tách audio lại)
```bash
# Đã có audio rồi, chỉ tạo lại script
python3 audio_to_text.py output/mondai --batch --model small
```

### Case 4: Script cho 1 mondai cụ thể
```bash
python3 audio_to_text.py output/mondai/mondai_1/mondai_1.mp3
```

---

## 📊 Ví dụ thực tế

**Input:** `jlpt_n2.mp3` (45MB, 49 phút)

**Sau Bước 2 (Tách audio - ~3 phút):**
- 5 mondai folders
- 29 questions
- 34 MP3 files (118MB)

**Sau Bước 3 (Tạo script - ~5 phút):**
- 34 TXT files
- Script tiếng Nhật cho mỗi file

**Chi tiết:**
```
Mondai 1: 5 câu hỏi, 9.6 phút
Mondai 2: 6 câu hỏi, 13.9 phút
Mondai 3: 5 câu hỏi, 10.4 phút
Mondai 4: 11 câu hỏi, 7.1 phút
Mondai 5: 2 câu hỏi, 6.2 phút
```

---

## 🛠️ Troubleshooting

**❌ GOOGLE_API_KEY not found**
```bash
# Tạo file .env
echo "GOOGLE_API_KEY=your_key" > .env
```

**❌ FFmpeg not found**
```bash
brew install ffmpeg
```

**❌ Script không chính xác**
```bash
# Dùng model lớn hơn
python3 audio_to_text.py output/mondai --batch --model small
```

**❌ File audio không hỗ trợ**
- Hỗ trợ: MP3, WAV, M4A, FLAC, OGG
- Convert bằng FFmpeg nếu cần

---

## 📁 Cấu trúc Files

```
Demo AI/
├── audio_splitter.py      # Tách audio
├── audio_to_text.py       # Tạo script
├── generate_scripts.py    # (Cũ, dùng audio_to_text.py --batch)
├── .env                   # API key
├── input/                  # Input
│   └── jlpt_n2.mp3
└── output/                # Output
    ├── transcript.json
    ├── structure.json
    └── mondai/
        ├── mondai_1/
        │   ├── mondai_1.mp3
        │   ├── mondai_1.txt
        │   └── questions/
        │       ├── question_1.mp3
        │       ├── question_1.txt
        │       └── ...
        └── ...
```

---

## ⚙️ Công nghệ

- **OpenAI Whisper** - Speech to text (Japanese)
- **Google Gemini 2.5 Flash** - AI phân tích cấu trúc (FREE)
- **FFmpeg** - Audio processing
- **Python 3.13** - Runtime

---

## 📝 Notes

- Script được lưu **cùng thư mục** với audio
- Tên script **giống** tên audio (chỉ đổi .mp3 → .txt)
- Có thể chạy lại `audio_to_text.py` mà không cần tách audio lại
- Model `base` đủ tốt cho hầu hết trường hợp
- API Gemini hoàn toàn miễn phí

---

**Version:** 2.1  
**Author:** PBL5 Team  
**Date:** 2026-01-14

## 📜 License

MIT License - Free to use
