# PyInstaller-spec: één map (dist/Jarvis) met de app, templates en static.
# Bouwen: pyinstaller jarvis.spec   (op het platform waarvoor je bouwt)
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

hidden = (
    collect_submodules("uvicorn") + collect_submodules("app")
    + ["pystray._xorg", "pystray._appindicator", "pystray._win32", "pystray._darwin",
       "google.auth.transport.requests", "googleapiclient.discovery", "msal", "tzdata", "PIL"]
)
datas = [("templates", "templates"), ("static", "static"), (".env.example", ".")]
datas += collect_data_files("tzdata") + collect_data_files("googleapiclient", includes=["discovery_cache/documents/gmail.*", "discovery_cache/documents/calendar.*"])

a = Analysis(
    ["desktop.py"],
    pathex=["."],
    binaries=[],
    datas=datas,
    hiddenimports=hidden,
    excludes=["tkinter", "pytest"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="Jarvis",
    console=False,
    icon=None,
)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="Jarvis")
