from datetime import datetime
from zoneinfo import ZoneInfo

from app.sources.ical import parse_ical

TZ = ZoneInfo("Europe/Amsterdam")

ICS = b"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//test//
BEGIN:VEVENT
UID:lecture-1
DTSTART;TZID=Europe/Amsterdam:20260909T104500
DTEND;TZID=Europe/Amsterdam:20260909T123000
SUMMARY:Lineaire algebra
LOCATION:RA 2503
END:VEVENT
BEGIN:VEVENT
UID:weekly-1
DTSTART;TZID=Europe/Amsterdam:20260901T090000
DTEND;TZID=Europe/Amsterdam:20260901T100000
RRULE:FREQ=WEEKLY;COUNT=10
SUMMARY:Werkcollege
END:VEVENT
BEGIN:VEVENT
UID:allday-1
DTSTART;VALUE=DATE:20260910
DTEND;VALUE=DATE:20260911
SUMMARY:Vrije dag
END:VEVENT
BEGIN:VEVENT
UID:event-assignment-123
DTSTART:20260912T215900Z
DTEND:20260912T215900Z
SUMMARY:Opdracht 2 [Statistiek]
URL:https://canvas.utwente.nl/courses/1/assignments/123
END:VEVENT
BEGIN:VEVENT
UID:event-calendar-event-7
DTSTART:20260911T120000Z
DTEND:20260911T130000Z
SUMMARY:Tutorial
END:VEVENT
END:VCALENDAR
"""

WINDOW = (datetime(2026, 9, 8, tzinfo=TZ), datetime(2026, 9, 20, tzinfo=TZ))


def parse(kind):
    return parse_ical(ICS, source="t", kind=kind, tz=TZ, window_start=WINDOW[0], window_end=WINDOW[1],
                      link_url="https://example.org/rooster")


def test_timed_event_local_tz_and_location():
    items = {i.title: i for i in parse("event")}
    la = items["Lineaire algebra"]
    assert la.start == datetime(2026, 9, 9, 10, 45, tzinfo=TZ)
    assert la.end.hour == 12 and la.subtitle == "RA 2503"
    assert la.url == "https://example.org/rooster"
    assert not la.all_day


def test_recurring_expanded_within_window():
    weekly = [i for i in parse("event") if i.title == "Werkcollege"]
    assert [i.start.day for i in weekly] == [8, 15]
    assert len({i.external_id for i in weekly}) == 2


def test_all_day():
    vrij = next(i for i in parse("event") if i.title == "Vrije dag")
    assert vrij.all_day and vrij.start.date().isoformat() == "2026-09-10"
    assert vrij.end.date().isoformat() == "2026-09-10"


def test_canvas_assignment_becomes_deadline_with_url_and_utc_conversion():
    items = {i.title: i for i in parse("deadline")}
    opdr = items["Opdracht 2 [Statistiek]"]
    assert opdr.kind == "deadline"
    assert opdr.due == datetime(2026, 9, 12, 23, 59, tzinfo=TZ)
    assert opdr.url.endswith("/assignments/123")
    # Gewone agenda-items in de Canvas-feed blijven events
    assert items["Tutorial"].kind == "event"


def test_all_day_deadline_is_due_end_of_day():
    ics = b"""BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:event-assignment-77
DTSTART;VALUE=DATE:20260911
DTEND;VALUE=DATE:20260912
SUMMARY:Team Contract
END:VEVENT
END:VCALENDAR
"""
    item = parse_ical(ics, source="c", kind="deadline", tz=TZ, window_start=WINDOW[0], window_end=WINDOW[1])[0]
    assert item.kind == "deadline" and item.all_day
    assert item.due.date().isoformat() == "2026-09-11" and item.due.hour == 23
