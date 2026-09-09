from __future__ import annotations

from typing import Protocol

from ..models import Item


class Source(Protocol):
    name: str        # korte sleutel, ook gebruikt als Item.source
    label: str       # weergavenaam
    interval: int    # seconden tussen fetches

    def configured(self) -> bool: ...
    def fetch(self) -> list[Item]: ...
