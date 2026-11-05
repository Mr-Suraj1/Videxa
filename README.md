# Videxa

Videxa turns long-form video and audio into searchable transcripts, concise
briefs, action items, and grounded answers. The application uses a Next.js web
frontend with a FastAPI backend.

## Features

- Analyze YouTube videos or upload local audio/video.
- Transcribe English or Hinglish recordings.
- Generate a summary, title, action items, decisions, and open questions.
- Ask questions against one video or compare up to 20 videos.
- Export transcripts and analysis as TXT, Markdown, or PDF.
- Browse previously processed sessions from the local session catalog.

## Stack

- Frontend: Next.js App Router, React, TypeScript
- Backend: FastAPI, Python
- Transcription and analysis: Whisper, Sarvam (Hinglish), Gemini
- Retrieval: LangChain, Sentence Transformers, ChromaDB

## Run locally

### Backend

Install Python dependencies and configure `.env` (copy from `.env.example`):

```env
GOOGLE_API_KEY=your_google_api_key_here
GEMINI_MODEL=gemini-3.7-flash
SARVAM_API_KEY=your_sarvam_api_key_here
```

`GOOGLE_API_KEY` is required. `gemini-3.7-flash` has a free tier; verify current
rate limits in Google AI Studio before relying on them. Production workloads
require a paid Google Cloud project with billing enabled and quota configured
accordingly.

Install FFmpeg and make sure `ffmpeg` is available on `PATH`. It is required
to download, convert, and chunk media.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r Requirements.txt
uvicorn backend.app:app --reload
```

The API runs at `http://127.0.0.1:8000`; interactive API documentation is at
`http://127.0.0.1:8000/docs`.

### Next.js frontend

In another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`. To use a different backend address, set
`NEXT_PUBLIC_API_BASE_URL` in `frontend/.env.local`:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

The backend allows the local Next.js development origins by default. Configure
`VIDEXA_CORS_ORIGINS` as a comma-separated list when using another origin.

## API endpoints

- `GET /health`, `GET /sessions`
- `POST /process` for a YouTube URL
- `POST /process/upload` for a local media upload
- `POST /chat` and `POST /chat/multi`
- `POST /exports/transcript`, `/exports/analysis`, `/exports/pdf`

Session titles and IDs are stored in `vector_db/sessions.sqlite3`. Transcript
vectors are kept in Chroma collections under `vector_db/`.

## Project layout

```text
frontend/       Next.js application
backend/        FastAPI routes and request/response schemas
core/           Processing, RAG, session catalog, and export services
utils/          Media download, conversion, and chunking
tests/          Backend test suite
```
