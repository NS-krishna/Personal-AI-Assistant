"""
critic.py — Critic agent: reviews answer quality and triggers retries.

Self-evaluation loop:
    1. Receives the user query + agent response
    2. Asks the LLM to score the response quality (1–10)
    3. If score < 6 → needs_retry = True
    4. If score ≥ 6 → approved
"""

import json
import re

from models.llm_router import LLMRouter


EVAL_PROMPT = """You are a quality evaluator for an AI personal assistant.

The user asked a question and the assistant produced a response.
Rate the response on a scale of 1-10 based on:
- Relevance: Does it answer the user's question?
- Completeness: Is the answer thorough enough?
- Clarity: Is it well-written and easy to understand?

Return ONLY a JSON object with these keys:
- "score": integer 1-10
- "feedback": one-line explanation

Example: {{"score": 8, "feedback": "Clear and relevant response"}}

User question: {query}

Assistant response: {response}

Your evaluation (JSON only):"""


class CriticAgent:
    """Evaluates response quality and triggers retries if needed."""

    QUALITY_THRESHOLD = 6

    def __init__(self):
        self.router = LLMRouter()

    def evaluate(self, user_query: str, response: str) -> dict:
        """
        Evaluate the quality of a generated response.

        Args:
            user_query: Original user input.
            response: The proposed response to the user.

        Returns:
            Dict with: score (int), feedback (str), needs_retry (bool)
        """
        prompt = EVAL_PROMPT.format(query=user_query, response=response)

        try:
            raw = self.router.generate(prompt, task_type="general")
            evaluation = self._parse_evaluation(raw)
        except Exception:
            # If the critic itself fails, approve by default
            evaluation = {
                "score": 7,
                "feedback": "Evaluation skipped — critic LLM call failed",
            }

        evaluation["needs_retry"] = evaluation["score"] < self.QUALITY_THRESHOLD
        return evaluation

    def _parse_evaluation(self, llm_output: str) -> dict:
        """
        Parse the LLM's evaluation output into a dict.

        Tries direct JSON parsing, then regex extraction.

        Returns:
            Dict with score and feedback.
        """
        text = llm_output.strip()

        # Try direct JSON parse
        try:
            result = json.loads(text)
            if isinstance(result, dict) and "score" in result:
                return {
                    "score": int(result["score"]),
                    "feedback": str(result.get("feedback", "")),
                }
        except (json.JSONDecodeError, ValueError):
            pass

        # Try extracting JSON from markdown code blocks
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if match:
            try:
                result = json.loads(match.group(1))
                return {
                    "score": int(result.get("score", 5)),
                    "feedback": str(result.get("feedback", "")),
                }
            except (json.JSONDecodeError, ValueError):
                pass

        # Try finding any JSON object in the text
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                result = json.loads(match.group(0))
                return {
                    "score": int(result.get("score", 5)),
                    "feedback": str(result.get("feedback", "")),
                }
            except (json.JSONDecodeError, ValueError):
                pass

        # Try extracting just a number as score
        match = re.search(r"\b(\d{1,2})\b", text)
        if match:
            score = min(int(match.group(1)), 10)
            return {"score": score, "feedback": text[:100]}

        # Default: assume it's okay
        return {"score": 7, "feedback": "Could not parse evaluation output"}
