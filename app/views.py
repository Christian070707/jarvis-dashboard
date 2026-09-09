"""Bouwt de data voor de vier kolommen uit de items-cache."""
from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from .db import Database
from .models import Item

SOURCE_ICONS = {
    "timeedit": "🎓", "gcal": "📅", "gcal_ics": "📅", "canvas": "📚", "canvas_ics": "📚",
    "trello": "📋", "gmail": "✉️", "outlook": "📨", "outlook_ics": "📨", "alarm": "⏰", "todo": "✅",
}


def _day_bounds(now: datetime) -> tuple[datetime, datetime]:
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return start, start + timedelta(days=1)


def _overlaps(item: Item, a: datetime, b: datetime) -> bool:
    if item.start is None:
        return False
    end = item.end or item.start
    return item.start < b and end >= a


def today_view(db: Database, tz: ZoneInfo) -> dict:
    now = datetime.now(tz)
    d0, d1 = _day_bounds(now)
    d2 = d1 + timedelta(days=1)
    events = db.items(kind="event")
    today = sorted((e for e in events if _overlaps(e, d0, d1)), key=lambda e: (not e.all_day, e.start))
    tomorrow = sorted((e for e in events if _overlaps(e, d1, d2)), key=lambda e: (not e.all_day, e.start))
    alarms = []
    for a in db.alarms():
        at = datetime.fromisoformat(a["at"]).astimezone(tz)
        if at >= now - timedelta(minutes=5):
            alarms.append(Item(source="alarm", external_id=a["app"], kind="alarm",
                               title=a["label"] or "Wekker", start=at, subtitle=a["app"]))
    return {"now": now, "today": today, "tomorrow": tomorrow, "alarms": sorted(alarms, key=lambda a: a.start)}


def deadlines_view(db: Database, tz: ZoneInfo) -> dict:
    now = datetime.now(tz)
    d0, d1 = _day_bounds(now)
    week = d0 + timedelta(days=7)
    items = sorted((i for i in db.items(kind="deadline") if i.due), key=lambda i: i.due)
    groups = {"overdue": [], "today": [], "week": [], "later": []}
    for i in items:
        if i.due < now:
            groups["overdue"].append(i)
        elif i.due < d1:
            groups["today"].append(i)
        elif i.due < week:
            groups["week"].append(i)
        else:
            groups["later"].append(i)
    return {"now": now, "groups": groups, "count": len(items)}


def inbox_view(db: Database, tz: ZoneInfo) -> dict:
    now = datetime.now(tz)
    mails = sorted(db.items(kind="mail"), key=lambda m: m.start or now, reverse=True)
    return {"now": now, "mails": mails}


def tasks_view(db: Database, tz: ZoneInfo) -> dict:
    now = datetime.now(tz)
    todos = db.todos(include_done=False)
    done = db.todos(include_done=True)
    external = sorted(db.items(kind="task"), key=lambda i: (i.source, i.title.lower()))
    return {
        "now": now, "todos": todos, "done_count": sum(1 for t in done if t["done"]),
        "external": external,
    }


def status_view(db: Database, tz: ZoneInfo, active_sources: list[str]) -> dict:
    now = datetime.now(tz)
    rows = []
    for r in db.statuses():
        if r["source"] not in active_sources:
            continue
        last_fetch = datetime.fromisoformat(r["last_fetch"]) if r["last_fetch"] else None
        rows.append({
            "source": r["source"], "label": r["label"], "ok": r["last_error"] is None,
            "count": r["item_count"], "error": r["last_error"], "last_fetch": last_fetch,
        })
    return {"now": now, "sources": rows}


# ---------- Jarvis-extra's ----------
def _frac(dt: datetime, d0: datetime) -> float:
    """Positie van dt binnen de dag die bij d0 begint, als 0..1 (buiten de dag afgekapt)."""
    return max(0.0, min(1.0, (dt - d0).total_seconds() / 86400))


def ring_view(db: Database, tz: ZoneInfo) -> dict:
    """Segmenten voor de 24-uurs dagring: events als bogen, deadlines en wekkers als tikken."""
    now = datetime.now(tz)
    d0, d1 = _day_bounds(now)
    segments, ticks = [], []
    events = [e for e in db.items(kind="event") if not e.all_day and _overlaps(e, d0, d1)]
    done = 0
    for e in events:
        s, en = _frac(e.start, d0), _frac(e.end or e.start + timedelta(hours=1), d0)
        if en <= s:
            en = min(1.0, s + 0.01)
        if (e.end or e.start) < now:
            done += 1
        segments.append({"start": round(s * 100, 2), "length": round((en - s) * 100, 2),
                         "title": e.title, "source": e.source, "past": (e.end or e.start) < now,
                         "current": e.start <= now < (e.end or e.start)})
    for i in db.items(kind="deadline"):
        if i.due and d0 <= i.due < d1:
            ticks.append({"at": round(_frac(i.due, d0) * 100, 2), "title": i.title, "kind": "deadline"})
    for a in db.alarms():
        at = datetime.fromisoformat(a["at"]).astimezone(tz)
        if d0 <= at < d1:
            ticks.append({"at": round(_frac(at, d0) * 100, 2), "title": a["label"] or "Wekker", "kind": "alarm"})
    return {
        "now": now, "segments": segments, "ticks": ticks,
        "now_pct": round(_frac(now, d0) * 100, 2),
        "events_total": len(events), "events_done": done,
    }


def next_view(db: Database, tz: ZoneInfo) -> dict:
    """Wat is nu bezig, wat komt hierna, en de eerstvolgende deadline."""
    now = datetime.now(tz)
    horizon = now + timedelta(days=2)
    events = [e for e in db.items(kind="event") if e.start and not e.all_day]
    current = next((e for e in sorted(events, key=lambda e: e.start)
                    if e.start <= now < (e.end or e.start + timedelta(hours=1))), None)
    upcoming = sorted((e for e in events if now < e.start <= horizon), key=lambda e: e.start)
    nxt = upcoming[0] if upcoming else None
    deadlines = sorted((i for i in db.items(kind="deadline") if i.due and i.due >= now), key=lambda i: i.due)
    overdue = sum(1 for i in db.items(kind="deadline") if i.due and i.due < now)
    alarms = [datetime.fromisoformat(a["at"]).astimezone(tz) for a in db.alarms()]
    alarms = sorted(a for a in alarms if a >= now)
    return {
        "now": now, "current": current, "next": nxt,
        "deadline": deadlines[0] if deadlines else None, "overdue": overdue,
        "alarm": alarms[0] if alarms else None,
    }


def briefing_view(db: Database, tz: ZoneInfo) -> dict:
    """Ochtendbriefing als korte Nederlandse zinnen, regelgebaseerd."""
    now = datetime.now(tz)
    d0, d1 = _day_bounds(now)
    d2 = d1 + timedelta(days=1)
    h = now.hour
    greeting = "Goedemorgen" if 5 <= h < 12 else "Goedemiddag" if h < 18 else "Goedenavond"
    from .formatting import fmt_time

    lines: list[str] = []
    events = sorted((e for e in db.items(kind="event") if _overlaps(e, d0, d1) and not e.all_day),
                    key=lambda e: e.start)
    if events:
        first, last = events[0], events[-1]
        n = len(events)
        s = f"Je hebt vandaag {n} {'afspraak' if n == 1 else 'afspraken'} op het rooster"
        s += f": de eerste om {fmt_time(first.start)}"
        if first.subtitle:
            s += f" in {first.subtitle}"
        if n > 1 and last.end:
            s += f", de laatste eindigt om {fmt_time(last.end)}"
        lines.append(s + ".")
    else:
        lines.append("Er staat vandaag niets op het rooster.")

    deadlines = [i for i in db.items(kind="deadline") if i.due]
    overdue = [i for i in deadlines if i.due < now]
    today = [i for i in deadlines if now <= i.due < d1]
    tomorrow = [i for i in deadlines if d1 <= i.due < d2]
    if today:
        names = ", ".join(i.title for i in today[:3])
        lines.append(f"Vandaag {'moet' if len(today) == 1 else 'moeten'} {names} binnen zijn"
                     f"{', de laatste om ' + fmt_time(max(i.due for i in today)) if today else ''}.")
    if tomorrow:
        lines.append(f"Morgen {'volgt' if len(tomorrow) == 1 else 'volgen'} {len(tomorrow)} "
                     f"{'deadline' if len(tomorrow) == 1 else 'deadlines'}: "
                     + ", ".join(i.title for i in tomorrow[:3]) + ".")
    if overdue:
        lines.append(f"Let op: {len(overdue)} {'deadline is' if len(overdue) == 1 else 'deadlines zijn'} verlopen.")
    if not (today or tomorrow or overdue):
        lines.append("Geen deadlines vandaag of morgen.")

    mails = db.items(kind="mail")
    if mails:
        senders = {m.subtitle for m in mails if m.subtitle}
        lines.append(f"Er {'staat' if len(mails) == 1 else 'staan'} {len(mails)} ongelezen "
                     f"{'mail' if len(mails) == 1 else 'mails'}"
                     + (f", onder andere van {', '.join(list(senders)[:2])}" if senders else "") + ".")

    todos = db.todos()
    if todos:
        lines.append(f"Op je eigen lijst {'staat' if len(todos) == 1 else 'staan'} nog {len(todos)} "
                     f"{'taak' if len(todos) == 1 else 'taken'}.")

    alarms = sorted(datetime.fromisoformat(a["at"]).astimezone(tz) for a in db.alarms())
    alarms = [a for a in alarms if a >= now]
    if alarms:
        from .formatting import fmt_day
        lines.append(f"De volgende wekker staat {fmt_day(alarms[0], now)} om {fmt_time(alarms[0])}.")

    lines.append("Dat was alles. Succes vandaag.")
    return {"now": now, "greeting": greeting, "lines": lines, "text": f"{greeting}. " + " ".join(lines)}


def focus_view(db: Database, tz: ZoneInfo) -> dict:
    """Kandidaten voor focusmodus: verlopen en nabije deadlines, eigen taken, losse taken."""
    now = datetime.now(tz)
    week = now + timedelta(days=7)
    deadlines = sorted((i for i in db.items(kind="deadline") if i.due and i.due < week), key=lambda i: i.due)
    todos = db.todos()
    tasks = sorted(db.items(kind="task"), key=lambda i: i.title.lower())
    return {"now": now, "deadlines": deadlines[:8], "todos": todos[:8], "tasks": tasks[:6]}
