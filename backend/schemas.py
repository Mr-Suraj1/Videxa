"""Validated request and response models for the Videxa API."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class HealthResponse(BaseModel):
    status: Literal["ok"]


class VideoSession(BaseModel):
    session_id: str
    title: str
    created_at: str
    processing_status: str = "completed"
    analysis_status: str = "completed"


class SessionStatusResponse(VideoSession):
    analysis_error: str | None = None


class SessionListResponse(BaseModel):
    sessions: list[VideoSession]


class ProcessingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: str = Field(min_length=1, max_length=4096)
    language: Literal["english", "hinglish"] = "english"

    @field_validator("source")
    @classmethod
    def source_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("source must not be blank")
        return value.strip()


class AnalysisResponse(BaseModel):
    title: str
    summary: str
    action_items: str
    key_decisions: str
    open_questions: str


class SessionContentResponse(BaseModel):
    session_id: str
    title: str
    transcript: str
    analysis: AnalysisResponse | None = None


class ProcessingResponse(BaseModel):
    status: Literal["completed"]
    session_id: str
    transcript: str
    analysis: AnalysisResponse


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1, max_length=10_000)
    session_id: str = Field(
        min_length=1,
        max_length=128,
        pattern=r"^[A-Za-z0-9_-]+$",
    )

    @field_validator("question")
    @classmethod
    def question_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("question must not be blank")
        return value.strip()


class ChatResponse(BaseModel):
    session_id: str
    answer: str


class MultiChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_ids: list[str] = Field(min_length=1, max_length=20)
    question: str = Field(min_length=1, max_length=10_000)

    @field_validator("session_ids")
    @classmethod
    def session_ids_must_be_valid(cls, values: list[str]) -> list[str]:
        normalized = [value.strip() for value in values]
        if any(not value or not value.replace("-", "").replace("_", "").isalnum() for value in normalized):
            raise ValueError("session_ids must contain valid session IDs")
        return list(dict.fromkeys(normalized))

    @field_validator("question")
    @classmethod
    def question_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("question must not be blank")
        return value.strip()


class MultiChatResponse(BaseModel):
    session_ids: list[str]
    answer: str


class ExportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, max_length=10_000)
    transcript: str | None = Field(default=None, max_length=2_000_000)
    summary: str | None = Field(default=None, max_length=2_000_000)
    action_items: Any = None
    key_decisions: Any = None
    open_questions: Any = None
    source: str | None = Field(default=None, max_length=4096)
    source_url: str | None = Field(default=None, max_length=4096)
    video_url: str | None = Field(default=None, max_length=4096)

    def as_mapping(self) -> dict[str, Any]:
        return self.model_dump(exclude_none=True)


class TranscriptExportRequest(ExportRequest):
    transcript: str = Field(min_length=1, max_length=2_000_000)

    @field_validator("transcript")
    @classmethod
    def transcript_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("transcript must not be blank")
        return value
