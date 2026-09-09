from __future__ import annotations

from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from . import formatting, views
from .config import ROOT

templates = Jinja2Templates(directory=ROOT / "templates")
templates.env.filters.update({
    "time": formatting.fmt_time, "day": formatting.fmt_day,
    "relative": formatting.fmt_relative, "range": formatting.fmt_range,
})
templates.env.globals["icons"] = views.SOURCE_ICONS


def static_url(name: str) -> str:
    """Versienummer op basis van wijzigingstijd, zodat de browser nooit een oude CSS/JS vasthoudt."""
    try:
        v = int((ROOT / "static" / name).stat().st_mtime)
    except OSError:
        v = 0
    return f"/static/{name}?v={v}"


templates.env.globals["static_url"] = static_url


def render(request: Request, name: str, ctx: dict) -> HTMLResponse:
    return templates.TemplateResponse(request, name, ctx)


def prerender(name: str, ctx: dict) -> str:
    return templates.get_template(name).render(ctx)
