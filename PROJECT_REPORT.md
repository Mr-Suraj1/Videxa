# Videxa Project Report

## Current architecture

Videxa is a local video intelligence app with a Next.js App Router frontend and
a FastAPI backend. The frontend handles YouTube links, local media uploads,
analysis results, transcript viewing, exports, session selection, and grounded
Q&A. The backend delegates to the shared Python processing pipeline.

### Completed product phases

- Media download/upload, conversion, chunking, and transcription.
- Summaries, action items, decisions, and open question extraction.
- Persistent, isolated Chroma collections for processed videos.
- Single-video and cross-video grounded Q&A.
- Persistent session catalog and session listing API.
- TXT, Markdown, and PDF export endpoints.
- Next.js frontend replacing the former Python UI.

### Remaining roadmap

- Speaker diarization (provider/model and runtime choice needed).
- Cloud deployment (hosting target and configuration needed).
- Team collaboration (identity, access control, and shared storage design needed).
- Background jobs for long-running media processing.

## Structure

- `frontend/`: Next.js App Router UI.
- `backend/app.py`: FastAPI API routes, CORS configuration, and upload handling.
- `backend/schemas.py`: validated request and response models.
- `backend/services.py`: adapters for pipeline and RAG services.
- `core/pipeline.py`: shared analysis orchestration.
- `core/transcriber.py`, `core/summarizer.py`, `core/extractor.py`: AI pipeline stages.
- `core/vector_store.py`, `core/rag_engine.py`: transcript indexing and Q&A.
- `core/session_catalog.py`: SQLite catalog for session IDs, titles, and dates.
- `core/exporters/`: in-memory transcript, analysis, and PDF exports.
- `utils/audio_processor.py`: YouTube download and media preparation.

## Current API

- `GET /health`, `GET /sessions`
- `POST /process` for a YouTube URL
- `POST /process/upload` for a local media upload
- `POST /chat` and `POST /chat/multi`
- `POST /exports/transcript`, `/exports/analysis`, `/exports/pdf`

## Operational notes

- FFmpeg must be installed and available on `PATH` for media conversion and
  YouTube audio extraction.
- The backend defaults to allowing `http://localhost:3000` and
  `http://127.0.0.1:3000`; configure other origins with `VIDEXA_CORS_ORIGINS`.
- The frontend API base defaults to `http://127.0.0.1:8000` and can be changed
  with `NEXT_PUBLIC_API_BASE_URL`.
- The session catalog is stored in `vector_db/sessions.sqlite3`; Chroma indexes
  are stored under `vector_db/`.
- Authentication is not implemented, so the API is intended for trusted local
  use until access control is added.
