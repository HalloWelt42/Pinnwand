"""Probebetrieb: das Backend mit der nachgestellten Kellerwolke und Leitstelle der Tests (backend/tests/nachgestellt.py),
eingerichtet und bereit zum Anmelden als anna, bert oder cora (Passwort "geheim"); die Leitstelle antwortet mit
Beispielen in der verlangten Form, die Transkription hat ein Telefonat (cora darf sie nicht nutzen). Für die Prüfung der echten Oberfläche ohne echte
Zugangsdaten; die Daten liegen in einem eigenen Ordner.

    backend/.venv/bin/python tools/probebetrieb.py --daten <ordner> [--port 8420]
"""

from __future__ import annotations

import argparse
import sys
import threading
import time
from pathlib import Path

import httpx
import uvicorn

BACKEND = Path(__file__).resolve().parents[1] / "backend"
sys.path[:0] = [str(BACKEND), str(BACKEND / "tests")]

from app.main import app_bauen  # noqa: E402
from nachgestellt import EINRICHTUNG, LEITSTELLE_EINRICHTUNG, PASSWORT, TRANSKRIPTION_EINRICHTUNG, kellerwolke  # noqa: E402


def main() -> None:
    a = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    a.add_argument("--daten", type=Path, required=True)
    a.add_argument("--port", type=int, default=8420)
    args = a.parse_args()
    app = app_bauen(args.daten, transport=httpx.MockTransport(kellerwolke))
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=args.port, log_level="warning"))
    t = threading.Thread(target=server.run, daemon=True)
    t.start()
    basis = f"http://127.0.0.1:{args.port}/api/v1"
    for _ in range(100):
        try:
            if httpx.get(f"{basis}/app").json().get("einrichtung_noetig"):
                httpx.post(f"{basis}/einrichtung", json=EINRICHTUNG).raise_for_status()
            token = httpx.post(f"{basis}/anmeldung", json={"kennung": "anna", "passwort": PASSWORT}).json()["token"]
            httpx.patch(f"{basis}/einstellungen", headers={"X-Kellerwolke-Sitzung": token},
                        json={"werte": LEITSTELLE_EINRICHTUNG | TRANSKRIPTION_EINRICHTUNG}).raise_for_status()
            break
        except httpx.HTTPError:
            time.sleep(0.1)
    print(f"Probebetrieb bereit auf {basis} (Daten: {args.daten})", flush=True)
    t.join()


if __name__ == "__main__":
    main()
