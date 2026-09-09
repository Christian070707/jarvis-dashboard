"""Canvas planner-API: opdrachten, quizzes, discussies en agenda-items van de ingelogde student."""
from __future__ import annotations

import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import httpx

from ..models import Item

SKIP_TYPES = {"announcement"}


def _dt(value: str | None, tz: ZoneInfo) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(tz)


def parse_planner_items(raw: list[dict], *, source: str, base_url: str, tz: ZoneInfo) -> list[Item]:
    items: list[Item] = []
    for p in raw:
        ptype = p.get("plannable_type", "")
        if ptype in SKIP_TYPES:
            continue
        plannable = p.get("plannable") or {}
        subs = p.get("submissions")
        submitted = bool(isinstance(subs, dict) and (subs.get("submitted") or subs.get("graded")))
        if submitted:
            continue
        html_url = p.get("html_url") or ""
        if html_url.startswith("/"):
            html_url = base_url + html_url
        title = plannable.get("title") or p.get("context_name") or ptype
        ext_id = f"{ptype}-{plannable.get('id') or p.get('plannable_id')}"
        if ptype == "calendar_event":
            start = _dt(plannable.get("start_at"), tz)
            end = _dt(plannable.get("end_at"), tz)
            items.append(Item(
                source=source, external_id=ext_id, kind="event", title=title,
                start=start, end=end, url=html_url or None, subtitle=p.get("context_name"),
                all_day=bool(plannable.get("all_day")),
                meta={"type": ptype},
            ))
            continue
        due = _dt(plannable.get("due_at") or p.get("plannable_date"), tz)
        items.append(Item(
            source=source, external_id=ext_id, kind="deadline" if due else "task", title=title,
            due=due, url=html_url or None, subtitle=p.get("context_name"),
            meta={"type": ptype, "points": plannable.get("points_possible")},
        ))
    return items


class CanvasSource:
    name = "canvas"
    label = "Canvas"
    interval = 10 * 60

    def __init__(self, *, base_url: str, token: str, tz: ZoneInfo):
        self.base_url, self.token, self.tz = base_url.rstrip("/"), token, tz

    def configured(self) -> bool:
        return bool(self.base_url and self.token)

    def fetch(self) -> list[Item]:
        now = datetime.now(self.tz)
        params = {
            "start_date": (now - timedelta(days=14)).isoformat(),
            "end_date": (now + timedelta(days=60)).isoformat(),
            "per_page": 100,
        }
        raw: list[dict] = []
        url: str | None = f"{self.base_url}/api/v1/planner/items"
        with httpx.Client(timeout=30, headers={"Authorization": f"Bearer {self.token}"}) as client:
            while url:
                r = client.get(url, params=params)
                r.raise_for_status()
                raw.extend(r.json())
                params = {}  # volgende pagina's zitten volledig in de Link-header
                url = _next_link(r.headers.get("Link", ""))
        return parse_planner_items(raw, source=self.name, base_url=self.base_url, tz=self.tz)


def _next_link(header: str) -> str | None:
    m = re.search(r'<([^>]+)>;\s*rel="next"', header)
    return m.group(1) if m else None
