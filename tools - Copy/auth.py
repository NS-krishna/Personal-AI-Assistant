"""
auth.py — Google OAuth 2.0 authentication.

Handles:
    - First-run OAuth flow via credentials.json → opens browser
    - Caches token in token.json for subsequent runs
    - Auto-refreshes expired tokens
    - Provides authenticated service builders for Gmail & Calendar

Scopes:
    - gmail.readonly, gmail.send, calendar
"""

import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Google API scopes required by this application
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar",
]

# Paths — relative to project root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_CREDENTIALS_FILE = _PROJECT_ROOT / "credentials.json"
_TOKEN_FILE = _PROJECT_ROOT / "token.json"


def get_google_credentials():
    """
    Load or generate Google OAuth credentials.

    Flow:
        1. If token.json exists and is valid → load it
        2. If token.json is expired → refresh it
        3. Otherwise → run InstalledAppFlow from credentials.json
           (opens browser for Google login)

    Returns:
        google.oauth2.credentials.Credentials
    """
    creds = None

    # 1. Try loading existing token
    if _TOKEN_FILE.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(_TOKEN_FILE), SCOPES)
        except Exception:
            creds = None

    # 2. Refresh or re-auth
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                # Token refresh failed — re-run full flow
                creds = None

        if not creds:
            if not _CREDENTIALS_FILE.exists():
                raise FileNotFoundError(
                    f"credentials.json not found at {_CREDENTIALS_FILE}. "
                    "Download it from Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                str(_CREDENTIALS_FILE), SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save for next run
        with open(_TOKEN_FILE, "w") as f:
            f.write(creds.to_json())

    return creds


def get_gmail_service():
    """Build and return an authenticated Gmail API service."""
    creds = get_google_credentials()
    return build("gmail", "v1", credentials=creds)


def get_calendar_service():
    """Build and return an authenticated Calendar API service."""
    creds = get_google_credentials()
    return build("calendar", "v3", credentials=creds)
