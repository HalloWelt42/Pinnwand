"""Eine nachgestellte Kellerwolke für Tests und den Probebetrieb (tools/probebetrieb.py): drei Personen mit dem
Passwort "geheim", anna besitzt den App-Schlüssel, bert und cora dürfen erst nach einer Einladung."""

from __future__ import annotations

import json

import httpx

PERSONEN = {"anna": "1", "bert": "2", "cora": "3"}
PASSWORT = "geheim"
#: Einrichtung der App gegen diese Kellerwolke (Adresse und App-Schlüssel nur zum Schein)
EINRICHTUNG = {"kellerwolke_adresse": "http://kw.test", "kellerwolke_schluessel": "kw_app_x"}


def benutzer(name: str) -> dict:
    return {"id": PERSONEN[name], "name": name, "rolle": "mitglied", "aktiv": True}


def kellerwolke(request: httpx.Request) -> httpx.Response:
    pfad = request.url.path
    if pfad == "/api/v1/ablage/ich":
        return httpx.Response(200, json={"app": "Pinnwand", "konto": "anna", "rechte": []})
    if pfad == "/api/v1/auth/login":
        e = json.loads(request.content)
        if e["kennung"] not in PERSONEN or e["passwort"] != PASSWORT:
            return httpx.Response(401, json={"detail": "Anmeldung fehlgeschlagen"})
        return httpx.Response(200, json={"token": f"t-{e['kennung']}", "benutzer": benutzer(e["kennung"])})
    if pfad == "/api/v1/auth/status":
        name = (request.headers.get("x-kellerwolke-sitzung") or "").removeprefix("t-")
        ok = name in PERSONEN
        return httpx.Response(200, json={"angemeldet": ok, "benutzer": benutzer(name) if ok else None})
    if pfad.startswith("/api/v1/auth/"):
        return httpx.Response(200, json={})
    return httpx.Response(404, json={"detail": "nicht da"})
