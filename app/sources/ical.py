"""Generieke iCal-bron: TimeEdit, Google Calendar (privé-ICS), Canvas-agenda, Outlook-publish."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx
import recurring_ical_events
from icalendar import Calendar

from ..models import Item, Kind


def _to_local(value, tz: ZoneInfo) -> tuple[datetime, bool]:
    """Geeft (lokale datetime, all_day)."""
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=tz), False
        return value.astimezone(tz), False
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day, tzinfo=tz), True
    raise TypeError(f"onbekend datumtype: {value!r}")


def _text(component, key: str) -> str | None:
    v = component.get(key)
    return str(v).strip() if v is not None and str(v).strip() else None


def parse_ical(
    text: str | bytes,
    *,
    source: str,
    kind: Kind,
    tz: ZoneInfo,
    window_start: datetime,
    window_end: datetime,
    link_url: str | None = None,
) -> list[Item]:
    cal = Calendar.from_ical(text)
    items: list[Item] = []
    for ev in recurring_ical_events.of(cal).between(window_start, window_end):
        dtstart = ev.get("DTSTART")
        if dtstart is None:
            continue
        start, all_day = _to_local(dtstart.dt, tz)
        end = None
        if ev.get("DTEND") is not None:
            end, _ = _to_local(ev.get("DTEND").dt, tz)
            if all_day:
                end = end - timedelta(seconds=1)  # DTEND is exclusief bij hele dagen
        uid = _text(ev, "UID") or f"{_text(ev, 'SUMMARY')}@{start.isoformat()}"
        title = _text(ev, "SUMMARY") or "(geen titel)"
        url = _text(ev, "URL") or link_url

        # Canvas zet opdrachten en agenda-items in één feed; alleen opdrachten zijn deadlines.
        item_kind: Kind = kind
        if kind == "deadline" and "assignment" not in uid.lower() and end is not None and end != start:
            item_kind = "event"

        items.append(
            Item(
                source=source,
                external_id=f"{uid}@{start.isoformat()}",
                kind=item_kind,
                title=title,
                start=start,
                end=end,
                due=(end if (all_day and end) else start) if item_kind == "deadline" else None,
                url=url,
                subtitle=_text(ev, "LOCATION"),
                all_day=all_day,
                meta={"description": (_text(ev, "DESCRIPTION") or "")[:500]},
            )
        )
    return items


class ICalSource:
    def __init__(
        self, *, name: str, label: str, url: str, kind: Kind, tz: ZoneInfo,
        link_url: str | None = None, interval: int = 900,
        days_back: int | None = None, days_ahead: int | None = None,
    ):
        self.name = name
        self.label = label
        self.url = url
        self.kind = kind
        self.tz = tz
        self.link_url = link_url
        self.interval = interval
        self.days_back = days_back if days_back is not None else (14 if kind == "deadline" else 1)
        self.days_ahead = days_ahead if days_ahead is not None else (60 if kind == "deadline" else 30)

    def configured(self) -> bool:
        return bool(self.url)

    def _download(self) -> bytes:
        url = self.url
        if url.startswith("webcal://"):
            url = "https://" + url[len("webcal://"):]
        if url.startswith("file://"):
            return Path(url[len("file://"):]).read_bytes()
        r = httpx.get(url, follow_redirects=True, timeout=30, headers={"User-Agent": "home-dashboard/0.1"})
        r.raise_for_status()
        return r.content

    def fetch(self) -> list[Item]:
        now = datetime.now(self.tz)
        return parse_ical(
            self._download(),
            source=self.name, kind=self.kind, tz=self.tz,
            window_start=now - timedelta(days=self.days_back),
            window_end=now + timedelta(days=self.days_ahead),
            link_url=self.link_url,
        )
