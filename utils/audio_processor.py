"""Validated, temporary audio preparation for Videxa."""

from __future__ import annotations

import shutil
import uuid
import logging
import os
import re
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import yt_dlp
from pydub import AudioSegment

DOWNLOAD_DIR = Path("downloades")
logger = logging.getLogger(__name__)
DEFAULT_MAX_MEDIA_SIZE_MB = 2_048
SUPPORTED_MEDIA_EXTENSIONS = {
    ".aac", ".avi", ".flac", ".m4a", ".mkv", ".mov", ".mp3", ".mp4", ".mpeg",
    ".mpg", ".ogg", ".wav", ".webm", ".wma",
}
YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be", "www.youtu.be"}


class InputValidationError(ValueError):
    """An input cannot safely be processed by the media pipeline."""


class MediaProcessingError(RuntimeError):
    """Download, conversion, or chunking could not produce usable audio."""


def _max_media_size_bytes() -> int:
    """Return a bounded local-media size limit without exposing configuration."""
    try:
        size_mb = int(os.getenv("VIDEXA_MAX_MEDIA_SIZE_MB", str(DEFAULT_MAX_MEDIA_SIZE_MB)))
    except ValueError:
        logger.warning("Invalid VIDEXA_MAX_MEDIA_SIZE_MB; using the default limit")
        size_mb = DEFAULT_MAX_MEDIA_SIZE_MB
    return max(1, size_mb) * 1024 * 1024


def _is_protected_system_path(path: Path) -> bool:
    """Prevent accidental processing of files from common Windows system locations."""
    protected_roots = [
        os.getenv("SystemRoot"),
        os.getenv("ProgramFiles"),
        os.getenv("ProgramFiles(x86)"),
    ]
    return any(
        root and path.is_relative_to(Path(root).resolve())
        for root in protected_roots
    )


def validate_input(source: str) -> tuple[str, str]:
    """Validate a YouTube URL or an existing supported local media file."""
    if not source or not source.strip():
        raise InputValidationError("Enter a YouTube URL or a path to a media file.")
    candidate = source.strip()
    parsed = urlparse(candidate)
    windows_path = len(candidate) > 2 and candidate[1] == ":" and candidate[2] in {"/", "\\"}
    if (parsed.scheme or parsed.netloc) and not windows_path:
        try:
            port = parsed.port
        except ValueError as exc:
            raise InputValidationError("Enter a valid YouTube URL (youtube.com or youtu.be).") from exc
        if (
            parsed.scheme not in {"http", "https"}
            or parsed.hostname not in YOUTUBE_HOSTS
            or parsed.username
            or parsed.password
            or port not in {None, 80, 443}
        ):
            raise InputValidationError("Enter a valid YouTube URL (youtube.com or youtu.be).")
        if parsed.hostname in {"youtu.be", "www.youtu.be"}:
            video_id = parsed.path.strip("/")
            valid_path = bool(video_id) and "/" not in video_id
        else:
            video_id = parse_qs(parsed.query).get("v", [""])[0]
            valid_path = bool(video_id) or bool(
                re.fullmatch(r"/(?:shorts|live|embed)/[^/]+/?", parsed.path)
            )
        if not valid_path:
            raise InputValidationError("This YouTube URL is malformed or missing a video identifier.")
        return "youtube", candidate

    path = Path(candidate).expanduser().resolve()
    if not path.is_file():
        raise InputValidationError("The local media file does not exist or is not a file.")
    if _is_protected_system_path(path):
        raise InputValidationError("Files from protected system folders cannot be processed.")
    if path.suffix.lower() not in SUPPORTED_MEDIA_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_MEDIA_EXTENSIONS))
        raise InputValidationError(f"Unsupported media file type. Supported types: {supported}.")
    if path.stat().st_size > _max_media_size_bytes():
        raise InputValidationError("The media file exceeds the configured size limit.")
    return "file", str(path)


def _require_ffmpeg() -> None:
    if not shutil.which("ffmpeg"):
        raise MediaProcessingError("FFmpeg is required for media conversion. Install FFmpeg and add it to PATH.")


def _new_work_dir() -> Path:
    work_dir = DOWNLOAD_DIR / f"session_{uuid.uuid4().hex}"
    work_dir.mkdir(parents=True, exist_ok=False)
    return work_dir


def download_youtube_audio(url: str, work_dir: Path) -> str:
    source_kind, validated_url = validate_input(url)
    if source_kind != "youtube":
        raise InputValidationError("Enter a valid YouTube URL (youtube.com or youtu.be).")
    _require_ffmpeg()
    options = {
        "format": "bestaudio/best",
        "outtmpl": str(work_dir / "source.%(ext)s"),
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "wav", "preferredquality": "192"}],
        "quiet": True,
        "noplaylist": True,
    }
    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.extract_info(validated_url, download=True)
    except Exception as exc:
        logger.warning("YouTube audio download failed")
        raise MediaProcessingError("Could not download audio from that YouTube video.") from exc
    wav_files = list(work_dir.glob("*.wav"))
    if not wav_files:
        raise MediaProcessingError("The YouTube download completed but produced no WAV audio.")
    return str(wav_files[0])


def convert_to_wav(input_path: str, work_dir: Path) -> str:
    _require_ffmpeg()
    output_path = work_dir / "audio.wav"
    try:
        audio = AudioSegment.from_file(input_path)
        if len(audio) == 0:
            raise MediaProcessingError("The media file contains no audio.")
        audio.set_channels(1).set_frame_rate(16000).export(output_path, format="wav")
    except MediaProcessingError:
        raise
    except Exception as exc:
        logger.warning("Local media conversion failed")
        raise MediaProcessingError("Could not read or convert this media file. It may be corrupted or unsupported.") from exc
    if not output_path.is_file() or output_path.stat().st_size == 0:
        raise MediaProcessingError("Audio conversion produced an empty output file.")
    return str(output_path)


def chunk_audio(wav_path: str, chunk_minutes: int = 10) -> list[str]:
    if chunk_minutes < 1:
        raise ValueError("Chunk length must be at least one minute.")
    try:
        audio = AudioSegment.from_wav(wav_path)
        if len(audio) == 0:
            raise MediaProcessingError("The converted audio is empty.")
        chunks = []
        for index, start in enumerate(range(0, len(audio), chunk_minutes * 60 * 1000)):
            chunk_path = Path(f"{wav_path}_chunk_{index}.wav")
            audio[start:start + chunk_minutes * 60 * 1000].export(chunk_path, format="wav")
            if not chunk_path.is_file() or chunk_path.stat().st_size == 0:
                raise MediaProcessingError("Audio chunking produced an empty chunk.")
            chunks.append(str(chunk_path))
        return chunks
    except MediaProcessingError:
        raise
    except Exception as exc:
        logger.warning("Audio chunking failed")
        raise MediaProcessingError("Could not split the audio into transcription chunks.") from exc


def cleanup_audio_files(chunks: list[str]) -> None:
    """Remove only Videxa-created temporary session directories."""
    download_root = DOWNLOAD_DIR.resolve()
    for chunk in chunks:
        path = Path(chunk).resolve()
        try:
            relative = path.relative_to(download_root)
        except ValueError:
            continue
        if relative.parts and relative.parts[0].startswith("session_"):
            _cleanup_work_dir(download_root / relative.parts[0])


def _cleanup_work_dir(work_dir: Path) -> None:
    """Best-effort cleanup with a safe diagnostic when the filesystem refuses it."""
    try:
        shutil.rmtree(work_dir)
    except FileNotFoundError:
        return
    except OSError:
        logger.warning("Unable to clean Videxa temporary media directory")


def process_input(source: str) -> list[str]:
    kind, value = validate_input(source)
    work_dir = _new_work_dir()
    try:
        wav_path = download_youtube_audio(value, work_dir) if kind == "youtube" else convert_to_wav(value, work_dir)
        chunks = chunk_audio(wav_path)
        logger.info("Media preparation completed")
        return chunks
    except Exception:
        _cleanup_work_dir(work_dir)
        raise
