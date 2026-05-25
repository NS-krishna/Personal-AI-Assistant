"""
stt.py — Speech-to-Text using OpenAI Whisper (local).

Loads the Whisper "base" model on first call and transcribes
audio files to text. Runs entirely locally — no API key needed.

First run downloads ~150MB model weights (cached afterwards).

Audio from the browser (webm) is converted to 16kHz mono WAV
via ffmpeg before being passed to Whisper for reliable results.
"""

import os
import subprocess
import tempfile

import whisper

# Lazy-loaded model
_model = None


def _get_model():
    """Load Whisper model once and cache it."""
    global _model
    if _model is None:
        print("[STT] Loading Whisper 'base' model (first run downloads ~150MB)...")
        _model = whisper.load_model("base")
        print("[STT] Whisper model loaded.")
    return _model


def transcribe(audio_file_path: str) -> str:
    """
    Transcribe an audio file to text using Whisper.

    Args:
        audio_file_path: Path to audio file (wav, mp3, etc.)

    Returns:
        Transcribed text string.
    """
    if not os.path.exists(audio_file_path):
        raise FileNotFoundError(f"Audio file not found: {audio_file_path}")

    try:
        model = _get_model()
        result = model.transcribe(audio_file_path, language="en")
        return result.get("text", "").strip()
    except Exception as e:
        raise RuntimeError(f"Whisper transcription failed: {e}") from e


def transcribe_bytes(audio_bytes: bytes, suffix: str = ".webm") -> str:
    """
    Transcribe raw audio bytes to text.

    Saves bytes to a temp file, converts to 16kHz mono WAV via ffmpeg,
    transcribes with Whisper, then cleans up.

    Args:
        audio_bytes: Raw audio data.
        suffix: File extension for temp file (default .webm).

    Returns:
        Transcribed text string, or "No speech detected".
    """
    webm_path = None
    wav_path = None
    try:
        # ── 1. Save raw audio bytes ──────────────────────────────────
        print(f"[STT DEBUG] Audio bytes received: {len(audio_bytes)}")

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
            f.write(audio_bytes)
            webm_path = f.name
        print(f"[STT DEBUG] Saved audio file: {webm_path}")
        print(f"[STT DEBUG] File size on disk: {os.path.getsize(webm_path)} bytes")

        # ── 2. Convert to 16kHz mono WAV via ffmpeg ──────────────────
        wav_path = webm_path.replace(suffix, ".wav")
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-i", webm_path,
            "-ar", "16000",   # 16kHz sample rate (Whisper expects this)
            "-ac", "1",       # mono
            "-c:a", "pcm_s16le",  # 16-bit PCM
            wav_path,
        ]
        print(f"[STT DEBUG] Running ffmpeg: {' '.join(ffmpeg_cmd)}")

        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
        print(f"[STT DEBUG] FFmpeg return code: {result.returncode}")
        if result.stderr:
            # ffmpeg sends most output to stderr even on success
            print(f"[STT DEBUG] FFmpeg stderr (last 500 chars): {result.stderr[-500:]}")

        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg conversion failed: {result.stderr[-300:]}")

        wav_exists = os.path.exists(wav_path)
        wav_size = os.path.getsize(wav_path) if wav_exists else 0
        print(f"[STT DEBUG] WAV exists: {wav_exists}, WAV size: {wav_size} bytes")

        if wav_size < 1000:
            print("[STT DEBUG] WARNING: WAV file is very small -- audio may be empty/silent")

        # ── 3. Transcribe with Whisper ───────────────────────────────
        model = _get_model()
        transcription = model.transcribe(wav_path, language="en")
        text = transcription.get("text", "").strip()
        print(f"[STT DEBUG] Transcription result: '{text}'")

        return text if text else "No speech detected"

    except Exception as e:
        print(f"[STT ERROR] {e}")
        return f"Transcription error: {str(e)}"

    finally:
        # ── 4. Cleanup temp files ────────────────────────────────────
        for path in (webm_path, wav_path):
            if path and os.path.exists(path):
                try:
                    os.unlink(path)
                except OSError:
                    pass
