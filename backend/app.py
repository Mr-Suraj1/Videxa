"""FastAPI application boundary for the Videxa core."""

from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware

from backend import services
from backend.schemas import (
    AnalysisResponse,
    ChatRequest,
    ChatResponse,
    ExportRequest,
    HealthResponse,
    MultiChatRequest,
    MultiChatResponse,
    PatchSessionRequest,
    ProcessingRequest,
    ProcessingResponse,
    SessionListResponse,
    SessionContentResponse,
    SessionStatusResponse,
    TranscriptExportRequest,
)
from core.transcriber import TranscriptionError
from core.pipeline import AnalysisFailure
from core.gemini_retry import GeminiProviderError
from core.session_catalog import list_sessions
from core.vector_store import VectorStoreUnavailableError
from utils.audio_processor import InputValidationError, MediaProcessingError, SUPPORTED_MEDIA_EXTENSIONS

logger = logging.getLogger(__name__)
load_dotenv()

app = FastAPI(
    title="Videxa API",
    version="1.0.0",
    description="Backend API for Videxa transcription, analysis, RAG, and exports.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.getenv("VIDEXA_CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
        if origin.strip()
    ],
    allow_methods=["GET", "POST", "DELETE", "PATCH"],
    allow_headers=["Content-Type"],
)


@app.exception_handler(RequestValidationError)
async def request_validation_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    del request
    return JSONResponse(status_code=422, content={"detail": "Invalid request data."})


@app.exception_handler(Exception)
async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
    del request
    logger.exception("Unhandled Videxa API failure", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "The request could not be completed."},
    )


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/sessions", response_model=SessionListResponse)
def sessions() -> SessionListResponse:
    return SessionListResponse(sessions=list_sessions())


@app.get("/sessions/{session_id}", response_model=SessionStatusResponse)
def session_status(session_id: str) -> SessionStatusResponse:
    try:
        result = services.session_status(session_id)
    except ValueError as exc:
        raise _http_error(400, str(exc)) from exc
    if result is None:
        raise _http_error(404, "The requested session was not found.")
    return SessionStatusResponse(**result)


@app.get("/sessions/{session_id}/content", response_model=SessionContentResponse)
def session_content(session_id: str) -> SessionContentResponse:
    try:
        result = services.session_content(session_id)
    except ValueError as exc:
        raise _http_error(400, str(exc)) from exc
    if result is None:
        raise _http_error(404, "Saved transcript content was not found for this session.")
    return SessionContentResponse(**result)


@app.patch("/sessions/{session_id}", status_code=204)
def update_session(session_id: str, request: PatchSessionRequest) -> None:
    try:
        found = services.update_session_title(session_id, request.title)
    except ValueError as exc:
        raise _http_error(400, str(exc)) from exc
    if not found:
        raise _http_error(404, "The requested session was not found.")


@app.delete("/sessions/{session_id}", status_code=204)
def delete_session(session_id: str) -> None:
    try:
        found = services.delete_session(session_id)
    except ValueError as exc:
        raise _http_error(400, str(exc)) from exc
    if not found:
        raise _http_error(404, "The requested session was not found.")


@app.post("/sessions/{session_id}/analysis/retry", response_model=ProcessingResponse)
def retry_session_analysis(session_id: str) -> ProcessingResponse | JSONResponse:
    try:
        result = services.retry_analysis(session_id)
    except KeyError as exc:
        raise _http_error(404, str(exc)) from exc
    except AnalysisFailure as exc:
        return _analysis_failure_response(exc)
    except Exception as exc:
        logger.exception("Videxa analysis retry failed")
        raise _http_error(500, "Analysis retry could not be completed.") from exc
    return _processing_response(result)


@app.post("/process", response_model=ProcessingResponse)
def process(request: ProcessingRequest) -> ProcessingResponse | JSONResponse:
    try:
        result = services.run_pipeline(request.source, request.language)
    except AnalysisFailure as exc:
        return _analysis_failure_response(exc)
    except InputValidationError as exc:
        raise _http_error(400, str(exc)) from exc
    except (MediaProcessingError, TranscriptionError) as exc:
        raise _http_error(502, str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        raise _provider_http_error(exc) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Videxa processing failed")
        raise _http_error(500, "Analysis could not be completed.") from exc

    return _processing_response(result)


@app.post("/process/upload", response_model=ProcessingResponse)
def process_upload(
    file: UploadFile = File(...),
    language: str = Form("english"),
    ) -> ProcessingResponse | JSONResponse:
    """Process a user-uploaded media file and remove its temporary copy."""
    if language not in {"english", "hinglish"}:
        raise _http_error(422, "Choose english or hinglish transcription.")
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in SUPPORTED_MEDIA_EXTENSIONS:
        raise _http_error(400, "This media file type is not supported.")

    try:
        max_size = max(1, int(os.getenv("VIDEXA_MAX_MEDIA_SIZE_MB", "2048"))) * 1024 * 1024
    except ValueError:
        max_size = 2048 * 1024 * 1024

    try:
        with tempfile.TemporaryDirectory(prefix="videxa-upload-") as temp_dir:
            source_path = Path(temp_dir) / f"upload{suffix}"
            size = 0
            with source_path.open("wb") as destination:
                while chunk := file.file.read(1024 * 1024):
                    size += len(chunk)
                    if size > max_size:
                        raise _http_error(413, "The uploaded media exceeds the configured size limit.")
                    destination.write(chunk)
            if size == 0:
                raise _http_error(400, "The uploaded media file is empty.")
            result = services.run_pipeline(str(source_path), language)
    except AnalysisFailure as exc:
        return _analysis_failure_response(exc)
    except InputValidationError as exc:
        raise _http_error(400, str(exc)) from exc
    except (MediaProcessingError, TranscriptionError) as exc:
        raise _http_error(502, str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        raise _provider_http_error(exc) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Uploaded media processing failed")
        raise _http_error(500, "Analysis could not be completed.") from exc
    finally:
        file.file.close()

    return _processing_response(result)


def _processing_response(result: dict) -> ProcessingResponse:
    return ProcessingResponse(
        status="completed",
        session_id=result["session_id"],
        transcript=result["transcript"],
        analysis=AnalysisResponse(
            title=result["title"],
            summary=result["summary"],
            action_items=result["action_items"],
            key_decisions=result["key_decisions"],
            open_questions=result["open_questions"],
        ),
    )


def _analysis_failure_response(exc: AnalysisFailure) -> JSONResponse:
    cause = exc.cause
    category = getattr(cause, "category", None)
    if category == "quota":
        detail = str(cause)
        status_code = getattr(cause, "status_code", None) or 429
        analysis_status = "quota"
    elif category == "rate_limit":
        detail = str(cause)
        status_code = 429
        analysis_status = "rate_limited"
    elif isinstance(cause, httpx.HTTPStatusError):
        status_code = 503 if cause.response.status_code in {401, 403} else 502
        detail = "Gemini rejected the credentials. Check the backend GOOGLE_API_KEY configuration." if status_code == 503 else "Analysis failed due to a provider error. The saved transcript can be analyzed again later."
        analysis_status = "failed"
    else:
        status_code = 502
        detail = "Analysis failed, but the transcript was saved. Retry analysis using this session ID."
        analysis_status = "failed"
    return JSONResponse(status_code=status_code, content={
        "detail": detail,
        "session_id": exc.session_id,
        "processing_status": "completed",
        "analysis_status": analysis_status,
    })


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    try:
        answer = services.answer_question(request.session_id, request.question)
    except ValueError as exc:
        raise _http_error(400, str(exc)) from exc
    except VectorStoreUnavailableError as exc:
        raise _http_error(404, str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        raise _provider_http_error(exc) from exc
    except GeminiProviderError as exc:
        raise _http_error(exc.status_code or 429, str(exc)) from exc
    except Exception as exc:
        logger.exception("Videxa RAG request failed")
        raise _http_error(502, "The transcript question could not be answered.") from exc
    return ChatResponse(session_id=request.session_id, answer=answer)


@app.post("/chat/multi", response_model=MultiChatResponse)
def chat_multiple(request: MultiChatRequest) -> MultiChatResponse:
    try:
        answer = services.answer_question_across_sessions(request.session_ids, request.question)
    except ValueError as exc:
        raise _http_error(400, str(exc)) from exc
    except VectorStoreUnavailableError as exc:
        raise _http_error(404, str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        raise _provider_http_error(exc) from exc
    except GeminiProviderError as exc:
        raise _http_error(exc.status_code or 429, str(exc)) from exc
    except Exception as exc:
        logger.exception("Videxa multi-video RAG request failed")
        raise _http_error(502, "The cross-video question could not be answered.") from exc
    return MultiChatResponse(session_ids=request.session_ids, answer=answer)


@app.post("/exports/transcript")
def export_transcript(request: TranscriptExportRequest) -> Response:
    from core.exporters import export_transcript as export_service

    try:
        content = export_service(request.transcript)
    except ValueError as exc:
        raise _http_error(400, str(exc)) from exc
    return Response(
        content=content,
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="transcript.txt"'},
    )


@app.post("/exports/analysis")
def export_analysis(request: ExportRequest) -> Response:
    from core.exporters import export_analysis as export_service

    try:
        content = export_service(request.as_mapping(), format="markdown")
    except ValueError as exc:
        raise _http_error(400, str(exc)) from exc
    return Response(
        content=content,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="analysis.md"'},
    )


@app.post("/exports/pdf")
def export_pdf(request: ExportRequest) -> Response:
    from core.exporters import generate_pdf_report

    try:
        content = generate_pdf_report(request.as_mapping())
    except ValueError as exc:
        raise _http_error(400, str(exc)) from exc
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="videxa-report.pdf"'},
    )


def _http_error(status_code: int, detail: str):
    from fastapi import HTTPException

    return HTTPException(status_code=status_code, detail=detail)


def _provider_http_error(exc: httpx.HTTPStatusError):
    """Translate common LLM-provider responses into actionable API errors."""
    status = exc.response.status_code
    if status == 402:
        return _http_error(
            402,
            "Gemini API billing or quota limit was reached. Check the Google Cloud Console quota settings before retrying.",
        )
    if status == 429:
        return _http_error(
            429,
            "The Gemini API rate limit has been reached. Wait for the provider limit to reset, then retry.",
        )
    if status in {401, 403}:
        return _http_error(
            503,
            "The Gemini API rejected its credentials. Check GOOGLE_API_KEY in the backend environment.",
        )
    return _http_error(
        502,
        "The Gemini API is temporarily unavailable. Please try again later.",
    )
