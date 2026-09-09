"""FastAPI-app: pagina, HTMX-partials, todo-CRUD, wekker-endpoint, status, setup-wizard."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import BackgroundTasks, FastAPI, Form, Header, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles

from . import views
from .config import ROOT
from .setup import router as setup_router
from .state import state
from .templating import prerender, render

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
log = logging.getLogger("dashboard")


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("data in %s", state.settings.data_dir)
    log.info("actieve bronnen: %s", ", ".join(state.active_names()) or "(geen; open /setup)")
    await state.scheduler.start()
    yield
    await state.scheduler.stop()


app = FastAPI(title="Jarvis", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
app.include_router(setup_router)


def _tz():
    return state.settings.tz


# ---------- pagina + partials ----------
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    s = state.settings
    if not s.setup_done and not s.any_source_configured():
        return RedirectResponse("/setup", status_code=303)
    db, tz = state.db, _tz()
    return render(request, "index.html", {
        "sources": state.sources, "tz": s.tz_name,
        "pre": {
            "status": prerender("partials/status.html", views.status_view(db, tz, state.active_names())),
            "next": prerender("partials/next.html", views.next_view(db, tz)),
            "briefing": prerender("partials/briefing.html", views.briefing_view(db, tz)),
            "ring": prerender("partials/ring.html", views.ring_view(db, tz)),
            "today": prerender("partials/today.html", views.today_view(db, tz)),
            "deadlines": prerender("partials/deadlines.html", views.deadlines_view(db, tz)),
            "inbox": prerender("partials/inbox.html", views.inbox_view(db, tz)),
            "tasks": prerender("partials/tasks.html", views.tasks_view(db, tz)),
        },
    })


@app.get("/partials/today", response_class=HTMLResponse)
def partial_today(request: Request):
    return render(request, "partials/today.html", views.today_view(state.db, _tz()))


@app.get("/partials/deadlines", response_class=HTMLResponse)
def partial_deadlines(request: Request):
    return render(request, "partials/deadlines.html", views.deadlines_view(state.db, _tz()))


@app.get("/partials/inbox", response_class=HTMLResponse)
def partial_inbox(request: Request):
    return render(request, "partials/inbox.html", views.inbox_view(state.db, _tz()))


@app.get("/partials/tasks", response_class=HTMLResponse)
def partial_tasks(request: Request):
    return render(request, "partials/tasks.html", views.tasks_view(state.db, _tz()))


@app.get("/partials/ring", response_class=HTMLResponse)
def partial_ring(request: Request):
    return render(request, "partials/ring.html", views.ring_view(state.db, _tz()))


@app.get("/partials/next", response_class=HTMLResponse)
def partial_next(request: Request):
    return render(request, "partials/next.html", views.next_view(state.db, _tz()))


@app.get("/partials/briefing", response_class=HTMLResponse)
def partial_briefing(request: Request):
    return render(request, "partials/briefing.html", views.briefing_view(state.db, _tz()))


@app.get("/partials/focus", response_class=HTMLResponse)
def partial_focus(request: Request):
    return render(request, "partials/focus.html", views.focus_view(state.db, _tz()))


@app.get("/partials/status", response_class=HTMLResponse)
def partial_status(request: Request):
    return render(request, "partials/status.html", views.status_view(state.db, _tz(), state.active_names()))


@app.get("/api/briefing")
def api_briefing():
    ctx = views.briefing_view(state.db, _tz())
    return {"greeting": ctx["greeting"], "lines": ctx["lines"], "text": ctx["text"]}


# ---------- eigen todolist ----------
@app.post("/todos", response_class=HTMLResponse)
def add_todo(request: Request, title: str = Form(...), due: str = Form("")):
    title = title.strip()
    if title:
        state.db.add_todo(title, due.strip() or None, datetime.now(_tz()))
    return partial_tasks(request)


@app.post("/todos/{todo_id}/toggle", response_class=HTMLResponse)
def toggle_todo(request: Request, todo_id: int):
    state.db.toggle_todo(todo_id, datetime.now(_tz()))
    return partial_tasks(request)


@app.delete("/todos/{todo_id}", response_class=HTMLResponse)
def delete_todo(request: Request, todo_id: int):
    state.db.delete_todo(todo_id)
    return partial_tasks(request)


# ---------- dismiss ----------
@app.post("/dismiss")
def dismiss(item_id: str = Form(...)):
    state.db.dismiss(item_id, datetime.now(_tz()))
    return Response(content="", status_code=200)


@app.post("/dismiss/reset")
def dismiss_reset():
    state.db.undismiss_all()
    return Response(content="", status_code=200, headers={"HX-Refresh": "true"})


# ---------- wekkers (vanaf telefoon) ----------
def _check_secret(secret: str | None) -> None:
    if not state.settings.secret or secret != state.settings.secret:
        raise HTTPException(status_code=401, detail="ongeldig of ontbrekend X-Dashboard-Secret")


@app.post("/api/alarms")
async def set_alarm(request: Request, x_dashboard_secret: str | None = Header(default=None)):
    _check_secret(x_dashboard_secret)
    tz = _tz()
    body = await request.json()
    app_name = str(body.get("app") or "phone")
    raw = body.get("at")
    if raw in (None, "", 0, "0"):
        state.db.clear_alarm(app_name)
        return {"ok": True, "cleared": app_name}
    try:
        if isinstance(raw, (int, float)) or str(raw).isdigit():
            ms = float(raw)
            at = datetime.fromtimestamp(ms / 1000 if ms > 1e11 else ms, tz=tz)
        else:
            at = datetime.fromisoformat(str(raw))
            if at.tzinfo is None:
                at = at.replace(tzinfo=tz)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"ongeldige tijd: {e}") from e
    state.db.set_alarm(app_name, body.get("label"), at, datetime.now(tz))
    return {"ok": True, "app": app_name, "at": at.isoformat()}


@app.delete("/api/alarms/{app_name}")
def clear_alarm(app_name: str, x_dashboard_secret: str | None = Header(default=None)):
    _check_secret(x_dashboard_secret)
    state.db.clear_alarm(app_name)
    return {"ok": True}


@app.get("/api/alarms")
def list_alarms():
    return [dict(a) for a in state.db.alarms()]


# ---------- status + refresh ----------
@app.get("/api/status")
def api_status():
    ctx = views.status_view(state.db, _tz(), state.active_names())
    return JSONResponse({
        "now": ctx["now"].isoformat(),
        "sources": [{**s, "last_fetch": s["last_fetch"].isoformat() if s["last_fetch"] else None}
                    for s in ctx["sources"]],
    })


@app.post("/api/refresh")
async def api_refresh(background: BackgroundTasks, source: str | None = None):
    if source and state.scheduler.by_name(source) is None:
        raise HTTPException(status_code=404, detail=f"onbekende bron: {source}")
    background.add_task(state.scheduler.refresh, source)
    return Response(content="", status_code=202, headers={"HX-Trigger": "refreshed"})
