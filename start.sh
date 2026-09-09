#!/usr/bin/env bash
# Linux/Mac: eerste keer maakt dit een venv en installeert alles; daarna start het Jarvis.
set -e
cd "$(dirname "$0")"
[ -d .venv ] || python3 -m venv .venv
.venv/bin/pip install -q -r requirements.txt
[ -f .env ] || cp .env.example .env
echo "Jarvis draait op http://127.0.0.1:8000  (Ctrl+C om te stoppen)"
exec .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
