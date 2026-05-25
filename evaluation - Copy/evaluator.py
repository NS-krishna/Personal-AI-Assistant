"""
evaluator.py -- Evaluation and analytics dashboard data.

Tracks agent performance metrics via JSON file persistence:
    - Response quality scores (from CriticAgent)
    - Tool usage frequency
    - Response latency (per request)
    - Retry rates

All interactions are logged to ./evaluation/logs.json so stats
survive server restarts.
"""

import json
import os
from collections import defaultdict
from datetime import datetime

LOGS_PATH = os.path.join(os.path.dirname(__file__), "logs.json")


def _read_logs() -> list[dict]:
    """Read all interaction logs from disk."""
    if not os.path.exists(LOGS_PATH):
        return []
    try:
        with open(LOGS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def _write_logs(logs: list[dict]) -> None:
    """Write interaction logs to disk."""
    with open(LOGS_PATH, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)


def log_interaction(
    tool_used: str,
    score: int,
    needs_retry: bool,
    response_time_ms: float,
) -> None:
    """
    Log a single interaction to logs.json.

    Args:
        tool_used: Name of the primary tool invoked (e.g. "gmail_reader").
        score: Quality score from CriticAgent (1-10).
        needs_retry: Whether the response triggered a retry.
        response_time_ms: Total response time in milliseconds.
    """
    logs = _read_logs()
    logs.append({
        "timestamp": datetime.now().isoformat(),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "tool_used": tool_used,
        "score": score,
        "needs_retry": needs_retry,
        "response_time_ms": round(response_time_ms, 1),
    })
    _write_logs(logs)


def get_stats() -> dict:
    """
    Compute aggregate statistics from all logged interactions.

    Returns:
        Dict with: total_conversations, average_score, total_retries,
                   avg_response_time_ms, tool_usage, scores_over_time.
    """
    logs = _read_logs()

    if not logs:
        return {
            "total_conversations": 0,
            "average_score": 0,
            "total_retries": 0,
            "avg_response_time_ms": 0,
            "tool_usage": {},
            "scores_over_time": [],
        }

    total = len(logs)
    total_score = sum(entry.get("score", 0) for entry in logs)
    total_retries = sum(1 for entry in logs if entry.get("needs_retry", False))
    total_time = sum(entry.get("response_time_ms", 0) for entry in logs)

    # Tool usage counts
    tool_counts: dict[str, int] = defaultdict(int)
    for entry in logs:
        tool = entry.get("tool_used", "chat")
        tool_counts[tool] += 1

    # Scores grouped by date
    date_scores: dict[str, list[int]] = defaultdict(list)
    for entry in logs:
        date = entry.get("date", "unknown")
        date_scores[date].append(entry.get("score", 0))

    scores_over_time = [
        {
            "date": date,
            "avg_score": round(sum(scores) / len(scores), 1),
        }
        for date, scores in sorted(date_scores.items())
    ]

    return {
        "total_conversations": total,
        "average_score": round(total_score / total, 1),
        "total_retries": total_retries,
        "avg_response_time_ms": round(total_time / total, 0),
        "tool_usage": dict(tool_counts),
        "scores_over_time": scores_over_time,
    }
