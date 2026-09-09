# Lokale build (Windows, PowerShell): dist\Jarvis\Jarvis.exe
Set-Location (Split-Path $PSScriptRoot -Parent)
if (-not (Test-Path .venv)) { python -m venv .venv }
.\.venv\Scripts\pip install -q -r requirements-build.txt
.\.venv\Scripts\pyinstaller jarvis.spec --noconfirm
Write-Host "Klaar: dist\Jarvis\Jarvis.exe"
