"""Configuratie. Volgorde: instellingen uit de database (wizard) > .env > standaardwaarde.

Waar bestanden staan:
- ontwikkelen vanuit de repo: alles in de projectmap (data/ naast app/)
- ingepakte app (PyInstaller): code in de bundel, data in een per-gebruiker map (JARVIS_DATA_DIR)
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

FROZEN = getattr(sys, "frozen", False)
ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))


def default_data_dir() -> Path:
    if os.environ.get("JARVIS_DATA_DIR"):
        return Path(os.environ["JARVIS_DATA_DIR"])
    if not FROZEN:
        return ROOT / "data"
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / "Jarvis"


DATA_DIR = default_data_dir()
load_dotenv(ROOT / ".env")
load_dotenv(DATA_DIR / ".env")

# Sleutels die de wizard mag beheren (alles wat in .env.example staat behalve host/poort/db).
WIZARD_KEYS = [
    "UNIVERSITY", "TIMEEDIT_ICS_URL", "TIMEEDIT_WEB_URL", "GCAL_ICS_URL", "CANVAS_ICS_URL",
    "OUTLOOK_ICS_URL", "TRELLO_KEY", "TRELLO_TOKEN", "TRELLO_BOARD_ID", "CANVAS_BASE_URL",
    "CANVAS_TOKEN", "DASHBOARD_SECRET", "MS_CLIENT_ID", "SETUP_DONE",
]


@dataclass(frozen=True)
class Settings:
    tz_name: str
    host: str
    port: int
    secret: str
    db_path: Path
    data_dir: Path
    university: str
    timeedit_ics_url: str
    timeedit_web_url: str
    gcal_ics_url: str
    canvas_ics_url: str
    outlook_ics_url: str
    trello_key: str
    trello_token: str
    trello_board_id: str
    canvas_base_url: str
    canvas_token: str
    google_credentials_file: Path
    google_token_file: Path
    ms_client_id: str
    ms_token_file: Path
    setup_done: bool

    @property
    def tz(self) -> ZoneInfo:
        return ZoneInfo(self.tz_name)

    def any_source_configured(self) -> bool:
        return any([
            self.timeedit_ics_url, self.gcal_ics_url, self.canvas_ics_url, self.outlook_ics_url,
            self.trello_key and self.trello_token and self.trello_board_id, self.canvas_token,
            self.google_token_file.exists(), self.ms_client_id and self.ms_token_file.exists(),
        ])


def build_settings(overrides: dict[str, str] | None = None) -> Settings:
    ov = {k: v for k, v in (overrides or {}).items() if v is not None}

    def get(key: str, default: str = "") -> str:
        if key in ov:
            return str(ov[key]).strip()
        return os.environ.get(key, default).strip()

    def path(key: str, default: str) -> Path:
        p = Path(get(key, default))
        return p if p.is_absolute() else DATA_DIR / p.name if p.parts[0] == "data" else ROOT / p

    return Settings(
        tz_name=get("TZ", "Europe/Amsterdam") or "Europe/Amsterdam",
        host=get("DASHBOARD_HOST", "127.0.0.1"),
        port=int(get("DASHBOARD_PORT", "8000")),
        secret=get("DASHBOARD_SECRET"),
        db_path=Path(os.environ["DASHBOARD_DB"]) if os.environ.get("DASHBOARD_DB") else DATA_DIR / "dashboard.sqlite3",
        data_dir=DATA_DIR,
        university=get("UNIVERSITY", "utwente"),
        timeedit_ics_url=get("TIMEEDIT_ICS_URL"),
        timeedit_web_url=get("TIMEEDIT_WEB_URL", "https://cloud.timeedit.net/nl_utwente/web/"),
        gcal_ics_url=get("GCAL_ICS_URL"),
        canvas_ics_url=get("CANVAS_ICS_URL"),
        outlook_ics_url=get("OUTLOOK_ICS_URL"),
        trello_key=get("TRELLO_KEY"),
        trello_token=get("TRELLO_TOKEN"),
        trello_board_id=get("TRELLO_BOARD_ID"),
        canvas_base_url=get("CANVAS_BASE_URL", "https://canvas.utwente.nl").rstrip("/"),
        canvas_token=get("CANVAS_TOKEN"),
        google_credentials_file=path("GOOGLE_CREDENTIALS_FILE", "data/google_credentials.json"),
        google_token_file=path("GOOGLE_TOKEN_FILE", "data/google_token.json"),
        ms_client_id=get("MS_CLIENT_ID"),
        ms_token_file=path("MS_TOKEN_FILE", "data/ms_token.json"),
        setup_done=get("SETUP_DONE", "").lower() in ("1", "true", "yes"),
    )


# Standaardinstantie zonder database-overrides; main.py vervangt deze na het lezen van de database.
settings = build_settings()
