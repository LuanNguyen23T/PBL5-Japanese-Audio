# Style-Bert-VITS2 R&D Environment

## Mô tả
Docker container chạy Style-Bert-VITS2 trong môi trường R&D riêng biệt,
hoàn toàn tách khỏi backend chính. Hỗ trợ GPU (NVIDIA) và CPU tự động.

## Yêu cầu

| Thành phần | Bắt buộc | Ghi chú |
|-----------|----------|---------|
| Docker Desktop | ✅ | Windows / Mac / Linux |
| NVIDIA Container Toolkit | ⚠️ Chỉ cần nếu dùng GPU | [Hướng dẫn cài](#gpu-setup) |

## Cấu trúc thư mục

```
StyleBertVITS2/
├── Dockerfile              # Python 3.11 + CUDA + style-bert-vits2
├── docker-compose.yml      # CPU mode (default)
├── docker-compose.gpu.yml  # GPU override (NVIDIA machines)
├── test_tts.py             # R&D test script (5 phases)
├── download_models.py      # Download pre-trained JP models
├── models/                 # TTS model files (volume mounted)
├── output/                 # Audio output files (volume mounted)
└── logs/                   # Test reports (volume mounted)
```

---

## Hướng dẫn sử dụng

### Bước 1: Build Docker Image (Lần đầu, ~10-20 phút)

```bash
cd R&D/StyleBertVITS2

# CPU mode (máy không có NVIDIA GPU)
docker compose build

# Hoặc GPU mode (máy có NVIDIA GPU)
docker compose -f docker-compose.yml -f docker-compose.gpu.yml build
```

### Bước 2: Download Models (Lần đầu, ~10-30 phút tùy internet)

```bash
docker compose run --rm sbvits2 python download_models.py
```

### Bước 3: Chạy R&D Test

```bash
# CPU mode
docker compose run --rm sbvits2 python test_tts.py

# GPU mode
docker compose -f docker-compose.yml -f docker-compose.gpu.yml run --rm sbvits2 python test_tts.py

# Test với text tùy chỉnh
docker compose run --rm sbvits2 python test_tts.py --text "こんにちは、世界！"
```

### Bước 4: Xem kết quả

```bash
# Xem test report
cat logs/test_report.md

# Nghe audio output (trên Windows)
start output/test_output.wav
```

---

## GPU Setup (NVIDIA machines only) {#gpu-setup}

### Windows (máy bạn bè có NVIDIA GPU)

1. Cài [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)
2. Restart Docker Desktop
3. Chạy với GPU mode:
   ```bash
   docker compose -f docker-compose.yml -f docker-compose.gpu.yml run --rm sbvits2 python test_tts.py
   ```

### Mac (Apple Silicon M1/M2/M3)

Docker trên Mac **không hỗ trợ GPU passthrough**. Chạy CPU mode trong Docker.  
Nếu muốn dùng Metal MPS → chạy natively (không qua Docker):
```bash
pip install style-bert-vits2
python test_tts.py
```

---

## Lệnh tiện ích

```bash
# Xem log container
docker compose logs sbvits2

# Vào shell container để debug
docker compose run --rm sbvits2 bash

# Xóa container (giữ lại images)
docker compose down

# Xóa image (build lại từ đầu)
docker compose down --rmi all
```

---

## Troubleshooting

| Lỗi | Nguyên nhân | Giải pháp |
|-----|-------------|-----------|
| `No models found` | Chưa download model | Chạy `download_models.py` |
| `CUDA not available` | Không có NVIDIA GPU | Bình thường, dùng CPU mode |
| `numpy>=2 warning` | numpy version mismatch | Bỏ qua, style-bert-vits2 tự xử lý |
| Container OOM | RAM không đủ | Đóng app khác, cần >=8GB RAM |
| Build thất bại | Internet chậm | Thử lại, pip retry tự động |

---

## Thông tin kỹ thuật

- **Base image:** `pytorch/pytorch:2.3.1-cuda12.1-cudnn8-runtime`
- **Python:** 3.11
- **PyTorch:** 2.3.1
- **CUDA:** 12.1 (nếu có GPU)
- **style-bert-vits2:** Latest pip release
