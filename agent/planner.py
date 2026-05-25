"""
planner.py — Planner agent: breaks user queries into tool steps.

Sends the user query + available tool list to the LLM.
The LLM returns a JSON plan of steps to execute.
Falls back to a simple chat step if JSON parsing fails.
"""

import json
import re

from models.llm_router import LLMRouter


SYSTEM_PROMPT = """You are a planning agent for a personal AI assistant.
Your job is to break the user's query into a list of tool steps.

Available tools:
1. "gmail_reader" — Read and search the user's emails.
   Actions: get_latest_emails, get_today_emails, summarize_emails
2. "calendar" — Manage the user's calendar events.
   Actions: get_today_events, list_events, create_event
3. "summarizer" — Summarize generic text or documents (NOT emails).
   Actions: summarize
4. "chat" — Direct conversation (no tool needed).
   Actions: respond
5. "web_search" — Search the web for information.
   Actions: search

RULES:
- Return ONLY a valid JSON array, no markdown, no explanation.
- Each element must have: "tool", "action", "arguments", "reason".
- Use "chat" tool if the query is just casual conversation.
- For email queries, use "gmail_reader".
- For calendar/meeting/schedule queries, use "calendar".
- For summarization requests, use "summarizer".

Example output:
[{"tool": "gmail_reader", "action": "get_today_emails", "arguments": {}, "reason": "user wants today's emails"}]
"""


class PlannerAgent:
    """Breaks a user query into an ordered list of tool invocations."""

    def __init__(self):
        self.router = LLMRouter()

    def plan(self, user_query: str) -> list[dict]:
        """
        Generate an execution plan from a user query.

        Args:
            user_query: The raw user input.

        Returns:
            List of step dicts: [{tool, action, arguments, reason}, ...]
        """
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_query},
        ]

        try:
            raw = self.router.chat(messages, task_type="general")
            plan = self._parse_plan(raw)
            if plan:
                return plan
        except Exception:
            pass

        # Fallback: treat as a direct chat query
        return [
            {
                "tool": "chat",
                "action": "respond",
                "arguments": {"query": user_query},
                "reason": "Fallback — could not parse a structured plan",
            }
        ]

    def _parse_plan(self, llm_output: str) -> list[dict] | None:
        """
        Parse the LLM's output into a validated plan.

        Tries direct JSON parsing first, then extracts JSON from
        markdown code blocks if present.

        Returns:
            Parsed plan list, or None if parsing fails.
        """
        text = llm_output.strip()

        # Try direct JSON parse
        try:
            result = json.loads(text)
            if isinstance(result, list) and len(result) > 0:
                return self._validate_plan(result)
        except json.JSONDecodeError:
            pass

        # Try extracting JSON from markdown code blocks
        match = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", text, re.DOTALL)
        if match:
            try:
                result = json.loads(match.group(1))
                if isinstance(result, list) and len(result) > 0:
                    return self._validate_plan(result)
            except json.JSONDecodeError:
                pass

        # Try finding any JSON array in the text
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if match:
            try:
                result = json.loads(match.group(0))
                if isinstance(result, list) and len(result) > 0:
                    return self._validate_plan(result)
            except json.JSONDecodeError:
                pass

        return None

    def _validate_plan(self, plan: list) -> list[dict]:
        """Ensure each step has the required keys, filling defaults."""
        validated = []
        for step in plan:
            if not isinstance(step, dict):
                continue
            validated.append({
                "tool": step.get("tool", "chat"),
                "action": step.get("action", "respond"),
                "arguments": step.get("arguments", {}),
                "reason": step.get("reason", ""),
            })
        return validated if validated else None
