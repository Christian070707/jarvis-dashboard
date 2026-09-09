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
    import app.state as st
    importlib.reload(st)
    import app.setup as setup
    importlib.reload(setup)
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
    asyncio.run(main.state.scheduler.refresh("timeedit"))
    st = client.get("/api/status").json()
    te = next(s for s in st["sources"] if s["source"] == "timeedit")
    assert te["ok"] and te["count"] == 1
    assert "Testcollege" in client.get("/partials/today").text


def test_todo_crud(client):
    r = client.post("/todos", data={"title": "Boodschappen", "due": "2026-09-30"})
    assert "Boodschappen" in r.text
    import app.main as main
    todo_id = main.state.db.todos()[0]["id"]
    assert "Boodschappen" not in client.post(f"/todos/{todo_id}/toggle").text
    client.post(f"/todos/{todo_id}/toggle")
    assert "Boodschappen" not in client.delete(f"/todos/{todo_id}").text


def test_dismiss(client):
    import app.main as main
    item = main.state.db.items()[0]
    assert client.post("/dismiss", data={"item_id": item.id}).status_code == 200
    assert all(i.id != item.id for i in main.state.db.items())
    client.post("/dismiss/reset")
    assert any(i.id == item.id for i in main.state.db.items())


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


def test_setup_wizard_save_test_and_reload(client, tmp_path):
    import app.main as main
    assert client.get("/setup").status_code == 200
    ics = tmp_path / "w.ics"
    day = (datetime.now() + timedelta(days=1)).strftime("%Y%m%d")
    ics.write_text(f"""BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:w1
DTSTART:{day}T090000Z
DTEND:{day}T100000Z
SUMMARY:Wizardcollege
END:VEVENT
END:VCALENDAR
""")
    # test zonder opslaan
    r = client.post("/setup/test", data={"source": "outlook_ics", "OUTLOOK_ICS_URL": f"file://{ics}"})
    assert "1 items" in r.text and "Wizardcollege" in r.text
    assert "outlook_ics" not in main.state.active_names()
    # fout netjes gemeld
    r = client.post("/setup/test", data={"source": "outlook_ics", "OUTLOOK_ICS_URL": "file:///nope.ics"})
    assert "✗" in r.text
    # opslaan -> herladen -> bron actief
    r = client.post("/setup/save", data={"OUTLOOK_ICS_URL": f"file://{ics}"})
    assert "opgeslagen" in r.text
    assert "outlook_ics" in main.state.active_names()
    assert main.state.db.get_settings()["OUTLOOK_ICS_URL"].endswith("w.ics")
    # leegmaken -> bron weg, items en status opgeruimd
    client.post("/setup/save", data={"OUTLOOK_ICS_URL": ""})
    assert "outlook_ics" not in main.state.active_names()
    assert all(i.source != "outlook_ics" for i in main.state.db.items())
    # klaar -> redirect naar dashboard
    r = client.post("/setup/done", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/"
    assert main.state.settings.setup_done


def test_index_redirects_to_setup_when_nothing_configured(tmp_path):
    import os, importlib
    os.environ["DASHBOARD_DB"] = str(tmp_path / "empty.sqlite3")
    for k in ("TIMEEDIT_ICS_URL", "GCAL_ICS_URL", "CANVAS_ICS_URL", "OUTLOOK_ICS_URL"):
        os.environ[k] = " "
    os.environ["GOOGLE_TOKEN_FILE"] = str(tmp_path / "no-token.json")
    import app.config as config, app.state as st, app.setup as setup, app.main as main
    for m in (config, st, setup, main):
        importlib.reload(m)
    from fastapi.testclient import TestClient
    with TestClient(main.app) as c:
        r = c.get("/", follow_redirects=False)
        assert r.status_code == 303 and r.headers["location"] == "/setup"
