import whisper
import os
import logging
import time
import requests
from pydub import AudioSegment

# Sarvam's sync STT-translate API rejects audio longer than 30s.
# We slice each chunk into 25s pieces (with a 5s safety margin) before sending.
SARVAM_PIECE_SECONDS = 25


WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")


SARVAM_STT_TRANSLATE_URL = "https://api.sarvam.ai/speech-to-text-translate"
SARVAM_MODEL = os.getenv("SARVAM_STT_MODEL", "saaras:v2.5")
SARVAM_TIMEOUT_SECONDS = 120
SARVAM_MAX_ATTEMPTS = 2
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

logger = logging.getLogger(__name__)

_model = None


class TranscriptionError(RuntimeError):
    """A transcription provider could not process the requested audio."""


def _sarvam_api_key() -> str | None:
    """Read the configured key at use time, after dotenv has initialized."""
    return os.getenv("SARVAM_API_KEY")


def load_model():

    global _model  

    if _model is None: 
        logger.info("Loading Whisper model")
        try:
            _model = whisper.load_model(WHISPER_MODEL)
        except Exception as exc:
            logger.exception("Whisper model could not be loaded")
            raise TranscriptionError("Whisper could not be started. Check the local model setup.") from exc
        logger.info("Whisper model loaded")
    return _model 


def transcribe_chunk_whisper(chunk_path: str) -> str:

    model = load_model()  

    try:
        result = model.transcribe(chunk_path, task="transcribe")
        return result["text"]
    except Exception as exc:
        logger.exception("Whisper transcription failed")
        raise TranscriptionError("Whisper could not transcribe this audio chunk.") from exc


def _send_to_sarvam(piece_path: str) -> str:
    """Send one ≤30s WAV file to Sarvam and return the English transcript."""
    api_key = _sarvam_api_key()
    if not api_key:
        raise TranscriptionError("Sarvam is not configured. Set SARVAM_API_KEY before using Hinglish transcription.")
    headers = {"api-subscription-key": api_key}

    for attempt in range(1, SARVAM_MAX_ATTEMPTS + 1):
        try:
            with open(piece_path, "rb") as f:
                files = {"file": (os.path.basename(piece_path), f, "audio/wav")}
                data = {"model": SARVAM_MODEL, "with_diarization": "false"}
                response = requests.post(
                    SARVAM_STT_TRANSLATE_URL,
                    headers=headers,
                    files=files,
                    data=data,
                    timeout=SARVAM_TIMEOUT_SECONDS,
                )
            if response.ok:
                try:
                    return response.json().get("transcript", "")
                except ValueError as exc:
                    logger.warning("Sarvam returned invalid JSON")
                    raise TranscriptionError("Sarvam returned an invalid transcription response.") from exc
            if response.status_code not in RETRYABLE_STATUS_CODES or attempt == SARVAM_MAX_ATTEMPTS:
                logger.warning("Sarvam transcription request failed with status %s", response.status_code)
                raise TranscriptionError("Sarvam could not transcribe this audio. Check your API configuration and try again.")
            logger.warning("Sarvam temporary failure; retrying once")
        except requests.RequestException as exc:
            if attempt == SARVAM_MAX_ATTEMPTS:
                logger.warning("Sarvam network request failed after retry")
                raise TranscriptionError("Sarvam is temporarily unavailable. Please try again.") from exc
            logger.warning("Sarvam network request failed; retrying once")
        time.sleep(1)
    raise TranscriptionError("Sarvam is temporarily unavailable. Please try again.")


def transcribe_chunk_sarvam(chunk_path: str) -> str:
    """
    Sarvam sync API only accepts ≤30s audio. We split this chunk into
    25-second pieces, send each separately, and join the transcripts.
    """
    if not _sarvam_api_key():
        raise TranscriptionError("Sarvam is not configured. Set SARVAM_API_KEY before using Hinglish transcription.")

    audio = AudioSegment.from_wav(chunk_path)
    piece_ms = SARVAM_PIECE_SECONDS * 1000

    full_text = ""
    total_pieces = (len(audio) + piece_ms - 1) // piece_ms

    for i, start in enumerate(range(0, len(audio), piece_ms)):
        piece = audio[start: start + piece_ms]
        piece_path = f"{chunk_path}_sv_{i}.wav"
        piece.export(piece_path, format="wav")

        try:
            logger.info("Submitting Sarvam audio piece %s of %s", i + 1, total_pieces)
            full_text += _send_to_sarvam(piece_path) + " "
        finally:
            if os.path.exists(piece_path):
                try:
                    os.remove(piece_path)
                except OSError:
                    logger.warning("Unable to remove temporary Sarvam audio piece")

    return full_text.strip()

   



def transcribe_chunk(chunk_path: str, language: str = "english") -> str:
    """
    Route one chunk to Whisper or Sarvam depending on language choice.
    - english  → Whisper (local model)
    - hinglish → Sarvam (translates to English while transcribing)
    """
    if language.lower() == "hinglish":
        return transcribe_chunk_sarvam(chunk_path)
    return transcribe_chunk_whisper(chunk_path)


def transcribe_all(chunks: list, language: str = "english") -> str:

    full_transcript = "" 

    engine = "Sarvam AI" if language.lower() == "hinglish" else "Whisper"
    logger.info("Starting transcription with %s", engine)

    for i, chunk in enumerate(chunks):  

        logger.info("Transcribing audio chunk %s of %s", i + 1, len(chunks))

        text = transcribe_chunk(chunk, language=language)  

        full_transcript += text + " "  

    logger.info("Transcription complete")

    return full_transcript.strip()
