"""
routes.py — All FastAPI REST endpoints.

Endpoints:
    POST   /chat              — Agent pipeline (with document context injection)
    GET    /health            — Service health check
    GET    /memory            — Recent conversation history
    DELETE /memory            — Clear all memory
    POST   /upload            — Upload PDF/DOCX, extract & store text for Q&A
    POST   /voice/transcribe  — Transcribe audio to text via Whisper
"""

import os
import time
import tempfile
from io import BytesIO

from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel

from agent.planner import PlannerAgent
from agent.executor import ExecutorAgent
from agent.critic import CriticAgent
from memory.memory_manager import MemoryManager
from models.llm_router import LLMRouter

# ── Initialise agents once (shared across requests) ─────────────────────

planner = PlannerAgent()
executor = ExecutorAgent()
critic = CriticAgent()
memory = MemoryManager()
router_llm = LLMRouter()

# ── Uploaded document store ──────────────────────────────────────────────
uploaded_document_text = ""
uploaded_document_name = ""

router = APIRouter()


# ── Request / Response schemas ───────────────────────────────────────────

class ChatRequest(BaseModel):
    text: str


class ChatResponse(BaseModel):
    reply: str
    plan: list
    score: int
    feedback: str
    needs_retry: bool


class MemoryResponse(BaseModel):
    conversations: list


class HealthResponse(BaseModel):
    status: str
    ollama: bool
    groq: bool


# ── Endpoints ────────────────────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Process a user message through the full agent pipeline.
    If a document is uploaded, injects document content into the prompt.
    """
    global uploaded_document_text, uploaded_document_name
    start_time = time.time()

    user_text = request.text.strip()
    if not user_text:
        raise HTTPException(status_code=400, detail="Message text cannot be empty.")

    # Inject document context if a document was uploaded
    if uploaded_document_text:
        enriched_input = (
            f"The user has uploaded a document called '{uploaded_document_name}'.\n"
            f"Document content: {uploaded_document_text}\n\n"
            f"User question: {user_text}"
        )
    else:
        enriched_input = user_text

    # 1. Get memory context
    context = memory.get_context(user_text)

    # 2. Plan (use original user text for planning, not the enriched one)
    plan = planner.plan(user_text)

    # 3. Execute (use enriched_input so the LLM has document context)
    response = executor.execute(plan, enriched_input)

    # 4. Evaluate
    evaluation = critic.evaluate(user_text, response)

    # 5. Retry once if quality is low
    if evaluation.get("needs_retry", False):
        response = executor.execute(plan, enriched_input)
        evaluation = critic.evaluate(user_text, response)

    # 6. Save to memory
    memory.save_interaction(user_text, response)

    # 7. Log interaction for evaluation dashboard
    response_time_ms = (time.time() - start_time) * 1000
    try:
        from evaluation.evaluator import log_interaction
        log_interaction(
            tool_used=plan[0]["tool"] if plan else "chat",
            score=evaluation.get("score", 0),
            needs_retry=evaluation.get("needs_retry", False),
            response_time_ms=response_time_ms,
        )
    except Exception:
        pass  # Don't let logging break the chat pipeline

    return ChatResponse(
        reply=response,
        plan=plan,
        score=evaluation.get("score", 0),
        feedback=evaluation.get("feedback", ""),
        needs_retry=evaluation.get("needs_retry", False),
    )


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Check health status of LLM providers."""
    status = router_llm.get_status()
    return HealthResponse(
        status="ok",
        ollama=status.get("ollama", False),
        groq=status.get("groq", False),
    )


@router.get("/memory", response_model=MemoryResponse)
async def get_memory():
    """Return last 5 conversations from episodic memory."""
    recent = memory.get_recent_conversations(k=5)
    return MemoryResponse(conversations=recent)


@router.delete("/memory")
async def clear_memory():
    """Clear all episodic and semantic memory."""
    memory.clear_all()
    return {"message": "Memory cleared successfully"}


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a PDF or DOCX file — extract text and store for Q&A.
    Does NOT auto-summarize. User asks questions via /chat.
    """
    global uploaded_document_text, uploaded_document_name

    content = await file.read()

    try:
        if file.filename.endswith(".pdf"):
            import fitz
            doc = fitz.open(stream=content, filetype="pdf")
            text = ""
            for page in doc:
                text += page.get_text()
        elif file.filename.endswith(".docx"):
            from docx import Document
            doc = Document(BytesIO(content))
            text = "\n".join([p.text for p in doc.paragraphs])
        else:
            text = content.decode("utf-8")

        # Store it — don't summarize yet
        uploaded_document_text = text[:5000]
        uploaded_document_name = file.filename

        return {
            "message": f"📄 '{file.filename}' uploaded! Now ask me anything about it.",
            "filename": file.filename,
        }
    except Exception as e:
        return {"message": f"❌ Error: {str(e)}"}


@router.delete("/upload")
async def clear_document():
    """Clear the currently uploaded document."""
    global uploaded_document_text, uploaded_document_name
    uploaded_document_text = ""
    uploaded_document_name = ""
    return {"message": "Uploaded document cleared."}


# ── Evaluation ───────────────────────────────────────────────────────────

@router.get("/evaluation/stats")
async def evaluation_stats():
    """Return aggregated evaluation metrics for the dashboard."""
    from evaluation.evaluator import get_stats
    return get_stats()


# ── Voice ────────────────────────────────────────────────────────────────

@router.post("/voice/transcribe")
async def voice_transcribe(file: UploadFile = File(...)):
    """
    Transcribe uploaded audio to text using Whisper.
    Accepts webm, wav, mp3 formats.
    """
    try:
        audio_bytes = await file.read()
        suffix = os.path.splitext(file.filename or ".webm")[1] or ".webm"

        from voice.stt import transcribe_bytes
        text = transcribe_bytes(audio_bytes, suffix=suffix)

        if not text.strip():
            return {"text": "", "error": "No speech detected"}

        return {"text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {e}")

