import os
from datetime import datetime, timedelta
from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("db")
    os.environ["DASHBOARD_DB"] = str(tmp / "test.sqlite3")
    os.environ["DASHBOARD_SECRET"] = "s3cret"
    for k in list(os.environ):
        if k.endswith("_ICS_URL") or k in ("TRELLO_KEY", "CANVAS_TOKEN", "MS_CLIENT_ID"):
            os.environ.pop(k)
    fixture = tmp / "fixture.ics"
    day = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
    fixture.write_text(f"""BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:today-1
DTSTART:{day}T230000Z
DTEND:{day}T233000Z
SUMMARY:Testcollege
END:VEVENT
END:VCALENDAR
""")
    os.environ["TIMEEDIT_ICS_URL"] = f"file://{fixture}"

    import importlib
    import app.config as config
    importlib.reload(config)
    import app.main as main
    importlib.reload(main)
    from fastapi.testclient import TestClient

    with TestClient(main.app) as c:
        yield c


def test_index_and_partials(client):
    assert client.get("/").status_code == 200
    for p in ("today", "deadlines", "inbox", "tasks", "status"):
        r = client.get(f"/partials/{p}")
        assert r.status_code == 200, p


def test_status_shows_timeedit_after_refresh(client):
    import asyncio
    import app.main as main
    asyncio.run(main.scheduler.refresh("timeedit"))
    st = client.get("/api/status").json()
    te = next(s for s in st["sources"] if s["source"] == "timeedit")
    assert te["ok"] and te["count"] == 1
    assert "Testcollege" in client.get("/partials/today").text


def test_todo_crud(client):
    r = client.post("/todos", data={"title": "Boodschappen", "due": "2026-09-30"})
    assert "Boodschappen" in r.text
    import app.main as main
    todo_id = main.db.todos()[0]["id"]
    assert "Boodschappen" not in client.post(f"/todos/{todo_id}/toggle").text
    client.post(f"/todos/{todo_id}/toggle")
    assert "Boodschappen" not in client.delete(f"/todos/{todo_id}").text


def test_dismiss(client):
    import app.main as main
    item = main.db.items()[0]
    assert client.post("/dismiss", data={"item_id": item.id}).status_code == 200
    assert all(i.id != item.id for i in main.db.items())
    client.post("/dismiss/reset")
    assert any(i.id == item.id for i in main.db.items())


def test_alarm_endpoint(client):
    assert client.post("/api/alarms", json={"app": "phone", "at": "2030-01-01T07:30:00"}).status_code == 401
    r = client.post("/api/alarms", json={"app": "phone", "label": "Opstaan", "at": "2030-01-01T07:30:00"},
                    headers={"X-Dashboard-Secret": "s3cret"})
    assert r.status_code == 200 and r.json()["at"].startswith("2030-01-01T07:30")
    r = client.post("/api/alarms", json={"app": "phone", "at": 1893483000000},
                    headers={"X-Dashboard-Secret": "s3cret"})
    assert r.status_code == 200
    assert len(client.get("/api/alarms").json()) == 1
    r = client.post("/api/alarms", json={"app": "phone", "at": ""}, headers={"X-Dashboard-Secret": "s3cret"})
    assert r.json()["cleared"] == "phone" and client.get("/api/alarms").json() == []


def test_refresh_unknown_source(client):
    assert client.post("/api/refresh?source=nope").status_code == 404
    assert client.post("/api/refresh").status_code == 202


def test_jarvis_partials(client):
    for p in ("ring", "next", "briefing", "focus"):
        r = client.get(f"/partials/{p}")
        assert r.status_code == 200, p
    ring = client.get("/partials/ring").text
    assert "ring-hand" in ring and "Testcollege" in ring
    b = client.get("/api/briefing").json()
    assert b["greeting"] in ("Goedemorgen", "Goedemiddag", "Goedenavond")
    assert any("rooster" in l for l in b["lines"])
    assert "Jarvis" in client.get("/").text
