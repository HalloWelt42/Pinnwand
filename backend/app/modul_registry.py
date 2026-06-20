"""Modul-Registry des Backends.

Module liegen unter ``backend/module/<id>/`` und beschreiben sich über eine
``manifest.json``. Die Registry findet sie per Verzeichnis-Scan, ruft ihren
Schema-Init-Hook auf, lädt ihren Router und aggregiert ihre
Erweiterungspunkte. So kommt neue Funktionalität ohne Änderung am Kern dazu.
"""
from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter

MODUL_VERZEICHNIS = Path(__file__).resolve().parent.parent / "module"

ERWEITERUNGSPUNKTE = ("views", "cardFields", "mappeTabs", "commands")


def lade_manifeste() -> list[dict[str, Any]]:
    manifeste: list[dict[str, Any]] = []
    for datei in sorted(MODUL_VERZEICHNIS.glob("*/manifest.json")):
        manifeste.append(json.loads(datei.read_text(encoding="utf-8")))
    return manifeste


def _aufgeloest(spezifikation: str | None) -> Any | None:
    """Löst einen Eintrag der Form ``modul.pfad:objekt`` zu Python-Objekt auf."""
    if not spezifikation:
        return None
    modulpfad, _, attribut = spezifikation.partition(":")
    modul = importlib.import_module(modulpfad)
    return getattr(modul, attribut)


def router_fuer(manifest: dict[str, Any]) -> APIRouter | None:
    return _aufgeloest(manifest.get("backend", {}).get("router"))


def init_fuer(manifest: dict[str, Any]) -> None:
    """Ruft den Schema-/Seed-Init-Hook eines Moduls auf, falls deklariert."""
    init = _aufgeloest(manifest.get("backend", {}).get("init"))
    if callable(init):
        init()


def mount_fuer(manifest: dict[str, Any]) -> tuple[str, Any] | None:
    """Liefert (Pfad, ASGI-App) eines Moduls, das eine Sub-App einhängen will.

    Erlaubt z.B. einen MCP-Server. Ist die App None (Feature abgeschaltet),
    wird nichts eingehängt - so bleiben solche Dienste optional.
    """
    spez = manifest.get("backend", {}).get("mount")
    if not isinstance(spez, dict):
        return None
    pfad = spez.get("path")
    app_obj = _aufgeloest(spez.get("app"))
    if not pfad or app_obj is None:
        return None
    return pfad, app_obj


def lifespan_fuer(manifest: dict[str, Any]):
    """Liefert einen async-Kontextmanager eines Moduls für Start/Stopp, falls deklariert."""
    fabrik = _aufgeloest(manifest.get("backend", {}).get("lifespan"))
    if callable(fabrik):
        return fabrik()
    return None


def aggregiere_erweiterungen() -> dict[str, list[dict[str, Any]]]:
    """Sammelt die deklarierten Erweiterungspunkte aller Module."""
    punkte: dict[str, list[dict[str, Any]]] = {p: [] for p in ERWEITERUNGSPUNKTE}
    for manifest in lade_manifeste():
        extends = manifest.get("extends", {})
        for punkt in ERWEITERUNGSPUNKTE:
            for eintrag in extends.get(punkt, []):
                punkte[punkt].append({"modul": manifest["id"], "wert": eintrag})
    return punkte
