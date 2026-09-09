#!/usr/bin/env python3
"""Eenmalige Microsoft-login (device code) voor Outlook mail, agenda en To Do op het UT-account.

Stappen vooraf:
 1. https://entra.microsoft.com -> App registrations -> New registration
    - Supported account types: "Accounts in any organizational directory and personal Microsoft accounts"
    - Redirect URI: leeg laten; onder Authentication -> "Allow public client flows" = Yes
 2. API permissions -> Microsoft Graph -> Delegated: Mail.Read, Calendars.Read, Tasks.Read
 3. Zet de Application (client) ID in .env als MS_CLIENT_ID
 4. Draai: .venv/bin/python scripts/ms_auth.py  en log in met je UT-account

Krijg je "Need admin approval"? Dan blokkeert de UT-tenant user-consent. Fallback: OUTLOOK_ICS_URL
(Outlook Web -> Instellingen -> Agenda -> Gedeelde agenda's -> Agenda publiceren) en de eigen todolist.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings  # noqa: E402
from app.sources.outlook_graph import acquire_token  # noqa: E402


def main() -> None:
    if not settings.ms_client_id:
        sys.exit("MS_CLIENT_ID ontbreekt in .env (zie docstring)")
    acquire_token(settings.ms_client_id, settings.ms_token_file, interactive=True)
    print(f"Token opgeslagen in {settings.ms_token_file}. Herstart het dashboard.")


if __name__ == "__main__":
    main()
