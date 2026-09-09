"""Configuratie uit .env. Lege waarde betekent: bron uitgeschakeld."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default).strip()


@dataclass(frozen=True)
class Settings:
    tz_name: str = field(default_factory=lambda: _env("TZ", "Europe/Amsterdam"))
    host: str = field(default_factory=lambda: _env("DASHBOARD_HOST", "127.0.0.1"))
    port: int = field(default_factory=lambda: int(_env("DASHBOARD_PORT", "8000")))
    secret: str = field(default_factory=lambda: _env("DASHBOARD_SECRET"))
    db_path: Path = field(default_factory=lambda: ROOT / _env("DASHBOARD_DB", "data/dashboard.sqlite3"))

    timeedit_ics_url: str = field(default_factory=lambda: _env("TIMEEDIT_ICS_URL"))
    timeedit_web_url: str = field(
        default_factory=lambda: _env("TIMEEDIT_WEB_URL", "https://cloud.timeedit.net/nl_utwente/web/")
    )
    gcal_ics_url: str = field(default_factory=lambda: _env("GCAL_ICS_URL"))
    canvas_ics_url: str = field(default_factory=lambda: _env("CANVAS_ICS_URL"))
    outlook_ics_url: str = field(default_factory=lambda: _env("OUTLOOK_ICS_URL"))

    trello_key: str = field(default_factory=lambda: _env("TRELLO_KEY"))
    trello_token: str = field(default_factory=lambda: _env("TRELLO_TOKEN"))
    trello_board_id: str = field(default_factory=lambda: _env("TRELLO_BOARD_ID"))

    canvas_base_url: str = field(
        default_factory=lambda: _env("CANVAS_BASE_URL", "https://canvas.utwente.nl").rstrip("/")
    )
    canvas_token: str = field(default_factory=lambda: _env("CANVAS_TOKEN"))

    google_credentials_file: Path = field(
        default_factory=lambda: ROOT / _env("GOOGLE_CREDENTIALS_FILE", "data/google_credentials.json")
    )
    google_token_file: Path = field(
        default_factory=lambda: ROOT / _env("GOOGLE_TOKEN_FILE", "data/google_token.json")
    )

    ms_client_id: str = field(default_factory=lambda: _env("MS_CLIENT_ID"))
    ms_token_file: Path = field(default_factory=lambda: ROOT / _env("MS_TOKEN_FILE", "data/ms_token.json"))

    @property
    def tz(self) -> ZoneInfo:
        return ZoneInfo(self.tz_name)


settings = Settings()
