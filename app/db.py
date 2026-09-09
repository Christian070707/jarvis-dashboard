"""SQLite-opslag: items-cache per bron, eigen todos, dismissed-state, wekkers, bronstatus."""
from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from .models import Item

SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
  id TEXT PRIMARY KEY,
  source TEXT NOT NULL,
  external_id TEXT NOT NULL,
  kind TEXT NOT NULL,
  title TEXT NOT NULL,
  subtitle TEXT,
  start TEXT, "end" TEXT, due TEXT,
  url TEXT,
  all_day INTEGER NOT NULL DEFAULT 0,
  meta TEXT,
  fetched_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS items_source ON items(source);
CREATE INDEX IF NOT EXISTS items_kind ON items(kind);

CREATE TABLE IF NOT EXISTS todos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  due TEXT,
  done INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dismissed (
  item_id TEXT PRIMARY KEY,
  dismissed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS alarms (
  app TEXT PRIMARY KEY,
  label TEXT,
  at TEXT NOT NULL,
  received_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS source_status (
  source TEXT PRIMARY KEY,
  label TEXT NOT NULL,
  last_fetch TEXT,
  last_success TEXT,
  item_count INTEGER NOT NULL DEFAULT 0,
  last_error TEXT
);
"""


class Database:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        with self.connect() as c:
            c.executescript(SCHEMA)

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.path, timeout=10, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            with self._lock:
                yield conn
                conn.commit()
        finally:
            conn.close()

    # ---- items ----
    def replace_items(self, source: str, items: list[Item], fetched_at: datetime) -> None:
        rows = [i.to_row(fetched_at) for i in items]
        with self.connect() as c:
            c.execute("DELETE FROM items WHERE source = ?", (source,))
            c.executemany(
                """INSERT OR REPLACE INTO items
                   (id, source, external_id, kind, title, subtitle, start, "end", due, url, all_day, meta, fetched_at)
                   VALUES (:id, :source, :external_id, :kind, :title, :subtitle, :start, :end, :due, :url, :all_day, :meta, :fetched_at)""",
                rows,
            )

    def items(self, kind: str | None = None, include_dismissed: bool = False) -> list[Item]:
        sql = "SELECT i.* FROM items i"
        params: list = []
        if not include_dismissed:
            sql += " LEFT JOIN dismissed d ON d.item_id = i.id"
        where = []
        if kind:
            where.append("i.kind = ?")
            params.append(kind)
        if not include_dismissed:
            where.append("d.item_id IS NULL")
        if where:
            sql += " WHERE " + " AND ".join(where)
        with self.connect() as c:
            return [Item.from_row(r) for r in c.execute(sql, params)]

    # ---- dismissed ----
    def dismiss(self, item_id: str, now: datetime) -> None:
        with self.connect() as c:
            c.execute("INSERT OR REPLACE INTO dismissed VALUES (?, ?)", (item_id, now.isoformat()))

    def undismiss_all(self) -> None:
        with self.connect() as c:
            c.execute("DELETE FROM dismissed")

    # ---- todos ----
    def todos(self, include_done: bool = False) -> list[sqlite3.Row]:
        sql = "SELECT * FROM todos" + ("" if include_done else " WHERE done = 0")
        sql += " ORDER BY done, CASE WHEN due IS NULL THEN 1 ELSE 0 END, due, created_at"
        with self.connect() as c:
            return list(c.execute(sql))

    def add_todo(self, title: str, due: str | None, now: datetime) -> int:
        with self.connect() as c:
            cur = c.execute(
                "INSERT INTO todos (title, due, done, created_at, updated_at) VALUES (?, ?, 0, ?, ?)",
                (title, due or None, now.isoformat(), now.isoformat()),
            )
            return int(cur.lastrowid)

    def toggle_todo(self, todo_id: int, now: datetime) -> None:
        with self.connect() as c:
            c.execute(
                "UPDATE todos SET done = 1 - done, updated_at = ? WHERE id = ?", (now.isoformat(), todo_id)
            )

    def delete_todo(self, todo_id: int) -> None:
        with self.connect() as c:
            c.execute("DELETE FROM todos WHERE id = ?", (todo_id,))

    # ---- alarms ----
    def set_alarm(self, app: str, label: str | None, at: datetime, now: datetime) -> None:
        with self.connect() as c:
            c.execute(
                "INSERT OR REPLACE INTO alarms (app, label, at, received_at) VALUES (?, ?, ?, ?)",
                (app, label, at.isoformat(), now.isoformat()),
            )

    def clear_alarm(self, app: str) -> None:
        with self.connect() as c:
            c.execute("DELETE FROM alarms WHERE app = ?", (app,))

    def alarms(self) -> list[sqlite3.Row]:
        with self.connect() as c:
            return list(c.execute("SELECT * FROM alarms ORDER BY at"))

    # ---- status ----
    def set_status(
        self, source: str, label: str, now: datetime, *, ok: bool, count: int = 0, error: str | None = None
    ) -> None:
        with self.connect() as c:
            row = c.execute("SELECT * FROM source_status WHERE source = ?", (source,)).fetchone()
            last_success = now.isoformat() if ok else (row["last_success"] if row else None)
            c.execute(
                """INSERT OR REPLACE INTO source_status (source, label, last_fetch, last_success, item_count, last_error)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (source, label, now.isoformat(), last_success, count, None if ok else error),
            )

    def statuses(self) -> list[sqlite3.Row]:
        with self.connect() as c:
            return list(c.execute("SELECT * FROM source_status ORDER BY label"))
