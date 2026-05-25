"""
gmail_reader_tool.py — Real Gmail API integration.

Uses Google OAuth (via tools/auth.py) to fetch real emails.

Functions:
    get_latest_emails(max_results)  → list of real emails
    get_today_emails()              → today's emails only
    summarize_emails(emails)        → LLM summary of email list
"""

from datetime import datetime

from tools.auth import get_gmail_service
from models.llm_router import LLMRouter


def _extract_header(headers: list, name: str) -> str:
    """Extract a header value by name from Gmail message headers."""
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


def get_latest_emails(max_results: int = 10) -> list[dict]:
    """
    Fetch the most recent emails from the user's real Gmail inbox.

    Args:
        max_results: Maximum number of emails to return.

    Returns:
        List of dicts with keys: subject, snippet, from, date
    """
    try:
        service = get_gmail_service()
        results = service.users().messages().list(
            userId="me", maxResults=max_results, labelIds=["INBOX"]
        ).execute()

        messages = results.get("messages", [])
        if not messages:
            return []

        emails = []
        for msg_ref in messages:
            msg = service.users().messages().get(
                userId="me", id=msg_ref["id"], format="metadata",
                metadataHeaders=["Subject", "From", "Date"]
            ).execute()

            headers = msg.get("payload", {}).get("headers", [])
            emails.append({
                "subject": _extract_header(headers, "Subject") or "(No Subject)",
                "snippet": msg.get("snippet", ""),
                "from": _extract_header(headers, "From"),
                "date": _extract_header(headers, "Date"),
            })

        return emails

    except Exception as e:
        return [{"subject": f"Error fetching emails: {e}", "snippet": "", "from": "", "date": ""}]


def get_today_emails(max_results: int = 20) -> list[dict]:
    """
    Fetch only today's emails using Gmail search query.

    Returns:
        List of email dicts from today.
    """
    try:
        service = get_gmail_service()
        results = service.users().messages().list(
            userId="me", maxResults=max_results,
            labelIds=["INBOX"], q="newer_than:1d"
        ).execute()

        messages = results.get("messages", [])
        if not messages:
            return []

        emails = []
        for msg_ref in messages:
            msg = service.users().messages().get(
                userId="me", id=msg_ref["id"], format="metadata",
                metadataHeaders=["Subject", "From", "Date"]
            ).execute()

            headers = msg.get("payload", {}).get("headers", [])
            emails.append({
                "subject": _extract_header(headers, "Subject") or "(No Subject)",
                "snippet": msg.get("snippet", ""),
                "from": _extract_header(headers, "From"),
                "date": _extract_header(headers, "Date"),
            })

        return emails

    except Exception as e:
        return [{"subject": f"Error fetching today's emails: {e}", "snippet": "", "from": "", "date": ""}]


def summarize_emails(emails: list[dict] | None = None) -> str:
    """
    Summarize a list of emails using the LLM.

    Args:
        emails: List of email dicts. If None, uses today's emails.

    Returns:
        A natural-language summary of the emails.
    """
    if emails is None:
        emails = get_today_emails()

    if not emails:
        return "You have no emails to summarize."

    # Build a text block from the emails
    lines = []
    for i, email in enumerate(emails, 1):
        lines.append(
            f"{i}. From: {email['from']}\n"
            f"   Subject: {email['subject']}\n"
            f"   Snippet: {email['snippet']}\n"
            f"   Date: {email['date']}"
        )
    email_text = "\n\n".join(lines)

    prompt = (
        "You are a personal assistant. Summarize these emails briefly, "
        "highlighting anything urgent or important.\n\n"
        f"Emails:\n{email_text}\n\n"
        "Summary:"
    )

    try:
        router = LLMRouter()
        return router.generate(prompt, task_type="general")
    except Exception as e:
        return f"Could not summarize emails: {e}"


def send_email(to: str, subject: str, body: str) -> str:
    import base64
    from email.mime.text import MIMEText
    from tools.auth import get_gmail_service
    
    service = get_gmail_service()
    
    message = MIMEText(body)
    message['to'] = to
    message['subject'] = subject
    
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    
    try:
        service.users().messages().send(
            userId='me',
            body={'raw': raw}
        ).execute()
        return f"✅ Email sent to {to} with subject '{subject}'"
    except Exception as e:
        return f"❌ Failed to send email: {str(e)}"

def draft_email(to: str, subject: str, body: str) -> str:
    """Shows draft to user before sending — safety check"""
    return f"""
📝 Email Draft Ready:
To: {to}
Subject: {subject}
Body: {body}

Reply 'confirm send' to send this email.
"""
