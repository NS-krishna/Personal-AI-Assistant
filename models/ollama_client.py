"""
ollama_client.py — Local LLM wrapper using Ollama (qwen2.5-coder).

Communicates with the Ollama REST API at http://localhost:11434.
Uses the `requests` library — no external ollama package required.

Methods:
    generate(prompt)   → single-prompt completion
    chat(messages)     → multi-turn conversation
    stream(prompt)     → token-by-token streaming generator
    health_check()     → True if Ollama server is reachable
"""

import json
import requests
from typing import Generator

from config import settings


class OllamaClient:
    """Wrapper around the local Ollama REST API."""

    def __init__(self, model: str = None, base_url: str = None):
        self.model = model or settings.OLLAMA_MODEL
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")

    def generate(self, prompt: str, **kwargs) -> str:
        """
        Single-prompt completion.

        Args:
            prompt: The input text prompt.
            **kwargs: Extra parameters forwarded to the Ollama API
                      (e.g. temperature, top_p, num_predict).

        Returns:
            The full generated text response.

        Raises:
            ConnectionError: If the Ollama server is unreachable.
            RuntimeError: If the API returns a non-200 status.
        """
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                **kwargs,
            }
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=120,
            )
            response.raise_for_status()
            return response.json()["response"]
        except requests.ConnectionError:
            raise ConnectionError(
                f"Cannot connect to Ollama at {self.base_url}. "
                "Make sure Ollama is running (ollama serve)."
            )
        except requests.Timeout:
            raise RuntimeError(
                "Ollama request timed out. The model may be loading — try again."
            )
        except requests.HTTPError as e:
            raise RuntimeError(f"Ollama API error: {e.response.status_code} — {e.response.text}")
        except KeyError:
            raise RuntimeError(
                "Unexpected response format from Ollama. "
                f"Raw response: {response.text[:500]}"
            )

    def chat(self, messages: list[dict], **kwargs) -> str:
        """
        Multi-turn chat completion.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
                      Example: [{"role": "user", "content": "Hello"}]
            **kwargs: Extra parameters forwarded to the Ollama API.

        Returns:
            The assistant's reply text.

        Raises:
            ConnectionError: If the Ollama server is unreachable.
            RuntimeError: If the API returns a non-200 status.
        """
        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                **kwargs,
            }
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=120,
            )
            response.raise_for_status()
            return response.json()["message"]["content"]
        except requests.ConnectionError:
            raise ConnectionError(
                f"Cannot connect to Ollama at {self.base_url}. "
                "Make sure Ollama is running (ollama serve)."
            )
        except requests.Timeout:
            raise RuntimeError(
                "Ollama chat request timed out. The model may be loading — try again."
            )
        except requests.HTTPError as e:
            raise RuntimeError(f"Ollama API error: {e.response.status_code} — {e.response.text}")
        except KeyError:
            raise RuntimeError(
                "Unexpected response format from Ollama chat. "
                f"Raw response: {response.text[:500]}"
            )

    def stream(self, prompt: str, **kwargs) -> Generator[str, None, None]:
        """
        Streaming completion — yields tokens one at a time.

        Args:
            prompt: The input text prompt.
            **kwargs: Extra parameters forwarded to the Ollama API.

        Yields:
            Individual token strings as they arrive.

        Raises:
            ConnectionError: If the Ollama server is unreachable.
            RuntimeError: If the API returns a non-200 status.
        """
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": True,
                **kwargs,
            }
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                stream=True,
                timeout=120,
            )
            response.raise_for_status()

            for line in response.iter_lines(decode_unicode=True):
                if line:
                    chunk = json.loads(line)
                    token = chunk.get("response", "")
                    if token:
                        yield token
                    if chunk.get("done", False):
                        break

        except requests.ConnectionError:
            raise ConnectionError(
                f"Cannot connect to Ollama at {self.base_url}. "
                "Make sure Ollama is running (ollama serve)."
            )
        except requests.Timeout:
            raise RuntimeError(
                "Ollama streaming request timed out."
            )
        except requests.HTTPError as e:
            raise RuntimeError(f"Ollama API error: {e.response.status_code} — {e.response.text}")

    def health_check(self) -> bool:
        """
        Check if the Ollama server is reachable.

        Returns:
            True if the server responds, False otherwise.
        """
        try:
            response = requests.get(self.base_url, timeout=5)
            return response.status_code == 200
        except (requests.ConnectionError, requests.Timeout):
            return False