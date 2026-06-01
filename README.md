# Videxa

Videxa is a Python-based audio processing project focused on downloading, converting, and chunking audio files.

## Features

- Download audio from YouTube URLs using `yt-dlp`
- Convert audio/video files to WAV format using `pydub`
- Split long audio recordings into smaller WAV chunks
- Designed to support speech-to-text and RAG workflows with local Whisper, translation, and LangChain dependencies

## Requirements

Install dependencies from `Requirements.txt`:

```bash
pip install -r Requirements.txt
```

> Note: `ffmpeg` must be installed on your system separately for audio conversion to work.

## Usage

The main audio utility lives in `utils/audio_processor.py`.

### Process a YouTube video

```python
from utils.audio_processor import process_input

chunks = process_input("https://www.youtube.com/watch?v=YOUR_VIDEO_ID")
print(chunks)
```

### Process a local file

```python
from utils.audio_processor import process_input

chunks = process_input("path/to/audio_or_video_file.mp4")
print(chunks)
```

## Project Structure

- `Requirements.txt` - Python dependencies
- `utils/audio_processor.py` - core audio download, convert, and chunking utilities
- `downloades/` - output directory for downloaded audio files
- `.env` - optional environment file for secrets and API keys

## Notes

- The repository currently provides a utility module rather than a complete CLI or Streamlit app entrypoint.
- If you want to extend Videxa, add a main application script or Streamlit frontend to orchestrate audio processing and transcription.
