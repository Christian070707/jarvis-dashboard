"""FastAPI-app: pagina, HTMX-partials, todo-CRUD, wekker-endpoint, status."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, Form, Header, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import formatting, views
from .config import settings
from .db import Database
from .scheduler import Scheduler
from .sources import build_sources

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
log = logging.getLogger("dashboard")

ROOT = Path(__file__).resolve().parent.parent
db = Database(settings.db_path)
sources = build_sources(settings)
scheduler = Scheduler(db, sources, settings.tz)


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("actieve bronnen: %s", ", ".join(s.name for s in sources) or "(geen; vul .env in)")
    await scheduler.start()
    yield
    await scheduler.stop()


app = FastAPI(title="Home Dashboard", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
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


def _active() -> list[str]:
    return [s.name for s in sources]


# ---------- pagina + partials ----------
def _prerender(name: str, ctx: dict) -> str:
    return templates.get_template(name).render(ctx)


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    tz = settings.tz
    return render(request, "index.html", {
        "sources": sources, "tz": settings.tz_name,
        "pre": {
            "status": _prerender("partials/status.html", views.status_view(db, tz, _active())),
            "next": _prerender("partials/next.html", views.next_view(db, tz)),
            "briefing": _prerender("partials/briefing.html", views.briefing_view(db, tz)),
            "ring": _prerender("partials/ring.html", views.ring_view(db, tz)),
            "today": _prerender("partials/today.html", views.today_view(db, tz)),
            "deadlines": _prerender("partials/deadlines.html", views.deadlines_view(db, tz)),
            "inbox": _prerender("partials/inbox.html", views.inbox_view(db, tz)),
            "tasks": _prerender("partials/tasks.html", views.tasks_view(db, tz)),
        },
    })


@app.get("/partials/today", response_class=HTMLResponse)
def partial_today(request: Request):
    return render(request, "partials/today.html", views.today_view(db, settings.tz))


@app.get("/partials/deadlines", response_class=HTMLResponse)
def partial_deadlines(request: Request):
    return render(request, "partials/deadlines.html", views.deadlines_view(db, settings.tz))


@app.get("/partials/inbox", response_class=HTMLResponse)
def partial_inbox(request: Request):
    return render(request, "partials/inbox.html", views.inbox_view(db, settings.tz))


@app.get("/partials/tasks", response_class=HTMLResponse)
def partial_tasks(request: Request):
    return render(request, "partials/tasks.html", views.tasks_view(db, settings.tz))


@app.get("/partials/ring", response_class=HTMLResponse)
def partial_ring(request: Request):
    return render(request, "partials/ring.html", views.ring_view(db, settings.tz))


@app.get("/partials/next", response_class=HTMLResponse)
def partial_next(request: Request):
    return render(request, "partials/next.html", views.next_view(db, settings.tz))


@app.get("/partials/briefing", response_class=HTMLResponse)
def partial_briefing(request: Request):
    return render(request, "partials/briefing.html", views.briefing_view(db, settings.tz))


@app.get("/partials/focus", response_class=HTMLResponse)
def partial_focus(request: Request):
    return render(request, "partials/focus.html", views.focus_view(db, settings.tz))


@app.get("/api/briefing")
def api_briefing():
    ctx = views.briefing_view(db, settings.tz)
    return {"greeting": ctx["greeting"], "lines": ctx["lines"], "text": ctx["text"]}


@app.get("/partials/status", response_class=HTMLResponse)
def partial_status(request: Request):
    return render(request, "partials/status.html", views.status_view(db, settings.tz, _active()))


# ---------- eigen todolist ----------
@app.post("/todos", response_class=HTMLResponse)
def add_todo(request: Request, title: str = Form(...), due: str = Form("")):
    title = title.strip()
    if title:
        db.add_todo(title, due.strip() or None, datetime.now(settings.tz))
    return partial_tasks(request)


@app.post("/todos/{todo_id}/toggle", response_class=HTMLResponse)
def toggle_todo(request: Request, todo_id: int):
    db.toggle_todo(todo_id, datetime.now(settings.tz))
    return partial_tasks(request)


@app.delete("/todos/{todo_id}", response_class=HTMLResponse)
def delete_todo(request: Request, todo_id: int):
    db.delete_todo(todo_id)
    return partial_tasks(request)


# ---------- dismiss ----------
@app.post("/dismiss")
def dismiss(item_id: str = Form(...)):
    db.dismiss(item_id, datetime.now(settings.tz))
    return Response(content="", status_code=200)


@app.post("/dismiss/reset")
def dismiss_reset():
    db.undismiss_all()
    return Response(content="", status_code=200, headers={"HX-Refresh": "true"})


# ---------- wekkers (vanaf telefoon) ----------
def _check_secret(secret: str | None) -> None:
    if not settings.secret or secret != settings.secret:
        raise HTTPException(status_code=401, detail="ongeldig of ontbrekend X-Dashboard-Secret")


@app.post("/api/alarms")
async def set_alarm(request: Request, x_dashboard_secret: str | None = Header(default=None)):
    _check_secret(x_dashboard_secret)
    body = await request.json()
    app_name = str(body.get("app") or "phone")
    raw = body.get("at")
    if raw in (None, "", 0, "0"):
        db.clear_alarm(app_name)
        return {"ok": True, "cleared": app_name}
    try:
        if isinstance(raw, (int, float)) or str(raw).isdigit():
            ms = float(raw)
            at = datetime.fromtimestamp(ms / 1000 if ms > 1e11 else ms, tz=settings.tz)
        else:
            at = datetime.fromisoformat(str(raw))
            if at.tzinfo is None:
                at = at.replace(tzinfo=settings.tz)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"ongeldige tijd: {e}") from e
    db.set_alarm(app_name, body.get("label"), at, datetime.now(settings.tz))
    return {"ok": True, "app": app_name, "at": at.isoformat()}


@app.delete("/api/alarms/{app_name}")
def clear_alarm(app_name: str, x_dashboard_secret: str | None = Header(default=None)):
    _check_secret(x_dashboard_secret)
    db.clear_alarm(app_name)
    return {"ok": True}


@app.get("/api/alarms")
def list_alarms():
    return [dict(a) for a in db.alarms()]


# ---------- status + refresh ----------
@app.get("/api/status")
def api_status():
    ctx = views.status_view(db, settings.tz, _active())
    return JSONResponse({
        "now": ctx["now"].isoformat(),
        "sources": [{**s, "last_fetch": s["last_fetch"].isoformat() if s["last_fetch"] else None}
                    for s in ctx["sources"]],
    })


@app.post("/api/refresh")
async def api_refresh(background: BackgroundTasks, source: str | None = None):
    if source and scheduler.by_name(source) is None:
        raise HTTPException(status_code=404, detail=f"onbekende bron: {source}")
    background.add_task(scheduler.refresh, source)
    return Response(content="", status_code=202, headers={"HX-Trigger": "refreshed"})
