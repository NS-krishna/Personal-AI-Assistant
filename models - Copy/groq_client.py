"""
groq_client.py — Cloud LLM wrapper using Groq API (llama3-70b).

Ultra-fast inference via Groq's cloud API.
Uses the official `groq` Python package.

Methods:
    generate(prompt)   → single-prompt completion
    chat(messages)     → multi-turn conversation
    health_check()     → True if API is reachable and key is valid
"""

from groq import Groq

from config import settings


class GroqClient:
    """Wrapper around the Groq cloud inference API."""

    def __init__(self, model: str = None, api_key: str = None):
        self.model = model or settings.GROQ_MODEL
        self.api_key = api_key or settings.GROQ_API_KEY

        if not self.api_key:
            raise ValueError(
                "GROQ_API_KEY is not set. "
                "Add it to your .env file or pass it directly."
            )

        try:
            self.client = Groq(api_key=self.api_key)
        except Exception as e:
            raise RuntimeError(f"Failed to initialise Groq client: {e}")

    def generate(self, prompt: str, **kwargs) -> str:
        """
        Single-prompt completion via Groq.

        Wraps the prompt in a user message and calls the chat API.

        Args:
            prompt: The input text prompt.
            **kwargs: Extra params (temperature, max_tokens, top_p, etc.).

        Returns:
            The generated text response.
        """
        messages = [{"role": "user", "content": prompt}]
        return self.chat(messages, **kwargs)

    def chat(self, messages: list[dict], **kwargs) -> str:
        """
        Multi-turn chat completion via Groq.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
                      Example: [{"role": "user", "content": "Hello"}]
            **kwargs: Extra params (temperature, max_tokens, top_p, etc.).

        Returns:
            The assistant's reply text.
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                **kwargs,
            )
            return response.choices[0].message.content
        except Exception as e:
            error_type = type(e).__name__
            if "authentication" in str(e).lower() or "api_key" in str(e).lower():
                raise RuntimeError(
                    "Groq authentication failed. Check your GROQ_API_KEY in .env."
                ) from e
            if "rate_limit" in str(e).lower():
                raise RuntimeError(
                    "Groq rate limit hit. Wait a moment and try again."
                ) from e
            if "model" in str(e).lower() and "not found" in str(e).lower():
                raise RuntimeError(
                    f"Groq model '{self.model}' not found. "
                    "Check GROQ_MODEL in .env (try 'llama3-70b-8192')."
                ) from e
            raise RuntimeError(f"Groq API error ({error_type}): {e}") from e

    def health_check(self) -> bool:
        """
        Check if the Groq API is reachable and the key is valid.

        Sends a minimal request to verify connectivity.

        Returns:
            True if the API responds successfully, False otherwise.
        """
        try:
            self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=1,
            )
            return True
        except Exception:
            return False
