"""
document_summarizer_tool.py — Document processing and Q&A.

Capabilities:
    - summarize(text)              → Summarize text via LLMRouter
    - summarize_file(filepath)     → Extract text from PDF/DOCX, then summarize
    - extract_text_from_file(path) → Extract raw text only (no summarisation)
    - answer_from_document(q, doc) → Answer a question using document context

PDF extraction uses PyMuPDF (fitz).
DOCX extraction uses python-docx.
"""

from pathlib import Path

import fitz  # PyMuPDF
from docx import Document

from models.llm_router import LLMRouter


# Module-level router (lazy-initialised on first call)
_router: LLMRouter | None = None


def _get_router() -> LLMRouter:
    """Return a shared LLMRouter instance."""
    global _router
    if _router is None:
        _router = LLMRouter()
    return _router


def summarize(text: str) -> str:
    """
    Summarize a block of text using the LLM.

    Args:
        text: Raw text to summarize.

    Returns:
        A concise summary string.

    Raises:
        ValueError: If text is empty.
        RuntimeError: If the LLM call fails.
    """
    if not text or not text.strip():
        raise ValueError("Cannot summarize empty text.")

    prompt = (
        "Summarize the following text concisely in 2-3 sentences. "
        "Focus on the key points.\n\n"
        f"Text:\n{text}\n\n"
        "Summary:"
    )
    try:
        return _get_router().generate(prompt, task_type="general")
    except Exception as e:
        raise RuntimeError(f"Summarization failed: {e}") from e


def _extract_text_pdf(filepath: str) -> str:
    """
    Extract all text from a PDF file using PyMuPDF.

    Args:
        filepath: Path to the PDF file.

    Returns:
        The extracted text.

    Raises:
        FileNotFoundError: If the file doesn't exist.
        RuntimeError: If extraction fails.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {filepath}")

    try:
        doc = fitz.open(str(path))
        text_parts = []
        for page in doc:
            text_parts.append(page.get_text())
        doc.close()
        return "\n".join(text_parts).strip()
    except Exception as e:
        raise RuntimeError(f"Failed to extract text from PDF: {e}") from e


def _extract_text_docx(filepath: str) -> str:
    """
    Extract all text from a DOCX file using python-docx.

    Args:
        filepath: Path to the DOCX file.

    Returns:
        The extracted text.

    Raises:
        FileNotFoundError: If the file doesn't exist.
        RuntimeError: If extraction fails.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"DOCX file not found: {filepath}")

    try:
        doc = Document(str(path))
        text_parts = [para.text for para in doc.paragraphs if para.text.strip()]
        return "\n".join(text_parts).strip()
    except Exception as e:
        raise RuntimeError(f"Failed to extract text from DOCX: {e}") from e


def extract_text_from_file(filepath: str) -> str:
    """
    Extract raw text from a PDF or DOCX file (no summarisation).

    Args:
        filepath: Path to the file (must be .pdf or .docx).

    Returns:
        The extracted raw text.
    """
    path = Path(filepath)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        text = _extract_text_pdf(filepath)
    elif suffix == ".docx":
        text = _extract_text_docx(filepath)
    else:
        raise ValueError(
            f"Unsupported file type: '{suffix}'. Only .pdf and .docx are supported."
        )

    if not text.strip():
        return ""

    # Truncate very long documents to avoid exceeding context window
    max_chars = 8000
    if len(text) > max_chars:
        text = text[:max_chars] + "\n\n[... truncated ...]"

    return text


def summarize_file(filepath: str) -> str:
    """
    Read a PDF or DOCX file, extract its text, and summarize it.
    """
    text = extract_text_from_file(filepath)
    if not text:
        return "The document appears to be empty — no text could be extracted."
    return summarize(text)


def answer_from_document(question: str, document_text: str) -> str:
    """
    Answer a user question using stored document text as context.

    Args:
        question: The user's question about the document.
        document_text: The raw text extracted from the uploaded document.

    Returns:
        An answer based on the document content.
    """
    if not document_text or not document_text.strip():
        return "No document is currently loaded. Please upload a document first."

    prompt = (
        "You are a helpful assistant. The user has uploaded a document. "
        "Answer their question based ONLY on the document content below. "
        "If the answer is not in the document, say so.\n\n"
        f"=== DOCUMENT ===\n{document_text}\n=== END DOCUMENT ===\n\n"
        f"User question: {question}\n\n"
        "Answer:"
    )
    try:
        return _get_router().generate(prompt, task_type="general")
    except Exception as e:
        raise RuntimeError(f"Could not answer from document: {e}") from e
