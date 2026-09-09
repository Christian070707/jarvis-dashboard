"""Eén object met database, instellingen, actieve bronnen en scheduler; herlaadbaar vanuit de wizard."""
from __future__ import annotations

import logging
from datetime import datetime

from .config import Settings, build_settings
from .db import Database
from .scheduler import Scheduler
from .sources import build_sources

log = logging.getLogger("dashboard.state")


class AppState:
    def __init__(self) -> None:
        base = build_settings()
        base.data_dir.mkdir(parents=True, exist_ok=True)
        self.db = Database(base.db_path)
        self.settings: Settings = build_settings(self.db.get_settings())
        self.sources = build_sources(self.settings)
        self.scheduler = Scheduler(self.db, self.sources, self.settings.tz)

    def active_names(self) -> list[str]:
        return [s.name for s in self.sources]

    async def reload(self) -> None:
        """Instellingen opnieuw lezen, bronnen opnieuw opbouwen, scheduler herstarten."""
        old = set(self.active_names())
        await self.scheduler.stop()
        self.settings = build_settings(self.db.get_settings())
        self.sources = build_sources(self.settings)
        now = datetime.now(self.settings.tz)
        for gone in old - set(self.active_names()):
            self.db.replace_items(gone, [], now)
            self.db.clear_source_status(gone)
        self.scheduler = Scheduler(self.db, self.sources, self.settings.tz)
        await self.scheduler.start()
        log.info("herladen; actieve bronnen: %s", ", ".join(self.active_names()) or "(geen)")


state = AppState()
