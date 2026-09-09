"""Trello-bord: kaarten met due-date worden deadlines, zonder due-date taken."""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import httpx

from ..models import Item

API = "https://api.trello.com/1"
DONE_LIST_NAMES = ("done", "klaar", "afgerond", "gereed", "archief", "completed")


def parse_cards(cards: list[dict], lists: list[dict], *, source: str, tz: ZoneInfo) -> list[Item]:
    list_names = {l["id"]: l["name"] for l in lists}
    items: list[Item] = []
    for c in cards:
        if c.get("closed") or c.get("dueComplete"):
            continue
        list_name = list_names.get(c.get("idList"), "")
        if list_name.strip().lower() in DONE_LIST_NAMES:
            continue
        due = None
        if c.get("due"):
            due = datetime.fromisoformat(c["due"].replace("Z", "+00:00")).astimezone(tz)
        labels = [l.get("name") for l in c.get("labels", []) if l.get("name")]
        items.append(
            Item(
                source=source,
                external_id=c["id"],
                kind="deadline" if due else "task",
                title=c["name"],
                due=due,
                url=c.get("shortUrl") or c.get("url"),
                subtitle=list_name or None,
                meta={"labels": labels},
            )
        )
    return items


class TrelloSource:
    name = "trello"
    label = "Trello"
    interval = 5 * 60

    def __init__(self, *, key: str, token: str, board_id: str, tz: ZoneInfo):
        self.key, self.token, self.board_id, self.tz = key, token, board_id, tz

    def configured(self) -> bool:
        return bool(self.key and self.token and self.board_id)

    def _get(self, client: httpx.Client, path: str, **params) -> list[dict]:
        r = client.get(f"{API}{path}", params={"key": self.key, "token": self.token, **params})
        r.raise_for_status()
        return r.json()

    def fetch(self) -> list[Item]:
        with httpx.Client(timeout=30) as client:
            lists = self._get(client, f"/boards/{self.board_id}/lists", fields="name")
            cards = self._get(
                client, f"/boards/{self.board_id}/cards/open",
                fields="name,due,dueComplete,shortUrl,url,idList,labels,closed",
            )
        return parse_cards(cards, lists, source=self.name, tz=self.tz)
