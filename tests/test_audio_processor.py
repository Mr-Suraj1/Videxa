from pathlib import Path

import pytest

from utils.audio_processor import InputValidationError, validate_input


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


def test_accepts_existing_supported_local_file(tmp_path):
    media = tmp_path / "meeting.mp3"
    media.touch()
    kind, path = validate_input(str(media))
    assert kind == "file"
    assert Path(path) == media.resolve()


def test_windows_style_path_is_treated_as_a_local_file(monkeypatch):
    monkeypatch.setattr(Path, "is_file", lambda _: True)
    kind, _ = validate_input(r"C:\meetings\recording.mp3")
    assert kind == "file"


def test_rejects_missing_or_unsupported_local_file(tmp_path):
    with pytest.raises(InputValidationError, match="does not exist"):
        validate_input(str(tmp_path / "missing.mp4"))
    text_file = tmp_path / "notes.txt"
    text_file.touch()
    with pytest.raises(InputValidationError, match="Unsupported"):
        validate_input(str(text_file))
