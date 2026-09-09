"""Jarvis als desktop-app: start de server op een vrije poort en opent een venster (of de browser).

Gebruik:  python desktop.py            venster + tray-icoon
          python desktop.py --browser  alleen server + systeembrowser (handig zonder WebView)
"""
from __future__ import annotations

import logging
import os
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path

APP_NAME = "Jarvis"


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def wait_for(host: str, port: int, timeout: float = 20) -> bool:
    end = time.time() + timeout
    while time.time() < end:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.15)
    return False


def main() -> int:
    port = int(os.environ.get("DASHBOARD_PORT") or free_port())
    os.environ["DASHBOARD_PORT"] = str(port)
    os.environ.setdefault("DASHBOARD_HOST", "127.0.0.1")

    from app.config import DATA_DIR  # bepaalt ook de datamap (per gebruiker bij een ingepakte app)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(DATA_DIR / "jarvis.log", encoding="utf-8"), logging.StreamHandler()],
    )
    log = logging.getLogger("desktop")

    import uvicorn

    from app.main import app

    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="info")
    server = uvicorn.Server(config)
    threading.Thread(target=server.run, name="uvicorn", daemon=True).start()
    if not wait_for("127.0.0.1", port):
        log.error("server kwam niet op binnen 20 s")
        return 1
    url = f"http://127.0.0.1:{port}/"
    log.info("%s draait op %s (data: %s)", APP_NAME, url, DATA_DIR)

    def shutdown() -> None:
        server.should_exit = True

    def run_in_browser() -> int:
        webbrowser.open(url)
        print(f"{APP_NAME} draait op {url}  (Ctrl+C om te stoppen)")
        try:
            while not server.should_exit:
                time.sleep(0.5)
        except KeyboardInterrupt:
            shutdown()
        return 0

    if "--browser" in sys.argv:
        return run_in_browser()
    try:
        import webview  # type: ignore

        window = webview.create_window(APP_NAME, url, width=1500, height=950, min_size=(900, 600))
    except Exception as e:  # noqa: BLE001
        log.warning("geen app-venster mogelijk (%s); open in de browser", e)
        return run_in_browser()

    # Tray-icoon (optioneel; pystray kan ontbreken of geen backend hebben)
    tray = None
    try:
        import pystray
        from PIL import Image, ImageDraw

        def icon_image() -> "Image.Image":
            img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
            d = ImageDraw.Draw(img)
            d.ellipse((2, 2, 62, 62), fill=(11, 18, 32, 255))
            d.ellipse((10, 10, 54, 54), outline=(55, 210, 255, 255), width=5)
            d.ellipse((26, 26, 38, 38), fill=(191, 245, 255, 255))
            return img

        def on_open(*_):
            try:
                window.show()
                window.restore()
            except Exception:  # noqa: BLE001
                webbrowser.open(url)

        def on_quit(*_):
            shutdown()
            try:
                tray.stop()
            finally:
                window.destroy()

        tray = pystray.Icon(APP_NAME, icon_image(), APP_NAME, pystray.Menu(
            pystray.MenuItem("Openen", on_open, default=True),
            pystray.MenuItem("In browser openen", lambda *_: webbrowser.open(url)),
            pystray.MenuItem("Afsluiten", on_quit),
        ))
        tray.run_detached()
    except Exception as e:  # noqa: BLE001
        log.info("geen tray-icoon: %s", e)

    def on_closed():
        shutdown()
        if tray:
            try:
                tray.stop()
            except Exception:  # noqa: BLE001
                pass

    window.events.closed += on_closed
    try:
        webview.start()
    except Exception as e:  # noqa: BLE001
        # Geen GTK/QT/WebView2 beschikbaar: niet crashen, maar in de browser openen.
        log.warning("app-venster kon niet starten (%s); open in de browser", e)
        if tray:
            try:
                tray.stop()
            except Exception:  # noqa: BLE001
                pass
        return run_in_browser()
    shutdown()
    return 0


if __name__ == "__main__":
    if getattr(sys, "frozen", False):
        os.chdir(Path(sys.executable).parent)
    sys.exit(main())
