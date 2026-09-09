"""Microsoft Graph (UT M365): ongelezen mail, agenda en To Do. Token via scripts/ms_auth.py.

Werkt alleen als de UT-tenant user-consent voor je eigen app-registratie toestaat.
Zo niet: gebruik OUTLOOK_ICS_URL voor de agenda en de eigen todolist voor taken.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx

from ..models import Item

GRAPH = "https://graph.microsoft.com/v1.0"
SCOPES = ["Mail.Read", "Calendars.Read", "Tasks.Read"]
AUTHORITY = "https://login.microsoftonline.com/common"


def acquire_token(client_id: str, token_file: Path, *, interactive: bool = False) -> str:
    import msal

    cache = msal.SerializableTokenCache()
    if token_file.exists():
        cache.deserialize(token_file.read_text())
    app = msal.PublicClientApplication(client_id, authority=AUTHORITY, token_cache=cache)
    result = None
    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(SCOPES, account=accounts[0])
    if not result and interactive:
        flow = app.initiate_device_flow(scopes=SCOPES)
        if "user_code" not in flow:
            raise RuntimeError(f"Device flow mislukt: {flow}")
        print(flow["message"])
        result = app.acquire_token_by_device_flow(flow)
    if not result or "access_token" not in result:
        raise RuntimeError(f"Geen Microsoft-token: {(result or {}).get('error_description', 'draai scripts/ms_auth.py')}")
    if cache.has_state_changed:
        token_file.parent.mkdir(parents=True, exist_ok=True)
        token_file.write_text(cache.serialize())
    return result["access_token"]


def _dt(value: str | None, tz: ZoneInfo) -> datetime | None:
    if not value:
        return None
    v = value.rstrip("Z")
    if "." in v:
        v = v.split(".")[0]
    return datetime.fromisoformat(v).replace(tzinfo=ZoneInfo("UTC")).astimezone(tz)


class OutlookGraphSource:
    name = "outlook"
    label = "Outlook"
    interval = 3 * 60

    def __init__(self, *, client_id: str, token_file: Path, tz: ZoneInfo):
        self.client_id, self.token_file, self.tz = client_id, token_file, tz

    def configured(self) -> bool:
        return bool(self.client_id) and self.token_file.exists()

    def fetch(self) -> list[Item]:
        token = acquire_token(self.client_id, self.token_file)
        now = datetime.now(self.tz)
        items: list[Item] = []
        with httpx.Client(
            timeout=30,
            headers={"Authorization": f"Bearer {token}", "Prefer": 'outlook.timezone="UTC"'},
        ) as c:
            # Mail
            r = c.get(f"{GRAPH}/me/mailFolders/inbox/messages", params={
                "$filter": "isRead eq false", "$top": 30, "$orderby": "receivedDateTime desc",
                "$select": "subject,from,receivedDateTime,webLink,bodyPreview",
            })
            r.raise_for_status()
            for m in r.json().get("value", []):
                sender = (m.get("from") or {}).get("emailAddress", {})
                items.append(Item(
                    source=self.name, external_id=f"mail-{m['id']}", kind="mail",
                    title=m.get("subject") or "(geen onderwerp)",
                    start=_dt(m.get("receivedDateTime"), self.tz), url=m.get("webLink"),
                    subtitle=sender.get("name") or sender.get("address"),
                    meta={"snippet": (m.get("bodyPreview") or "")[:200], "from": sender.get("address")},
                ))
            # Agenda
            r = c.get(f"{GRAPH}/me/calendarView", params={
                "startDateTime": (now - timedelta(days=1)).isoformat(),
                "endDateTime": (now + timedelta(days=30)).isoformat(),
                "$top": 200, "$select": "subject,start,end,location,webLink,isAllDay,isCancelled",
            })
            r.raise_for_status()
            for ev in r.json().get("value", []):
                if ev.get("isCancelled"):
                    continue
                items.append(Item(
                    source=self.name, external_id=f"event-{ev['id']}", kind="event",
                    title=ev.get("subject") or "(geen titel)",
                    start=_dt(ev["start"]["dateTime"], self.tz), end=_dt(ev["end"]["dateTime"], self.tz),
                    url=ev.get("webLink"), subtitle=(ev.get("location") or {}).get("displayName"),
                    all_day=bool(ev.get("isAllDay")),
                ))
            # To Do
            r = c.get(f"{GRAPH}/me/todo/lists")
            if r.status_code == 200:
                for lst in r.json().get("value", []):
                    t = c.get(f"{GRAPH}/me/todo/lists/{lst['id']}/tasks", params={
                        "$filter": "status ne 'completed'", "$top": 100,
                    })
                    if t.status_code != 200:
                        continue
                    for task in t.json().get("value", []):
                        due = None
                        if task.get("dueDateTime"):
                            due = _dt(task["dueDateTime"]["dateTime"], self.tz)
                        items.append(Item(
                            source=self.name, external_id=f"todo-{task['id']}",
                            kind="deadline" if due else "task", title=task.get("title") or "(geen titel)",
                            due=due, url="https://to-do.office.com/tasks/", subtitle=lst.get("displayName"),
                        ))
        return items
