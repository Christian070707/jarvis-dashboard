"""Ververst elke bron op zijn eigen interval in een achtergrondtaak. Een falende bron raakt de rest niet."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from .db import Database
from .sources.base import Source

log = logging.getLogger("dashboard.scheduler")


class Scheduler:
    def __init__(self, db: Database, sources: list[Source], tz: ZoneInfo):
        self.db, self.sources, self.tz = db, sources, tz
        self._tasks: list[asyncio.Task] = []

    def by_name(self, name: str) -> Source | None:
        return next((s for s in self.sources if s.name == name), None)

    async def start(self) -> None:
        for src in self.sources:
            self._tasks.append(asyncio.create_task(self._loop(src), name=f"fetch:{src.name}"))

    async def stop(self) -> None:
        for t in self._tasks:
            t.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)

    async def _loop(self, src: Source) -> None:
        while True:
            await self.run(src)
            await asyncio.sleep(src.interval)

    async def run(self, src: Source) -> None:
        now = datetime.now(self.tz)
        try:
            items = await asyncio.to_thread(src.fetch)
            self.db.replace_items(src.name, items, now)
            self.db.set_status(src.name, src.label, now, ok=True, count=len(items))
            log.info("%s: %d items", src.name, len(items))
        except Exception as e:  # noqa: BLE001 - bron mag nooit de app neerhalen
            msg = f"{type(e).__name__}: {e}"[:300]
            self.db.set_status(src.name, src.label, now, ok=False, error=msg)
            log.warning("%s mislukt: %s", src.name, msg)

    async def refresh(self, name: str | None = None) -> None:
        targets = [s for s in self.sources if name is None or s.name == name]
        await asyncio.gather(*(self.run(s) for s in targets))
