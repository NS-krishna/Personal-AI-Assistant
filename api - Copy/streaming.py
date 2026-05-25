"""
streaming.py — Server-Sent Events (SSE) streaming handler.

Provides a streaming chat endpoint that yields tokens one at a time
from the Ollama local model, similar to ChatGPT's typing effect.
"""

import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from models.ollama_client import OllamaClient

stream_router = APIRouter()


class StreamRequest(BaseModel):
    text: str


async def _token_generator(prompt: str):
    """
    Async generator that wraps OllamaClient.stream() into SSE events.

    Each yielded string is a valid SSE data line:
        data: {"token": "hello", "done": false}\n\n

    The final event signals completion:
        data: {"token": "", "done": true}\n\n
    """
    client = OllamaClient()

    try:
        for token in client.stream(prompt):
            event = json.dumps({"token": token, "done": False})
            yield f"data: {event}\n\n"

        # Signal completion
        yield f"data: {json.dumps({'token': '', 'done': True})}\n\n"

    except Exception as e:
        error_event = json.dumps({"error": str(e), "done": True})
        yield f"data: {error_event}\n\n"


@stream_router.post("/chat/stream")
async def chat_stream(request: StreamRequest):
    """
    Stream a response token-by-token via Server-Sent Events.

    Uses the local Ollama model for streaming.
    The client should read this as an EventSource.
    """
    return StreamingResponse(
        _token_generator(request.text),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
