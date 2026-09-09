from datetime import datetime
from zoneinfo import ZoneInfo

from app.sources.canvas import _next_link, parse_planner_items
from app.sources.trello import parse_cards

TZ = ZoneInfo("Europe/Amsterdam")


def test_trello_cards():
    lists = [{"id": "L1", "name": "Te doen"}, {"id": "L2", "name": "Done"}]
    cards = [
        {"id": "a", "name": "Factuur sturen", "due": "2026-09-10T10:00:00.000Z", "dueComplete": False,
         "shortUrl": "https://trello.com/c/abc", "idList": "L1", "labels": [{"name": "admin"}]},
        {"id": "b", "name": "Idee", "due": None, "idList": "L1", "shortUrl": "https://trello.com/c/b"},
        {"id": "c", "name": "Klaar", "due": None, "idList": "L2"},
        {"id": "d", "name": "Afgevinkt", "due": "2026-09-01T10:00:00.000Z", "dueComplete": True, "idList": "L1"},
    ]
    items = parse_cards(cards, lists, source="trello", tz=TZ)
    assert [i.external_id for i in items] == ["a", "b"]
    assert items[0].kind == "deadline" and items[0].due == datetime(2026, 9, 10, 12, 0, tzinfo=TZ)
    assert items[0].subtitle == "Te doen" and items[0].meta["labels"] == ["admin"]
    assert items[1].kind == "task"


def test_canvas_planner_items():
    raw = [
        {"plannable_type": "assignment", "plannable_id": 1, "context_name": "Statistiek",
         "plannable": {"id": 1, "title": "Opdracht 1", "due_at": "2026-09-12T21:59:00Z", "points_possible": 10},
         "html_url": "/courses/5/assignments/1", "submissions": {"submitted": False}},
        {"plannable_type": "assignment", "plannable_id": 2, "context_name": "Statistiek",
         "plannable": {"id": 2, "title": "Al ingeleverd", "due_at": "2026-09-13T21:59:00Z"},
         "html_url": "/courses/5/assignments/2", "submissions": {"submitted": True}},
        {"plannable_type": "calendar_event", "plannable_id": 3, "context_name": "Statistiek",
         "plannable": {"id": 3, "title": "Q&A", "start_at": "2026-09-11T12:00:00Z", "end_at": "2026-09-11T13:00:00Z"},
         "html_url": "https://canvas.utwente.nl/calendar?event_id=3", "submissions": False},
        {"plannable_type": "announcement", "plannable_id": 4, "plannable": {"title": "x"}},
    ]
    items = parse_planner_items(raw, source="canvas", base_url="https://canvas.utwente.nl", tz=TZ)
    assert [i.title for i in items] == ["Opdracht 1", "Q&A"]
    assert items[0].kind == "deadline" and items[0].url == "https://canvas.utwente.nl/courses/5/assignments/1"
    assert items[0].due == datetime(2026, 9, 12, 23, 59, tzinfo=TZ)
    assert items[1].kind == "event" and items[1].start.hour == 14


def test_next_link():
    h = '<https://c/api/v1/planner/items?page=2>; rel="next", <https://c/x?page=1>; rel="first"'
    assert _next_link(h) == "https://c/api/v1/planner/items?page=2"
    assert _next_link('<https://c/x?page=1>; rel="first"') is None
