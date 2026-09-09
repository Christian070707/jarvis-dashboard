#!/usr/bin/env python3
"""Eenmalige Google OAuth-flow voor Gmail + Calendar.

Stappen vooraf (5 min):
 1. https://console.cloud.google.com -> nieuw project -> APIs & Services -> Enable: Gmail API, Google Calendar API
 2. OAuth consent screen: External, Testing, voeg je eigen Gmail-adres toe als test user
 3. Credentials -> Create OAuth client ID -> Desktop app -> download JSON -> sla op als data/google_credentials.json
 4. Draai: .venv/bin/python scripts/google_auth.py   (opent browser, schrijft data/google_token.json)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings  # noqa: E402
from app.sources._google import SCOPES  # noqa: E402


def main() -> None:
    from google_auth_oauthlib.flow import InstalledAppFlow

    if not settings.google_credentials_file.exists():
        sys.exit(f"Ontbreekt: {settings.google_credentials_file} (zie docstring)")
    flow = InstalledAppFlow.from_client_secrets_file(str(settings.google_credentials_file), SCOPES)
    creds = flow.run_local_server(port=0, prompt="consent")
    settings.google_token_file.parent.mkdir(parents=True, exist_ok=True)
    settings.google_token_file.write_text(creds.to_json())
    print(f"Token opgeslagen in {settings.google_token_file}. Herstart het dashboard.")


if __name__ == "__main__":
    main()
