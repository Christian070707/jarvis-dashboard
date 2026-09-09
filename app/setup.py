"""Setup-wizard: bronnen instellen, testen en opslaan zonder .env; Google koppelen vanuit de app."""
from __future__ import annotations

import logging
import threading
from datetime import datetime

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from .config import WIZARD_KEYS, build_settings
from .sources import build_sources
from .state import state
from .templating import render

log = logging.getLogger("dashboard.setup")
router = APIRouter()

UNIVERSITIES = {
    "utwente": {
        "name": "Universiteit Twente",
        "timeedit_web": "https://cloud.timeedit.net/nl_utwente/web/",
        "canvas_base": "https://canvas.utwente.nl",
        "timeedit_help": "Ga naar cloud.timeedit.net/nl_utwente/web, log in, open je persoonlijke rooster en klik op "
                         "'Abonneren' of het agenda-icoon. Kies 'Kopieer link' (niet downloaden). De link eindigt op .ics.",
        "canvas_help": "Ga naar canvas.utwente.nl, klik links op 'Agenda' en rechtsonder op 'Calendar Feed'. Kopieer de link.",
        "outlook_help": "Ga naar outlook.office.com, Instellingen, Agenda, 'Gedeelde agenda's', 'Een agenda publiceren'. "
                        "Kies je agenda en 'Kan alle details bekijken', klik Publiceren en kopieer de ICS-link.",
    },
    "other": {
        "name": "Andere instelling",
        "timeedit_web": "",
        "canvas_base": "",
        "timeedit_help": "Zoek in je roostersysteem naar 'Abonneren', 'iCal' of 'Agenda-koppeling' en kopieer de .ics-link.",
        "canvas_help": "In Canvas: Agenda, dan 'Calendar Feed' rechtsonder.",
        "outlook_help": "Outlook Web: Instellingen, Agenda, Gedeelde agenda's, Een agenda publiceren, ICS-link kopiëren.",
    },
}


def _ctx(request: Request) -> dict:
    s = state.settings
    uni = UNIVERSITIES.get(s.university, UNIVERSITIES["other"])
    statuses = {r["source"]: r for r in state.db.statuses()}
    return {
        "s": s, "uni": uni, "universities": UNIVERSITIES, "active": state.active_names(),
        "statuses": statuses, "google_creds": s.google_credentials_file.exists(),
        "google_token": s.google_token_file.exists(), "google_job": google_job.status(),
        "data_dir": str(s.data_dir),
    }


@router.get("/setup", response_class=HTMLResponse)
def setup_page(request: Request):
    return render(request, "setup.html", _ctx(request))


@router.post("/setup/save", response_class=HTMLResponse)
async def setup_save(request: Request):
    form = await request.form()
    values = {k: str(form.get(k, "")).strip() for k in WIZARD_KEYS if k in form}
    if "UNIVERSITY" in values:
        uni = UNIVERSITIES.get(values["UNIVERSITY"])
        if uni and uni["timeedit_web"] and not values.get("TIMEEDIT_WEB_URL"):
            values["TIMEEDIT_WEB_URL"] = uni["timeedit_web"]
        if uni and uni["canvas_base"] and not values.get("CANVAS_BASE_URL"):
            values["CANVAS_BASE_URL"] = uni["canvas_base"]
    state.db.set_settings(values)
    await state.reload()
    return HTMLResponse('<span class="ok">✓ opgeslagen</span>', headers={"HX-Trigger": "saved"})


@router.post("/setup/test", response_class=HTMLResponse)
async def setup_test(request: Request, source: str = Form(...)):
    """Test één bron met de ingevulde (nog niet opgeslagen) waarden."""
    form = await request.form()
    overrides = {**state.db.get_settings(), **{k: str(form.get(k, "")).strip() for k in WIZARD_KEYS if k in form}}
    settings = build_settings(overrides)
    src = next((x for x in build_sources(settings) if x.name == source), None)
    if src is None:
        return HTMLResponse('<span class="err">✗ vul eerst de velden in</span>')
    try:
        import asyncio
        items = await asyncio.to_thread(src.fetch)
    except Exception as e:  # noqa: BLE001
        return HTMLResponse(f'<span class="err">✗ {type(e).__name__}: {str(e)[:160]}</span>')
    if not items:
        return HTMLResponse('<span class="warn">⚠ verbinding werkt, maar 0 items gevonden</span>')
    first = min((i for i in items if i.start or i.due), key=lambda i: i.start or i.due, default=items[0])
    return HTMLResponse(f'<span class="ok">✓ {len(items)} items gevonden, bijv. "{first.title[:60]}"</span>')


@router.post("/setup/done")
async def setup_done():
    state.db.set_settings({"SETUP_DONE": "1"})
    await state.reload()
    return RedirectResponse("/", status_code=303)


# ---------- Google koppelen vanuit de app ----------
class GoogleAuthJob:
    """Draait de OAuth-flow in een thread (opent de browser) en bewaart het resultaat."""

    def __init__(self) -> None:
        self._thread: threading.Thread | None = None
        self._error: str | None = None
        self._done = False

    def status(self) -> str:
        if self._thread and self._thread.is_alive():
            return "busy"
        if self._error:
            return f"error: {self._error}"
        return "done" if self._done else "idle"

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._error, self._done = None, False
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self) -> None:
        try:
            from google_auth_oauthlib.flow import InstalledAppFlow

            from .sources._google import SCOPES

            s = state.settings
            if not s.google_credentials_file.exists():
                raise FileNotFoundError(f"ontbreekt: {s.google_credentials_file}")
            flow = InstalledAppFlow.from_client_secrets_file(str(s.google_credentials_file), SCOPES)
            creds = flow.run_local_server(port=0, prompt="consent", open_browser=True, timeout_seconds=300)
            s.google_token_file.parent.mkdir(parents=True, exist_ok=True)
            s.google_token_file.write_text(creds.to_json())
            self._done = True
        except Exception as e:  # noqa: BLE001
            self._error = f"{type(e).__name__}: {str(e)[:200]}"
            log.warning("Google-koppeling mislukt: %s", self._error)


google_job = GoogleAuthJob()


@router.post("/setup/google", response_class=HTMLResponse)
def setup_google_start():
    google_job.start()
    return HTMLResponse('<span class="warn">⏳ browser geopend, log in en kom hier terug…</span>')


@router.get("/setup/google/status", response_class=HTMLResponse)
async def setup_google_status():
    st = google_job.status()
    if st == "busy":
        return HTMLResponse('<span class="warn">⏳ wachten op inloggen in de browser…</span>')
    if st.startswith("error"):
        return HTMLResponse(f'<span class="err">✗ {st[7:]}</span>')
    if st == "done":
        await state.reload()
        return HTMLResponse('<span class="ok">✓ Google gekoppeld (Gmail + Agenda)</span>', headers={"HX-Trigger": "saved"})
    if state.settings.google_token_file.exists():
        return HTMLResponse('<span class="ok">✓ Google is gekoppeld</span>')
    return HTMLResponse('<span class="muted">nog niet gekoppeld</span>')


@router.post("/setup/google/disconnect", response_class=HTMLResponse)
async def setup_google_disconnect():
    try:
        state.settings.google_token_file.unlink()
    except FileNotFoundError:
        pass
    await state.reload()
    return HTMLResponse('<span class="muted">Google ontkoppeld</span>', headers={"HX-Trigger": "saved"})


def _now() -> datetime:
    return datetime.now(state.settings.tz)
