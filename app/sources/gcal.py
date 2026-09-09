"""Google Calendar API: alle geselecteerde agenda's, met htmlLink per event."""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from ..models import Item
from ._google import load_credentials


class GoogleCalendarSource:
    name = "gcal"
    label = "Google Calendar"
    interval = 5 * 60

    def __init__(self, *, token_file: Path, tz: ZoneInfo):
        self.token_file, self.tz = token_file, tz

    def configured(self) -> bool:
        return self.token_file.exists()

    def fetch(self) -> list[Item]:
        from googleapiclient.discovery import build

        service = build("calendar", "v3", credentials=load_credentials(self.token_file), cache_discovery=False)
        now = datetime.now(self.tz)
        time_min = (now - timedelta(days=1)).isoformat()
        time_max = (now + timedelta(days=30)).isoformat()
        calendars = service.calendarList().list().execute().get("items", [])
        items: list[Item] = []
        for cal in calendars:
            if cal.get("selected") is False:
                continue
            events = service.events().list(
                calendarId=cal["id"], timeMin=time_min, timeMax=time_max,
                singleEvents=True, orderBy="startTime", maxResults=250,
            ).execute().get("items", [])
            for ev in events:
                if ev.get("status") == "cancelled":
                    continue
                start, all_day = _parse(ev.get("start", {}), self.tz)
                end, _ = _parse(ev.get("end", {}), self.tz)
                if start is None:
                    continue
                if all_day and end is not None:
                    end = end - timedelta(seconds=1)
                items.append(Item(
                    source=self.name, external_id=ev["id"], kind="event",
                    title=ev.get("summary") or "(geen titel)",
                    start=start, end=end, url=ev.get("htmlLink"),
                    subtitle=ev.get("location") or cal.get("summary"),
                    all_day=all_day, meta={"calendar": cal.get("summary")},
                ))
        return items


def _parse(when: dict, tz: ZoneInfo) -> tuple[datetime | None, bool]:
    if "dateTime" in when:
        return datetime.fromisoformat(when["dateTime"]).astimezone(tz), False
    if "date" in when:
        d = datetime.fromisoformat(when["date"])
        return d.replace(tzinfo=tz), True
    return None, False
