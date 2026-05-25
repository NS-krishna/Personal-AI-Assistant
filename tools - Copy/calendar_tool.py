"""
calendar_tool.py — Real Google Calendar API integration.

Uses Google OAuth (via tools/auth.py) to manage real calendar events.

Functions:
    get_today_events()                → today's real events
    list_events(date=None)            → events for a date or next 7 days
    create_event(user_query, ...)     → LLM extracts details, creates real event
"""

import json
import re
from datetime import datetime, timedelta, timezone

from tools.auth import get_calendar_service
from models.llm_router import LLMRouter


# ── Read helpers ─────────────────────────────────────────────────────────

def _parse_event(event: dict) -> dict:
    """Convert a Google Calendar API event into a clean dict."""
    start_raw = event.get("start", {})
    end_raw = event.get("end", {})

    # Events can have dateTime (timed) or date (all-day)
    start = start_raw.get("dateTime", start_raw.get("date", ""))
    end = end_raw.get("dateTime", end_raw.get("date", ""))

    return {
        "title": event.get("summary", "(No Title)"),
        "start": start,
        "end": end,
        "location": event.get("location", ""),
    }


def get_today_events() -> list[dict]:
    """Fetch today's events from Google Calendar."""
    try:
        service = get_calendar_service()

        now = datetime.now()
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        # Format to RFC3339
        time_min = start_of_day.isoformat() + "Z"
        time_max = end_of_day.isoformat() + "Z"

        result = service.events().list(
            calendarId="primary",
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime",
        ).execute()

        events = result.get("items", [])
        return [_parse_event(e) for e in events]

    except Exception as e:
        return [{"title": f"Error fetching today's events: {e}", "start": "", "end": "", "location": ""}]


def list_events(date: str = None, max_results: int = 10) -> list[dict]:
    """
    List calendar events.

    Args:
        date: ISO date (YYYY-MM-DD) to filter. If None, returns next 7 days.
        max_results: Max events to return.
    """
    try:
        service = get_calendar_service()

        if date:
            day = datetime.fromisoformat(date)
            time_min = day.replace(hour=0, minute=0, second=0).isoformat() + "Z"
            time_max = (day + timedelta(days=1)).isoformat() + "Z"
        else:
            time_min = datetime.utcnow().isoformat() + "Z"
            time_max = (datetime.utcnow() + timedelta(days=7)).isoformat() + "Z"

        result = service.events().list(
            calendarId="primary",
            timeMin=time_min,
            timeMax=time_max,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
        ).execute()

        events = result.get("items", [])
        return [_parse_event(e) for e in events]

    except Exception as e:
        return [{"title": f"Error fetching events: {e}", "start": "", "end": "", "location": ""}]


# ── Create event ─────────────────────────────────────────────────────────

_EXTRACT_PROMPT = """You are a calendar event extractor. Today's date is {today}.

Extract event details from the user's message and return ONLY a JSON object.

Rules:
- "tomorrow" means {tomorrow}
- Use 24-hour format for times
- If no end time, assume 1 hour after start
- If no location mentioned, use empty string

Return format (JSON only, no markdown):
{{"title": "Event Title", "start": "YYYY-MM-DDTHH:MM:SS", "end": "YYYY-MM-DDTHH:MM:SS", "location": ""}}

User message: {message}

JSON:"""


def create_event(user_query: str = "", summary: str = "", start: str = "", end: str = "", attendees: list = []):
    """
    Create a real Google Calendar event.

    If summary/start not provided, uses LLM to extract from user_query.
    Then calls the Calendar API to insert the event.
    """
    # If details not provided, extract from natural language
    if not summary or not start:
        llm = LLMRouter()
        today = datetime.now().strftime("%Y-%m-%d")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        prompt = _EXTRACT_PROMPT.format(
            today=today, tomorrow=tomorrow, message=user_query
        )
        response = llm.generate(prompt, task_type="general")

        try:
            # Clean response and parse JSON
            clean = response.strip()
            if "```" in clean:
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
            details = json.loads(clean.strip())

            title = details.get("title", "New Event")
            start = details.get("start", "")
            end = details.get("end", "")
            location = details.get("location", "")
        except Exception:
            return "❌ Could not understand the event details. Try: 'Schedule meeting with Rahul on March 10th from 3pm to 4pm'"
    else:
        title = summary
        location = ""

    # Build Google Calendar event body
    event_body = {
        "summary": title,
        "start": {
            "dateTime": start,
            "timeZone": "Asia/Kolkata",
        },
        "end": {
            "dateTime": end,
            "timeZone": "Asia/Kolkata",
        },
    }
    if location:
        event_body["location"] = location

    # Insert via Calendar API
    try:
        service = get_calendar_service()
        created = service.events().insert(
            calendarId="primary", body=event_body
        ).execute()

        event_link = created.get("htmlLink", "")

        # Format confirmation
        try:
            start_dt = datetime.fromisoformat(start)
            end_dt = datetime.fromisoformat(end)
            formatted_start = start_dt.strftime("%B %d, %Y at %I:%M %p")
            formatted_end = end_dt.strftime("%I:%M %p")
        except Exception:
            formatted_start = start
            formatted_end = end

        msg = f"✅ Event created: '{title}' on {formatted_start} - {formatted_end}"
        if location:
            msg += f" at {location}"
        if event_link:
            msg += f"\n🔗 {event_link}"
        return msg

    except Exception as e:
        # Fallback: return confirmation without API (mock)
        try:
            start_dt = datetime.fromisoformat(start)
            end_dt = datetime.fromisoformat(end)
            formatted_start = start_dt.strftime("%B %d, %Y at %I:%M %p")
            formatted_end = end_dt.strftime("%I:%M %p")
        except Exception:
            formatted_start = start
            formatted_end = end

        return f"⚠️ Event parsed but Calendar API failed: '{title}' on {formatted_start} - {formatted_end}\nError: {e}"
