# Videxa Project Report

## 1. Project Overview

Videxa is a Python-based AI video assistant that accepts either a YouTube URL or a local media file, extracts the audio, transcribes it, generates a summary, extracts structured meeting insights, and supports Q&A over the generated transcript using a retrieval-augmented generation (RAG) flow. The core flow is assembled in `app.py` and the pipeline functions are split across `utils/audio_processor.py`, `core/transcriber.py`, `core/summarizer.py`, `core/extractor.py`, and `core/rag_engine.py`.

The project targets users who need to review meetings, lectures, podcasts, and other recorded audio/video content quickly without manually reading a long transcript. Based on the code, the intended users are knowledge workers, students, and anyone who needs an AI assistant to summarize and query media content. Evidence: `app.py`; `utils/audio_processor.py`; `core/transcriber.py`; `core/summarizer.py`; `core/rag_engine.py`.

## 2. Tech Stack

- Languages: Python is the primary language. The project contains Python files and a Python dependency manifest (`Requirements.txt`). Evidence: `Requirements.txt`; `app.py`; `main.py`; `core/*.py`.
- Frontend/UI: Streamlit is the UI framework. Evidence: `app.py` imports `streamlit as st`, calls `st.set_page_config`, and builds the dashboard layout; `Requirements.txt` includes `streamlit>=1.35.0`.
- Audio/video acquisition: `yt-dlp` is used to download YouTube audio, and `pydub` plus `ffmpeg-python` are used for audio conversion and chunking. Evidence: `utils/audio_processor.py`; `Requirements.txt`.
- Speech-to-text: `openai-whisper` is used for local transcription and `requests` calls are used against the Sarvam STT API (`https://api.sarvam.ai/speech-to-text-translate`). Evidence: `utils/audio_processor.py`; `Requirements.txt`.
- LLM orchestration: `langchain`, `langchain-core`, `langchain-community`, and `langchain-mistralai` are used; the model is `mistral-small-latest`. Evidence: `core/summarizer.py`; `core/extractor.py`; `core/rag_engine.py`; `Requirements.txt`.
- Embeddings and vector DB: `langchain-chroma`, `langchain-huggingface`, `sentence-transformers`, and `chromadb` are used with the embedding model `all-MiniLM-L6-v2`. Evidence: `core/vector_store.py`; `Requirements.txt`.
- Environment config: `python-dotenv` is used via `load_dotenv()`. Evidence: `app.py`; `main.py`; `test.py`; `Requirements.txt`.
- Exporting/documentation utilities: `reportlab` and `fpdf2` are in `Requirements.txt`, but no direct usage was found in the code inspected. Evidence: `Requirements.txt`.
- Database: there is no relational database (MySQL/Postgres/SQLite schema) in the code; the project uses a persistent Chroma vector store under `vector_db/`. Evidence: `core/vector_store.py` and `vector_db/`.
- External APIs: besides the Sarvam STT endpoint and Mistral LLM access, no project-owned backend API or REST routes were found. Evidence: `core/transcriber.py`; `core/rag_engine.py`; `app.py`.

## 3. Folder Structure

- `app.py`: Streamlit application entry point and UI. It sets page configuration, renders the sidebar and results cards, manages session state, and triggers the pipeline. Evidence: `app.py`.
- `main.py`: a CLI-style pipeline script that runs the same audio-to-transcript-to-summary flow from a hardcoded YouTube URL. Evidence: `main.py`.
- `test.py`: a one-off script that loads environment variables, runs the transcription/summarization pipeline on a hardcoded YouTube URL, and prints the transcript and extracted items. Evidence: `test.py`.
- `core/`: application backend logic. Evidence: `core/` directory.
  - `core/transcriber.py`: transcription orchestration and chunked speech-to-text logic.
  - `core/summarizer.py`: meeting summary generation and title creation with LangChain + Mistral.
  - `core/extractor.py`: extraction of action items, decisions, and unresolved questions.
  - `core/vector_store.py`: Chroma vector DB building and retrieval helpers.
  - `core/rag_engine.py`: RAG pipeline construction and Q&A function.
- `utils/`: helper utilities. Evidence: `utils/audio_processor.py`.
  - `utils/audio_processor.py`: source detection, YouTube download, local conversion, and chunking logic.
- `downloades/`: runtime output folder for downloaded and converted audio files. Created by `download_youtube_audio()` and used by conversion/chunking logic. Evidence: `utils/audio_processor.py`.
- `vector_db/`: persistent directory for the Chroma vector database and collection data. Evidence: `core/vector_store.py` and `vector_db/`.
- `Requirements.txt`: dependency file for the project. Evidence: `Requirements.txt`.
- `.env`: environment variables file for API keys and model settings. Evidence: `.env`.
- `.gitignore`: excludes `.env`, `downloades/`, and Python caches. Evidence: `.gitignore`.
- `README.md`: project overview and user-facing instructions. Evidence: `README.md`.

## 4. Architecture

The project is a single-process Python + Streamlit app, not a traditional multi-service architecture. The flow is:

1. User enters a YouTube URL or local file path into the Streamlit sidebar (`app.py`).
2. `process_input(source)` in `utils/audio_processor.py` detects if the source is a URL or a local file. For URLs, it calls `download_youtube_audio()`. For local files, it calls `convert_to_wav()` and then `chunk_audio()`.
3. `transcribe_all(chunks, language)` in `core/transcriber.py` transcribes each audio chunk. For `english`, it uses Whisper; for `hinglish`, it switches to the Sarvam API route via `transcribe_chunk_sarvam()`.
4. `generate_title(transcript)` and `summarize(transcript)` in `core/summarizer.py` create the title and summary using Mistral through LangChain prompt chains.
5. `extract_action_items()`, `extract_key_decisions()`, and `extract_questions()` in `core/extractor.py` run additional LLM-based structured extraction.
6. `build_vector_store(transcript)` in `core/vector_store.py` splits the transcript into chunks, creates embeddings with `HuggingFaceEmbeddings`, and stores them in Chroma.
7. `build_rag_chain(transcript)` in `core/rag_engine.py` creates a retriever and wraps it into a prompt + LLM chain for Q&A.
8. `ask_question(rag_chain, question)` returns answers grounded by transcript context. Evidence: `app.py`; `utils/audio_processor.py`; `core/transcriber.py`; `core/summarizer.py`; `core/extractor.py`; `core/vector_store.py`; `core/rag_engine.py`.

The frontend and backend are tightly coupled in one app rather than separated by an API layer. There is no Node/React frontend, no REST API server, and no separate database service. Evidence: `app.py` and the absence of a backend framework such as FastAPI/Flask/Django in the repository root and Python files.

## 5. Core Features

- Audio/video ingestion and conversion: `utils/audio_processor.py` (`download_youtube_audio`, `convert_to_wav`, `chunk_audio`, `process_input`).
- Local/remote transcription: `core/transcriber.py` (`transcribe_chunk_whisper`, `transcribe_chunk_sarvam`, `transcribe_chunk`, `transcribe_all`).
- Summary generation: `core/summarizer.py` (`summarize`, `generate_title`).
- Action item / decision / follow-up extraction: `core/extractor.py` (`extract_action_items`, `extract_key_decisions`, `extract_questions`).
- Chroma vector store creation and retrieval: `core/vector_store.py` (`build_vector_store`, `load_vector_store`, `get_retriever`).
- RAG Q&A: `core/rag_engine.py` (`build_rag_chain`, `load_rag_chain`, `ask_question`).
- Streamlit UI workflow: `app.py` (`st.sidebar`, result cards, progress indicators, chat UI, rerun logic).
- CLI demo pipeline: `main.py` (`run_pipeline`) and `test.py` (hardcoded execution). Evidence: each file and function name above.

## 6. Database Design

There is no SQL schema or formal ORM model in the project.

- The persistent data store is Chroma vector DB, configured in `core/vector_store.py`:
  - `CHROMA_DIR = "vector_db"`
  - `COLLECTION_NAME = "meeting_transcript"`
  - `EMBEDDING_MODEL = "all-MiniLM-L6-v2"`
  - Documents are created using `Document(page_content=chunk, metadata={'chunk_index': i})` and saved with `Chroma.from_documents(...)`.
- There are no tables like `users`, `sessions`, `transcripts`, `summaries`, or `chat_history` in a SQL database. The code instead stores transcript chunks as vector embeddings, not rows in a relational schema.
- The Chroma metadata structure is minimal: only `chunk_index` metadata per document chunk. There are no relationships, join tables, or foreign keys to model. Evidence: `core/vector_store.py` and the `vector_db/` directory.
- The only database-like file found is the local SQLite database in `vector_db/chroma.sqlite3`; it is part of Chroma's persistence layer rather than a custom app schema. Evidence: `vector_db/`.
- Related note: there is no migration system or schema tooling found. `not found` for Alembic, SQLAlchemy models, Prisma schema, Django models, or other DB configuration files.

## 7. API Endpoints

There are no local REST API routes or backend endpoints defined in the codebase.

- `app.py` is a Streamlit UI, not a Flask/FastAPI server. It wires UI actions directly to Python functions instead of HTTP endpoints.
- No `routes/`, `api/`, `controllers/`, or framework router files were found in the project tree. `not found` for `FastAPI`, `Flask`, `Express`, or similar route declarations.
- The only external HTTP interaction in the code is the Sarvam speech-to-text API call in `core/transcriber.py`:
  - `SARVAM_STT_TRANSLATE_URL = "https://api.sarvam.ai/speech-to-text-translate"`
  - The project posts audio to that URL with `requests.post(...)`.
- Mistral LLM access is via the LangChain `ChatMistralAI` client; no custom API endpoint layer is implemented around it. Evidence: `core/transcriber.py`; `core/summarizer.py`; `core/rag_engine.py`; `app.py`.

## 8. Authentication and Security

- Authentication: `not found`. There is no login page, no user model, no session/auth middleware, no JWT or OAuth flow, and no password hashing. Evidence: `app.py` and all Python files inspected.
- Authorization: `not found`. The app is effectively a single-user local tool, not a multi-user system.
- Secret handling: secrets are loaded using `load_dotenv()` from `.env` and passed directly to API clients. Evidence: `app.py` calls `load_dotenv()`, `main.py` calls `load_dotenv()`, `core/summarizer.py` uses `os.getenv("MISTRAL_API_KEY")`, and `core/transcriber.py` uses `os.getenv("SARVAM_API_KEY")`.
- Environment variables used by the code: `MISTRAL_API_KEY`, `WHISPER_MODEL`, `SARVAM_API_KEY`, `SARVAM_STT_MODEL`. Evidence: `.env`; `core/transcriber.py`; `core/summarizer.py`.
- Input validation: minimal to none. There is no URL validation, no file existence checks before calling the downloader/converter, and no file-type validation beyond the file extension checks inside `download_youtube_audio()`. Evidence: `utils/audio_processor.py`.
- Security concern: the repository contains a real `.env` file in the root with API keys. While `.gitignore` excludes `.env`, the file is physically present in the workspace and could be accidentally committed or leaked if the git state is not properly managed. Evidence: `.env`; `.gitignore`.
- Security concern: the code directly trusts and executes the user-supplied source string in `process_input()`, which may be a URL to a remote video or a local path. There is no sandboxing or allowed-host policy. Evidence: `utils/audio_processor.py`.
- Security concern: `app.py` renders transcript and AI output into HTML with `unsafe_allow_html=True` several times. That is a potential XSS vector if untrusted transcript content is injected into the page. Evidence: `app.py` uses `st.markdown(..., unsafe_allow_html=True)` for transcript and chat bubbles.

## 9. Setup and Run Instructions

Setup is straightforward but depends on the environment notes in `Requirements.txt`:

- Install Python and create a virtual environment. Evidence: `README.md`; `Requirements.txt`.
- Install project dependencies:
  - `pip install -r Requirements.txt`
  - The README says `pip install -r Requirements.txt`, but the actual repo file is `Requirements.txt` with an uppercase `R`. Evidence: `README.md`; `Requirements.txt`.
- Create a `.env` file in the project root with the following variable names (actual values are not shown in this report):
  - `MISTRAL_API_KEY`
  - `SARVAM_API_KEY`
  - `WHISPER_MODEL` (optional; default is `small`)
  - `SARVAM_STT_MODEL` (optional; default is `saaras:v2.5`)
  Evidence: `.env`; `core/transcriber.py`; `core/summarizer.py`; `app.py`.
- Run the app:
  - `streamlit run app.py`
  - or `python -m streamlit run app.py`
  Evidence: `README.md`; `app.py`.
- Special note from the code comments: the project recommends using the base Anaconda environment rather than a `.venv` because of a Windows torch DLL issue. Evidence: `Requirements.txt`.
- CLI fallback: `python main.py` executes the pipeline and asks for a URL and language at runtime. Evidence: `main.py`.
- Demo script: `python test.py` executes a hardcoded YouTube URL. Evidence: `test.py`.
- `Dockerfile`, `docker-compose.yml`, and other deployment configs: `not found`.

## 10. Code Quality Review

What is good:

- The codebase is modular and separated by concern: ingestion (`utils/audio_processor.py`), transcription (`core/transcriber.py`), summarization (`core/summarizer.py`), extraction (`core/extractor.py`), vector DB (`core/vector_store.py`), and UI (`app.py`).
- The app has a clear, polished Streamlit experience with progress indicators and a visible status bar. Evidence: `app.py`.
- The pipeline is easy to reason about and reproducible for local use. Evidence: `main.py` and `test.py`.
- Environment configuration is centralized through `.env` and `load_dotenv()`, which is cleaner than hardcoding secrets. Evidence: `app.py`; `.env`.

Bugs and issues:

- `load_rag_chain()` in `core/rag_engine.py` calls `get_retriever()` without passing a vector store. The function signature requires `vector_store` (`def get_retriever(vector_store: Chroma, k: int = 4):`), so this is a bug and likely a runtime TypeError.
- The app reuses a single Chroma collection name (`meeting_transcript`) without scoping by session or document, which can cause stale data and cross-session collisions. Evidence: `core/vector_store.py`.
- The pipeline assumes the provided source is valid and accessible; missing or malformed URLs or file paths are not validated. Evidence: `utils/audio_processor.py`.
- `download_youtube_audio()` uses a filename transformation to replace `.webm` and `.m4a` with `.wav`, but it does not robustly handle every YouTube format or clean up intermediate files. Evidence: `utils/audio_processor.py`.
- There are duplicate `get_llm()` implementations in `core/summarizer.py`, `core/extractor.py`, and `core/rag_engine.py`; each contains the same model and key access pattern. This is not an immediate bug, but it is duplicated logic. Evidence: each file.
- There are no automated tests on the project beyond ad hoc scripts. `not found` for `pytest`, `unittest`, or a proper test suite. Evidence: repository tree and `glob` for `**/*test*` plus `test.py`.
- There is no error handling for missing FFmpeg or unsupported local formats before `AudioSegment.from_file(...)` is called. Evidence: `utils/audio_processor.py`.
- There is no account layer, caching layer, or job queue for long-running media processing; the app is synchronous and can block the UI. Evidence: `app.py` and `utils/audio_processor.py`.
- There is no request logging, user auditing, or structured error reporting. Evidence: project files inspected.

Security concerns:

- Secret leakage risk via `.env` file in workspace. Evidence: `.env`.
- Direct HTML injection risk using `unsafe_allow_html=True` with untrusted transcript and chat content. Evidence: `app.py`.
- No rate limiting or abuse prevention for external API calls; a user can repeatedly trigger expensive transcription/LLM jobs. Evidence: `app.py`; `core/transcriber.py`; `core/rag_engine.py`.

## 11. Incomplete / TODO Parts

- `load_rag_chain()` appears incomplete or broken because it calls `get_retriever()` without a `vector_store` argument. Evidence: `core/rag_engine.py`.
- `main.py` and `test.py` are demo scripts with hardcoded source values, not a production CLI or service layer. Evidence: `main.py`; `test.py`.
- The project has no user data model or persistent app database beyond Chroma. Evidence: `core/vector_store.py` and the absence of SQL/ORM files.
- There is no explicit backlog or TODO markers in the code. Search for `TODO`, `FIXME`, and similar comments returned `not found`. Evidence: grep across Python files.
- Export features mentioned in the README (like PDF export) are not implemented in the inspected code. `reportlab` and `fpdf2` are in `Requirements.txt`, but no export function or UI action was found in `app.py` or the codebase. Evidence: `Requirements.txt`; `app.py`; no PDF export functions found in Python files.
- There is no end-to-end test or deployment automation. Evidence: repository root files and no CI config found.

## 12. Improvement Suggestions

Prioritized suggestions based on the code and risk:

1. Priority 1: Fix runtime bugs and validation.
   - Fix `load_rag_chain()` and add URL/file validation before running the analysis pipeline. Evidence: `core/rag_engine.py`; `utils/audio_processor.py`.
2. Priority 1: Remove or protect secret leakage.
   - Move secrets to a secure secret manager or environment injection system; do not rely on a workspace `.env` file for production use. Evidence: `.env`; `core/transcriber.py`; `core/summarizer.py`.
3. Priority 1: Sanitize HTML rendering.
   - Replace `unsafe_allow_html=True` with safer rendering or sanitize transcript/chat text before display. Evidence: `app.py`.
4. Priority 2: Add a real backend and persistence model.
   - Introduce a proper API layer and persistent user/session schema if the product is expected to scale beyond a single-user local tool. Evidence: no route layer found; `app.py` is a monolithic UI.
5. Priority 2: Add tests and CI.
   - Add unit tests for transcription, summarization, chunking, and RAG retrieval; add CI checks. Evidence: no test suite found.
6. Priority 2: Reduce duplicate LLM wiring.
   - Centralize the model configuration and use a single provider/client helper. Evidence: repeated `get_llm()` definitions across `core/summarizer.py`, `core/extractor.py`, and `core/rag_engine.py`.
7. Priority 3: Improve performance and reliability.
   - Add background job processing, cleanup for downloaded audio, retries for failed API calls, and a queue for long-running transcriptions. Evidence: `utils/audio_processor.py`; `app.py`.
8. Priority 3: Handle stale vector data and collection scoping.
   - Use a per-session or per-video collection ID instead of one global `meeting_transcript` collection. Evidence: `core/vector_store.py`.

## README vs Actual Code Mismatches

- README claim: `.env` should contain `OPENAI_API_KEY`.
  - Actual code: `MISTRAL_API_KEY`, `SARVAM_API_KEY`, `WHISPER_MODEL`, and `SARVAM_STT_MODEL` are used. Evidence: `.env`; `core/transcriber.py`; `core/summarizer.py`.
- README claim: the project is a generic “AI Video Assistant with RAG.”
  - Actual code: that description is broadly correct, but the app is more specifically a meeting/transcript assistant for YouTube or local media extraction and Q&A. Evidence: `app.py`; `core/rag_engine.py`.
- README claim: `requirements.txt` is used in lowercase.
  - Actual repo file: `Requirements.txt` (capital R) is the dependency manifest. Evidence: `Requirements.txt`; `README.md`.
- README claim: “This project is licensed under the MIT License.”
  - Actual code: no `LICENSE` file or explicit SPDX license declaration was found in the repository. Evidence: root directory listing and absence of `LICENSE` file.
- README claim: the project includes “PDF export” or similar future features.
  - Actual code: `reportlab` and `fpdf2` are installed, but there is no export implementation or UI in the inspected code. Evidence: `Requirements.txt`; `app.py`.
- README claim: there is a complete “future improvements” roadmap.
  - Actual code: these are not implemented yet and no explicit project task management was found beyond the demo scripts. Evidence: `README.md`; `app.py`; no roadmap/task files.

## Bottom line

Videxa is a functional Python prototype for AI-assisted transcript summarization and Q&A over video/audio content. The main value is the end-to-end pipeline from YouTube or local media ingestion to transcript, summary, extraction, and vector search. The code is focused, modular, and visually polished, but it is not yet a secure production-grade application: it lacks authentication, has minimal validation, contains a RAG runtime bug, and stores secrets in a local `.env` file. Evidence: `app.py`; `utils/audio_processor.py`; `core/*.py`.
