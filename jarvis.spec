# PyInstaller-spec: één map (dist/Jarvis) met de app, templates en static.
# Bouwen: pyinstaller jarvis.spec   (op het platform waarvoor je bouwt)
import sys

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

hidden = (
    collect_submodules("uvicorn") + collect_submodules("app")
    + ["pystray._xorg", "pystray._appindicator", "pystray._win32", "pystray._darwin",
       "google.auth.transport.requests", "googleapiclient.discovery", "msal", "tzdata", "PIL"]
)
if sys.platform.startswith("linux"):
    # pywebview en pystray laden GTK pas tijdens het draaien; PyInstaller ziet dat niet vanzelf.
    hidden += ["gi", "gi.repository.Gtk", "gi.repository.Gdk", "gi.repository.GLib", "gi.repository.GObject",
               "gi.repository.Gio", "gi.repository.WebKit2", "gi.repository.Soup", "gi.repository.GdkPixbuf",
               "gi.repository.AyatanaAppIndicator3"]
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
