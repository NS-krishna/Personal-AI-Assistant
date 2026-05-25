"""
llm_router.py — Smart switcher between Groq (cloud) and Ollama (local).

Routing strategy:
    task_type="code"    → Ollama (qwen2.5-coder excels at code)
    task_type="general" → Groq  (faster for general tasks)
    task_type="fast"    → Groq  (speed priority)

Fallback: If the primary provider fails, automatically retry with the other.
"""

from models.ollama_client import OllamaClient
from models.groq_client import GroqClient


class LLMRouter:
    """Unified LLM interface that routes to the best available provider."""

    def __init__(self):
        self._groq = None
        self._ollama = None

    @property
    def groq(self) -> GroqClient:
        """Lazy-init Groq client (skips if API key is missing)."""
        if self._groq is None:
            try:
                self._groq = GroqClient()
            except (ValueError, RuntimeError):
                self._groq = None
        return self._groq

    @property
    def ollama(self) -> OllamaClient:
        """Lazy-init Ollama client."""
        if self._ollama is None:
            self._ollama = OllamaClient()
        return self._ollama

    def _pick_provider(self, task_type: str) -> str:
        """
        Decide which provider to use based on task type.

        Returns:
            "groq" or "ollama"
        """
        if task_type == "code":
            return "ollama"
        return "groq" if self.groq is not None else "ollama"

    def generate(self, prompt: str, task_type: str = "general", **kwargs) -> str:
        """
        Generate a completion, routed to the best provider.

        Args:
            prompt: The input prompt.
            task_type: "general", "fast", or "code".
            **kwargs: Extra params forwarded to the provider.

        Returns:
            The generated text.
        """
        primary = self._pick_provider(task_type)

        # --- Try primary ---
        try:
            if primary == "groq":
                return self.groq.generate(prompt, **kwargs)
            else:
                return self.ollama.generate(prompt, **kwargs)
        except Exception as primary_error:
            pass

        # --- Fallback to the other ---
        fallback = "ollama" if primary == "groq" else "groq"
        try:
            if fallback == "groq" and self.groq is not None:
                return self.groq.generate(prompt, **kwargs)
            elif fallback == "ollama":
                return self.ollama.generate(prompt, **kwargs)
        except Exception as fallback_error:
            raise RuntimeError(
                f"Both providers failed.\n"
                f"  {primary}: {primary_error}\n"
                f"  {fallback}: {fallback_error}"
            ) from fallback_error

        raise RuntimeError(
            f"Primary provider ({primary}) failed: {primary_error}. "
            f"Fallback ({fallback}) is unavailable."
        )

    def chat(self, messages: list[dict], task_type: str = "general", **kwargs) -> str:
        """
        Chat completion, routed to the best provider.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            task_type: "general", "fast", or "code".
            **kwargs: Extra params forwarded to the provider.

        Returns:
            The assistant's reply text.
        """
        primary = self._pick_provider(task_type)

        # --- Try primary ---
        try:
            if primary == "groq":
                return self.groq.chat(messages, **kwargs)
            else:
                return self.ollama.chat(messages, **kwargs)
        except Exception as primary_error:
            pass

        # --- Fallback to the other ---
        fallback = "ollama" if primary == "groq" else "groq"
        try:
            if fallback == "groq" and self.groq is not None:
                return self.groq.chat(messages, **kwargs)
            elif fallback == "ollama":
                return self.ollama.chat(messages, **kwargs)
        except Exception as fallback_error:
            raise RuntimeError(
                f"Both providers failed.\n"
                f"  {primary}: {primary_error}\n"
                f"  {fallback}: {fallback_error}"
            ) from fallback_error

        raise RuntimeError(
            f"Primary provider ({primary}) failed: {primary_error}. "
            f"Fallback ({fallback}) is unavailable."
        )

    def stream(self, prompt: str, task_type: str = "general", **kwargs):
        """
        Stream tokens from the best available provider.

        Falls back to Ollama since it natively supports streaming.

        Args:
            prompt: The input prompt.
            task_type: "general", "fast", or "code".
            **kwargs: Extra params forwarded to Ollama.

        Yields:
            Individual token strings.
        """
        yield from self.ollama.stream(prompt, **kwargs)

    def get_status(self):
        ollama_ok = False
        groq_ok = False
        
        try:
            ollama_ok = self.ollama.health_check()
        except Exception:
            pass
            
        try:
            if self.groq is not None:
                groq_ok = self.groq.health_check()
        except Exception:
            pass
            
        return {"ollama": ollama_ok, "groq": groq_ok}
