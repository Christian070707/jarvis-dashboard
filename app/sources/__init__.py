"""Bronnenregister. Alleen geconfigureerde bronnen worden actief."""
from __future__ import annotations

from ..config import Settings
from .base import Source
from .canvas import CanvasSource
from .gcal import GoogleCalendarSource
from .gmail import GmailSource
from .ical import ICalSource
from .outlook_graph import OutlookGraphSource
from .trello import TrelloSource


def build_sources(s: Settings) -> list[Source]:
    candidates: list[Source] = [
        ICalSource(
            name="timeedit", label="TimeEdit", url=s.timeedit_ics_url, kind="event",
            link_url=s.timeedit_web_url, tz=s.tz, interval=15 * 60,
        ),
        ICalSource(
            name="gcal_ics", label="Google Calendar", url=s.gcal_ics_url, kind="event",
            link_url="https://calendar.google.com/", tz=s.tz, interval=15 * 60,
        ),
        ICalSource(
            name="canvas_ics", label="Canvas (agenda)", url=s.canvas_ics_url, kind="deadline",
            link_url=f"{s.canvas_base_url}/calendar", tz=s.tz, interval=15 * 60,
        ),
        ICalSource(
            name="outlook_ics", label="Outlook (agenda)", url=s.outlook_ics_url, kind="event",
            link_url="https://outlook.office.com/calendar/", tz=s.tz, interval=15 * 60,
        ),
        TrelloSource(key=s.trello_key, token=s.trello_token, board_id=s.trello_board_id, tz=s.tz),
        CanvasSource(base_url=s.canvas_base_url, token=s.canvas_token, tz=s.tz),
        GmailSource(token_file=s.google_token_file, tz=s.tz),
        GoogleCalendarSource(token_file=s.google_token_file, tz=s.tz),
        OutlookGraphSource(client_id=s.ms_client_id, token_file=s.ms_token_file, tz=s.tz),
    ]
    active = [c for c in candidates if c.configured()]
    # Als de API-variant van Canvas/Google Calendar actief is, de ICS-variant weglaten (dubbele items).
    names = {c.name for c in active}
    if "canvas" in names:
        active = [c for c in active if c.name != "canvas_ics"]
    if "gcal" in names:
        active = [c for c in active if c.name != "gcal_ics"]
    return active
