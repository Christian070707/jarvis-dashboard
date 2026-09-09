@echo off
REM Windows: eerste keer maakt dit een venv en installeert alles; daarna start het Jarvis.
cd /d "%~dp0"
where python >nul 2>nul || (echo Python niet gevonden. Installeer Python 3.12+ via python.org en vink "Add to PATH" aan. & pause & exit /b 1)
if not exist .venv python -m venv .venv
call .venv\Scripts\pip install -q -r requirements.txt
if not exist .env copy .env.example .env >nul
echo Jarvis draait op http://127.0.0.1:8000  (sluit dit venster om te stoppen)
start "" http://127.0.0.1:8000
.venv\Scripts\uvicorn app.main:app --host 127.0.0.1 --port 8000
