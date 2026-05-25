"""
tts.py — Text-to-Speech configuration.

TTS is handled entirely in the browser using the Web Speech API
(window.speechSynthesis). No backend processing is needed.

This module provides voice configuration that the frontend can
query to set up speech synthesis preferences.
"""


def get_voices() -> list[dict]:
    """
    Return available voice settings for the frontend.

    The actual voice selection happens in the browser via
    SpeechSynthesis API. These are suggested defaults.
    """
    return [
        {
            "name": "Default",
            "lang": "en-US",
            "rate": 1.0,
            "pitch": 1.0,
        },
        {
            "name": "Slow",
            "lang": "en-US",
            "rate": 0.8,
            "pitch": 1.0,
        },
        {
            "name": "Fast",
            "lang": "en-US",
            "rate": 1.3,
            "pitch": 1.0,
        },
    ]


def get_default_settings() -> dict:
    """Return default TTS settings."""
    return {
        "engine": "browser",
        "api": "SpeechSynthesis",
        "lang": "en-US",
        "rate": 1.0,
        "pitch": 1.0,
        "auto_speak": True,
    }
