# Jarvis

Eén pagina met rooster (TimeEdit), agenda's (Google, Outlook), deadlines (Canvas, Trello),
ongelezen mail (Gmail, Outlook), wekkers (Android) en een eigen takenlijst. Elk item linkt door
naar de bron. Draait lokaal op `http://127.0.0.1:8000`.

## Starten
Linux/Mac: `./start.sh` — Windows: dubbelklik `start.bat` (Python 3.12+ vereist).
Het script maakt een venv, installeert alles en opent `http://127.0.0.1:8000`.
Vul daarna `.env` in (wordt aangemaakt uit `.env.example`); leeg = bron uit.

Handmatig:
```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env
.venv/bin/uvicorn app.main:app --reload
```
Tests: `.venv/bin/pytest`

## Bronnen koppelen (in volgorde van moeite)
| Bron | Wat je nodig hebt | Waar |
|---|---|---|
| TimeEdit | iCal-abonnementslink | cloud.timeedit.net/nl_utwente/web → je rooster → Abonneren |
| Google Calendar | privé iCal-URL (of later OAuth) | Google Calendar → Instellingen → agenda → "Privéadres in iCal-formaat" |
| Canvas agenda | Calendar Feed-URL | canvas.utwente.nl → Agenda → "Calendar Feed" |
| Outlook agenda | gepubliceerde ICS-link | outlook.office.com → Instellingen → Agenda → Gedeelde agenda's → Publiceren |
| Trello | API key + token + board-id | trello.com/power-ups/admin |
| Canvas API | persoonlijk toegangstoken | Canvas → Account → Instellingen → Nieuw toegangstoken |
| Gmail + Google Calendar API | OAuth-token | `scripts/google_auth.py` (zie docstring) |
| Outlook mail/To Do (UT) | Entra app + device-login | `scripts/ms_auth.py` (zie docstring; kan door UT geblokkeerd zijn) |
| Wekkers | MacroDroid/Tasker-macro | `scripts/macrodroid_alarm.md` |

Status per bron staat bovenin de pagina (klik op een pil om die bron te verversen) en op `/api/status`.

## Autostart
`cp scripts/dashboard.service ~/.config/systemd/user/ && systemctl --user enable --now dashboard`
