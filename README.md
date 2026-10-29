# Jarvis

One page with your timetable (TimeEdit), calendars (Google, Outlook), deadlines (Canvas, Trello),
unread mail (Gmail, Outlook), alarms (Android) and your own to-do list. Every item links back
to its source. Runs locally on `http://127.0.0.1:8000`.

> The interface is currently in Dutch, and some sources (TimeEdit, Canvas) are preconfigured
> for the University of Twente, but any iCal feed or Canvas instance works.

## Getting started

**As an app (recommended)**: download the latest release for your system from
[Releases](../../releases), extract it and run `Jarvis` (Windows: `Jarvis.exe`). The setup
wizard opens on first launch. On first launch Windows shows a blue SmartScreen dialog
("Unknown Publisher" or "SmartScreen can't be reached") because the app is not code-signed.
Click "More info" and then "Run anyway", or "Run" directly. On Linux, Jarvis opens in your
browser (`./Jarvis --window` tries to open its own window). Your data is stored in your user
folder (Windows: `%APPDATA%\Jarvis`, Linux: `~/.local/share/Jarvis`,
Mac: `~/Library/Application Support/Jarvis`).

**From source**: Linux/Mac `./start.sh`, Windows double-click `start.bat` (Python 3.12+).
The script creates a venv, installs everything and opens `http://127.0.0.1:8000`. Go to
`/setup` (⚙ on the dashboard) to connect sources; `.env` is optional and serves as a fallback.

**Desktop window from source**: `pip install -r requirements-build.txt` and `python desktop.py`
(or `python desktop.py --browser` without a window).

Manually:
```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env
.venv/bin/uvicorn app.main:app --reload
```
Tests: `.venv/bin/pytest`

## Connecting sources (easiest first)
Detailed step-by-step instructions per source, including troubleshooting (in Dutch):
[docs/KOPPELEN.md](docs/KOPPELEN.md).

| Source | What you need | Where |
|---|---|---|
| TimeEdit | iCal subscription link | cloud.timeedit.net/nl_utwente/web → your timetable → Subscribe |
| Google Calendar | secret iCal URL (or OAuth) | Google Calendar → Settings → calendar → "Secret address in iCal format" |
| Canvas calendar | Calendar Feed URL | canvas.utwente.nl → Calendar → "Calendar Feed" |
| Outlook calendar | published ICS link | outlook.office.com → Settings → Calendar → Shared calendars → Publish |
| Trello | API key + token + board ID | trello.com/power-ups/admin |
| Canvas API | personal access token | Canvas → Account → Settings → New access token |
| Gmail + Google Calendar API | OAuth token | `scripts/google_auth.py` (see docstring) |
| Outlook mail/To Do | Entra app + device login | `scripts/ms_auth.py` (see docstring; may be blocked by your organisation) |
| Alarms | MacroDroid/Tasker macro | `scripts/macrodroid_alarm.md` |

The status of each source is shown at the top of the page (click a pill to refresh that source)
and at `/api/status`.

## Building
`scripts/build.sh` (Linux/Mac) or `scripts/build_windows.ps1` (Windows) produces `dist/Jarvis/`.
GitHub Actions builds for Windows, Linux and Mac on every push; a `v*` tag creates a release.

## Autostart (Linux, without the app)
`cp scripts/dashboard.service ~/.config/systemd/user/ && systemctl --user enable --now dashboard`
