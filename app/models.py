"""Uniform Item-model. Elke bron levert Items; de frontend kent geen bronnen."""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Literal

Kind = Literal["event", "deadline", "mail", "task", "alarm"]


@dataclass
class Item:
    source: str
    external_id: str
    kind: Kind
    title: str
    start: datetime | None = None   # event: begin; mail: ontvangen
    end: datetime | None = None
    due: datetime | None = None     # deadline / task
    url: str | None = None          # deeplink naar de bron
    subtitle: str | None = None     # locatie, afzender, vak, lijstnaam
    all_day: bool = False
    meta: dict = field(default_factory=dict)

    @property
    def id(self) -> str:
        return f"{self.source}:{self.external_id}"

    def to_row(self, fetched_at: datetime) -> dict:
        d = asdict(self)
        d["id"] = self.id
        for k in ("start", "end", "due"):
            d[k] = d[k].isoformat() if d[k] else None
        d["all_day"] = int(self.all_day)
        d["meta"] = json.dumps(self.meta, ensure_ascii=False, default=str)
        d["fetched_at"] = fetched_at.isoformat()
        return d

    @classmethod
    def from_row(cls, row) -> "Item":
        def dt(v):
            return datetime.fromisoformat(v) if v else None
        return cls(
            source=row["source"],
            external_id=row["external_id"],
            kind=row["kind"],
            title=row["title"],
            start=dt(row["start"]),
            end=dt(row["end"]),
            due=dt(row["due"]),
            url=row["url"],
            subtitle=row["subtitle"],
            all_day=bool(row["all_day"]),
            meta=json.loads(row["meta"] or "{}"),
        )
