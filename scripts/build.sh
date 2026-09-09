#!/usr/bin/env bash
# Lokale build (Linux/Mac): dist/Jarvis/Jarvis
set -e
cd "$(dirname "$0")/.."
.venv/bin/pip install -q -r requirements-build.txt
.venv/bin/pyinstaller jarvis.spec --noconfirm
echo "Klaar: dist/Jarvis/"
