"""Jinja-filters voor datum/tijd in het Nederlands."""
from __future__ import annotations

from datetime import datetime

DAYS = ["ma", "di", "wo", "do", "vr", "za", "zo"]
MONTHS = ["jan", "feb", "mrt", "apr", "mei", "jun", "jul", "aug", "sep", "okt", "nov", "dec"]


def fmt_time(dt: datetime | None) -> str:
    return dt.strftime("%H:%M") if dt else ""


def fmt_day(dt: datetime | None, now: datetime | None = None) -> str:
    if not dt:
        return ""
    now = now or datetime.now(dt.tzinfo)
    delta = (dt.date() - now.date()).days
    if delta == 0:
        return "vandaag"
    if delta == 1:
        return "morgen"
    if delta == -1:
        return "gisteren"
    if 1 < delta < 7:
        return DAYS[dt.weekday()]
    return f"{DAYS[dt.weekday()]} {dt.day} {MONTHS[dt.month - 1]}"


def fmt_relative(dt: datetime | None, now: datetime | None = None) -> str:
    if not dt:
        return ""
    now = now or datetime.now(dt.tzinfo)
    secs = (dt - now).total_seconds()
    past = secs < 0
    secs = abs(secs)
    if secs < 60:
        txt = "nu"
        return txt
    if secs < 3600:
        txt = f"{int(secs // 60)} min"
    elif secs < 86400:
        txt = f"{int(secs // 3600)} u"
    else:
        txt = f"{int(secs // 86400)} d"
    return f"{txt} geleden" if past else f"over {txt}"


def fmt_range(item, now: datetime | None = None) -> str:
    if item.all_day:
        return "hele dag"
    if item.start and item.end:
        return f"{fmt_time(item.start)}–{fmt_time(item.end)}"
    return fmt_time(item.start)
