# ============================================================
# Style-Bert-VITS2 - R&D Docker Image
# Base: Python 3.11
# Supports: NVIDIA GPU / CPU fallback
# ============================================================
FROM python:3.11-slim-bookworm

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    wget \
    libsndfile1 \
    libsndfile1-dev \
    ffmpeg \
    mecab \
    libmecab-dev \
    mecab-ipadic-utf8 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip

# Install PyTorch with CUDA 12.4 support (Fallback to CPU if no GPU)
RUN pip install --no-cache-dir torch==2.4.1 torchvision==0.19.1 torchaudio==2.4.1 --index-url https://download.pytorch.org/whl/cu124

# Install style-bert-vits2 dependencies
RUN pip install --no-cache-dir \
    "numpy<2" \
    "librosa==0.9.2" \
    "protobuf>=3.20,<5" \
    "transformers>=4.37,<5" \
    "style-bert-vits2" \
    "soundfile" \
    "pydub" \
    "soxr" \
    "sentencepiece" \
    "fastapi" \
    "uvicorn" \
    "python-multipart" \
    "httpx" \
    "unidic-lite"

# Install pyannote.audio separately to prevent pip dependency resolution deep loops
RUN pip install --no-cache-dir "pyannote.audio" "torch==2.4.1" "torchaudio==2.4.1"

# Verify critical imports work after install
RUN python -c "import torch; print('torch:', torch.__version__)" && \
    python -c "import transformers; print('transformers:', transformers.__version__)" && \
    python -c "from style_bert_vits2.tts_model import TTSModelHolder; print('style-bert-vits2: OK')"

# Create directories
RUN mkdir -p /app/models /app/output /app/logs

# Copy scripts
COPY . .

# Port for Gradio UI (optional)
EXPOSE 7860

# Default: run R&D test
CMD ["python", "test_tts.py"]
