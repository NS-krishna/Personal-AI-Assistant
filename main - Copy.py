"""
main.py — Entry point for the Personal AI Agent.

Starts the FastAPI server with all routes mounted.
Run with:  python main.py
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from api.routes import router as api_router
from api.streaming import stream_router


# ── App Factory ──────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Personal AI Agent",
        description=(
            "Multi-agent personal assistant with Gmail, Calendar, "
            "RAG, and voice support — powered by Groq + Ollama."
        ),
        version="0.1.0",
    )

    # CORS — allow React dev server and any origin during development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount API routes
    app.include_router(api_router)
    app.include_router(stream_router)

    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "name": "Personal AI Agent",
            "version": "0.1.0",
            "status": "running",
            "endpoints": {
                "chat": "POST /chat",
                "stream": "POST /chat/stream",
                "health": "GET /health",
                "memory": "GET /memory",
                "clear_memory": "DELETE /memory",
                "upload": "POST /upload",
                "docs": "GET /docs",
            },
        }

    return app


# ── Application instance ────────────────────────────────────────────────

app = create_app()


# ── Run ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print()
    print("=" * 55)
    print("  [Bot] Personal AI Agent")
    print("=" * 55)
    print(f"  Ollama model  : {settings.OLLAMA_MODEL}")
    print(f"  Groq model    : {settings.GROQ_MODEL}")
    print(f"  Server        : http://{settings.API_HOST}:{settings.API_PORT}")
    print(f"  Swagger docs  : http://localhost:{settings.API_PORT}/docs")
    print()
    print("  Endpoints:")
    print("    POST   /chat          — Agent chat pipeline")
    print("    POST   /chat/stream   — Streaming response (SSE)")
    print("    GET    /health        — Service health check")
    print("    GET    /memory        — Recent conversations")
    print("    DELETE /memory        — Clear all memory")
    print("    POST   /upload        — Upload PDF/DOCX for summary")
    print("=" * 55)
    print()

    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
    )
