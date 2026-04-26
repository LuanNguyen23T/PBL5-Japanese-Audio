# PBL5 — Japanese Audio Learning Platform

A full-stack web application for Japanese listening practice, powered by AI. Upload JLPT audio files and the system automatically transcribes, analyzes, and generates structured exam questions using ReazonSpeech and Gemini AI.

---

## Features

- **AI-Powered Audio Processing** — Automatic transcription (ReazonSpeech k2) + script refinement & timestamp extraction (Gemini 2.5 Flash)
- **JLPT Exam Management** — Create, manage, and take listening exams with structured Mondai/Question format
- **User Management** — JWT authentication, Google OAuth, role-based access
- **Result Tracking** — Store and review exam results per user
- **Internationalization** — Frontend supports multiple languages (i18n)
- **File Storage** — Audio/image uploads via Cloudinary

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 19, TypeScript, Vite, Tailwind CSS v4, shadcn/ui |
| Backend | FastAPI, SQLAlchemy 2.0 (async), Alembic, Pydantic v2 |
| Database | PostgreSQL 17 |
| AI / ASR | Gemini 2.5 Flash (`google-genai`), ReazonSpeech k2 |
| Audio | PyDub |
| Auth | JWT, Google OAuth2 |
| Storage | Cloudinary |
| Container | Docker, Docker Compose |

---

## Project Structure

```
.
├── backend/          # FastAPI application
│   ├── app/
│   │   ├── modules/  # auth, users, exam, questions, audio, ai_exam, result
│   │   ├── core/     # config, security, health
│   │   ├── db/       # models, session, migrations
│   │   └── shared/   # email, upload, utils, webhook
│   └── alembic/      # DB migration scripts
├── frontend/         # React + Vite SPA
│   └── src/
│       ├── features/ # Feature modules
│       ├── pages/    # Route pages
│       └── components/
├── R&D/Demo AI/      # AI pipeline scripts (standalone)
├── deployments/      # AWS & GCP config
├── docs/             # Project documentation
└── docker-compose.yml
```

---

## Prerequisites

- Python 3.12+
- Node.js 20+ / pnpm
- PostgreSQL 17 (or use Docker)
- `ffmpeg` (required by PyDub)
- Google API Key (Gemini)

---

## Getting Started

### 1. Clone & setup environment

```bash
git clone https://github.com/bnhan2710/PBL5-Japanese-Audio.git
cd PBL5-Japanese-Audio

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

### 2. Start Database

```bash
docker compose up -d postgres
```

### 3. Backend

```bash
cd backend
cp .env.example .env   # fill in your values
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start dev server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend API available at: `http://localhost:8000`  
Swagger docs: `http://localhost:8000/docs`

### 4. Frontend

```bash
cd frontend
pnpm install
pnpm dev
```

Frontend available at: `http://localhost:5173`

---

## Environment Variables

Create `backend/.env` with the following:

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/fastapi_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=fastapi_db
DB_HOST=localhost
DB_PORT=5433

# JWT
JWT_SECRET_KEY=your-secret-key

# Google AI
GOOGLE_API_KEY=your-gemini-api-key

# Google OAuth (optional)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=

# Cloudinary (optional)
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=

# Email (optional)
SMTP_EMAIL=
SMTP_PASSWORD=

# n8n Webhook (optional)
N8N_WEBHOOK_URL=
```

---

## AI Audio Pipeline (R&D)

Standalone script to process a JLPT audio file end-to-end:

```bash
cd "R&D/Demo AI"

# Install dependencies
pip install python-dotenv pydub google-genai reazonspeech-k2-asr

# Create .env with GOOGLE_API_KEY
echo "GOOGLE_API_KEY=your-key" > .env

# Run pipeline
python3 audio_splitter_to_text_v2.py input/J2.mp3 --output_dir output_v2
```

**Pipeline steps:**
1. **ReazonSpeech** — Transcribes Japanese audio → `raw_transcript.txt`
2. **Gemini** — Refines transcript into structured script → `refined_script.txt`
3. **Gemini** — Extracts Mondai/Question timestamps → `timestamps.json`
4. **PyDub** — Cuts audio into individual question files → `mondai/mondai_N/questions/`

---

## Running Tests

```bash
cd backend
pytest
```

---

## Deployment

See [`deployments/`](deployments/README.md) for AWS (CodeBuild + ECS) and Google Cloud (Cloud Build + Cloud Run) configurations.

---

## Documentation

Full documentation available via MkDocs:

```bash
pip install mkdocs
mkdocs serve
```

Or browse the [`docs/`](docs/) folder directly.

---

### 5. Japanese Voice Cloning Service (Style-Bert-VITS2)

> Requires **Docker Desktop** to be running. Recommended: 8 GB+ RAM.

```bash
cd R&D/StyleBertVITS2

# Step 1: Build the Docker image (10–20 min, first time only)
docker compose build

# Step 2: Download Japanese voice models — ~2 GB total
docker compose run --rm sbvits2 python download_models.py

# Step 3: Run the multi-speaker synthesis test
docker compose run --rm sbvits2 python test_multi_speaker.py

# Step 4: Start the TTS API server (port 7861)
docker compose up -d

# Verify the service is healthy
curl http://localhost:7861/health
```

TTS API available at: `http://localhost:7861`

To test multi-speaker synthesis inside the container:

```bash
docker exec -it style-bert-vits2 python test_multi_speaker.py
# Output saved to: R&D/StyleBertVITS2/output/multi_speaker_test.wav
```

**Available voice models:**

| Key | Description |
|---|---|
| `jvnv-F1-jp` | Female, Standard / Teacher |
| `jvnv-F2-jp` | Female, Mature / Calm |
| `jvnv-M1-jp` | Male, Young Adult |
| `jvnv-M2-jp` | Male, Deep / Elderly |
| `jp-extra-cool-young` | Male, Young boy (Rikka) |
| `jp-extra-amazing` | Female, Energetic / Cute |
| `myvoiceclone-male` | Male, Middle-aged clone |

---

## Japanese Voice Cloning

A built-in admin feature for generating JLPT listening audio from a dialogue script using AI voice synthesis.

- **Multi-speaker synthesis** — Each character is assigned a different Japanese voice model
- **Voice cloning** — Upload a reference audio sample to clone intonation style
- **Emotion styles** — `Neutral`, `Happy`, `Sad`, `Angry` (model-dependent)
- **Drag and drop** — Reference audio can be dragged directly into the config panel
- **Auto memory cleanup** — The TTS container restarts automatically after each generation

**Usage (Web UI):**

1. Log in as Admin, navigate to **Generate Japanese Voice**
2. Type a dialogue script using the format `SpeakerLabel: dialogue text`
3. Configure voice model, emotion style, and pitch per speaker
4. Optionally upload a reference `.wav` file (drag and drop supported)
5. Click **Generate** — audio is synthesized, uploaded to Cloudinary, and saved automatically

---
