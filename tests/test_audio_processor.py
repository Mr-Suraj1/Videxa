from pathlib import Path

import pytest

import utils.audio_processor as audio_processor
from utils.audio_processor import InputValidationError, MediaProcessingError, validate_input


@pytest.mark.parametrize("url", [
    "https://www.youtube.com/watch?v=abc123",
    "https://youtu.be/abc123",
])
def test_accepts_youtube_urls(url):
    assert validate_input(url) == ("youtube", url)


@pytest.mark.parametrize("source", ["", "https://example.com/video", "ftp://youtube.com/watch?v=x", "https://youtube.com/"])
def test_rejects_invalid_urls_and_empty_input(source):
    with pytest.raises(InputValidationError):
        validate_input(source)


@pytest.mark.parametrize("url", [
    "file:///C:/Windows/system32.mp4",
    "javascript://youtube.com/watch?v=abc123",
    "data:text/plain,youtube.com",
    "https://youtube.com.evil.example/watch?v=abc123",
    "https://www.youtube.com@evil.example/watch?v=abc123",
    "https://youtube.com/shorts/",
    "https://youtu.be/abc123/extra",
    "https://youtube.com:bad/watch?v=abc123",
])
def test_rejects_unsafe_or_malformed_youtube_urls(url):
    with pytest.raises(InputValidationError):
        validate_input(url)


def test_accepts_existing_supported_local_file(tmp_path):
    media = tmp_path / "meeting.mp3"
    media.touch()
    kind, path = validate_input(str(media))
    assert kind == "file"
    assert Path(path) == media.resolve()


def test_windows_style_path_is_treated_as_a_local_file(monkeypatch):
    monkeypatch.setattr(Path, "is_file", lambda _: True)
    monkeypatch.setattr(Path, "stat", lambda _: type("Stat", (), {"st_size": 0})())
    kind, _ = validate_input(r"C:\meetings\recording.mp3")
    assert kind == "file"


def test_rejects_missing_or_unsupported_local_file(tmp_path):
    with pytest.raises(InputValidationError, match="does not exist"):
        validate_input(str(tmp_path / "missing.mp4"))
    text_file = tmp_path / "notes.txt"
    text_file.touch()
    with pytest.raises(InputValidationError, match="Unsupported"):
        validate_input(str(text_file))


def test_rejects_oversized_local_media(tmp_path, monkeypatch):
    media = tmp_path / "large.mp4"
    media.write_bytes(b"x" * (2 * 1024 * 1024))
    monkeypatch.setenv("VIDEXA_MAX_MEDIA_SIZE_MB", "1")
    with pytest.raises(InputValidationError, match="size limit"):
        validate_input(str(media))


def test_download_revalidates_urls_before_yt_dlp(monkeypatch, tmp_path):
    monkeypatch.setattr(audio_processor, "_require_ffmpeg", lambda: None)
    with pytest.raises(InputValidationError):
        audio_processor.download_youtube_audio("https://evil.example/video", tmp_path)


def test_cleanup_removes_only_videxa_temp_directory(monkeypatch, tmp_path):
    monkeypatch.setattr(audio_processor, "DOWNLOAD_DIR", tmp_path)
    session_dir = tmp_path / "session_random"
    session_dir.mkdir()
    chunk = session_dir / "audio.wav_chunk_0.wav"
    chunk.write_bytes(b"audio")
    audio_processor.cleanup_audio_files([str(chunk)])
    assert not session_dir.exists()


def test_cleanup_failure_is_logged_without_exposing_paths(monkeypatch, tmp_path, caplog):
    monkeypatch.setattr(audio_processor, "DOWNLOAD_DIR", tmp_path)
    session_dir = tmp_path / "session_random"
    session_dir.mkdir()
    chunk = session_dir / "audio.wav_chunk_0.wav"
    chunk.write_bytes(b"audio")
    monkeypatch.setattr(audio_processor.shutil, "rmtree", lambda _: (_ for _ in ()).throw(OSError("blocked")))
    audio_processor.cleanup_audio_files([str(chunk)])
    assert "Unable to clean Videxa temporary media directory" in caplog.text
    assert str(session_dir) not in caplog.text


def test_missing_ffmpeg_raises_safe_error(monkeypatch):
    monkeypatch.setattr(audio_processor.shutil, "which", lambda _: None)
    with pytest.raises(MediaProcessingError, match="FFmpeg is required"):
        audio_processor._require_ffmpeg()
