"""Anmelde-Logik: Login/Logout, Status, Login-Modus und Zugriffspruefung.

Die Identitaet ist eine Person (planung). Bei aktivem Login identifiziert eine
Sitzung den Nutzer serverseitig; daraus folgt die Rolle und damit die echte
Durchsetzung der Admin-Bereiche. Ohne aktiven Login verhaelt sich alles wie
bisher (passwortlos, reines UI-Scoping).
"""
from __future__ import annotations

import os

from module.planung import persistence as planung

from . import persistence as db
from .models import AuthStatus

_LOGIN_KEY = "login_erforderlich"

# Schreibende Methoden, fuer die Admin-Bereiche durchgesetzt werden.
_SCHREIB = ("POST", "PATCH", "PUT", "DELETE")

# Pfade, die ohne Sitzung erreichbar bleiben muessen (Anmeldung selbst, Health).
_FREI = ("/api/health", "/api/auth/login", "/api/auth/status", "/api/auth/logout")


def login_aktiv() -> bool:
    """Ist die Anmeldung aktuell erforderlich? Notausgang ueber Umgebungsvariable."""
    if os.environ.get("PINNWAND_LOGIN_AUS", "").strip():
        return False
    return db.hole_einstellung(_LOGIN_KEY) == "1"


def setze_login_modus(erforderlich: bool) -> tuple[bool, str]:
    """Aktiviert/deaktiviert die Anmeldepflicht. Schuetzt vor Aussperren."""
    if erforderlich and not planung.hat_admin_mit_passwort():
        return False, "Vor dem Aktivieren muss mindestens eine Admin-Person ein Passwort haben."
    db.setze_einstellung(_LOGIN_KEY, "1" if erforderlich else "0")
    return True, ""


def login(kennung: str, passwort: str) -> str | None:
    """Prueft Name/Kuerzel + Passwort und gibt bei Erfolg einen Sitzungs-Token zurueck."""
    person = planung.pruefe_anmeldung(kennung, passwort)
    if person is None:
        return None
    return db.erstelle_sitzung(person["id"])


def logout(token: str) -> None:
    db.loesche_sitzung(token)


def status(token: str) -> AuthStatus:
    erforderlich = login_aktiv()
    person = planung.hole_person(db.sitzung_person(token) or "") if token else None
    if person is None:
        return AuthStatus(erforderlich=erforderlich, angemeldet=False)
    return AuthStatus(
        erforderlich=erforderlich,
        angemeldet=True,
        person_id=person["id"],
        name=person["name"],
        kuerzel=person.get("kuerzel"),
        rolle=person.get("rolle", "mitarbeiter"),
    )


# Rein-globale Bereiche, deren Admin-Pflicht schon am Pfad (ohne Kenntnis des
# Zielobjekts) feststeht. methoden=None bedeutet "alle Methoden".
# Zielbezogene Rechte (self-or-admin fuer persoenliche Planung, Eigentum an
# Zeiteintraegen) sind hier bewusst NICHT enthalten - sie pruefen die Endpunkte
# selbst ueber den Akteur (akteur.py/rechte.py), weil das Ziel erst dort bekannt ist.
_ADMIN_REGELN: tuple[tuple[tuple[str, ...] | None, str], ...] = (
    (None, "/api/backup"),                          # Backup/Restore komplett
    (None, "/api/auth/login-modus"),                # Anmeldepflicht schalten
    (_SCHREIB, "/api/planung/abwesenheitstypen"),   # globale Abwesenheits-Konfig
    (_SCHREIB, "/api/planung/feiertage"),           # globaler Feiertags-Import/-Loesch
    (_SCHREIB, "/api/kanban/labels"),               # globale Label-Verwaltung
    (_SCHREIB, "/api/kanban/einstellungen"),        # globale Kanban-Einstellungen
)


def _admin_only(method: str, pfad: str) -> bool:
    for methoden, praefix in _ADMIN_REGELN:
        if methoden is not None and method not in methoden:
            continue
        if pfad == praefix or pfad.startswith(praefix + "/"):
            return True
    return False


def zugriff_pruefen(method: str, pfad: str, token: str) -> int:
    """0 = ok, sonst HTTP-Status (401/403). Greift nur bei aktivem Login.

    Die Agenten-API (/api/agent) und /mcp haben eigene Token-Pruefungen und werden
    hier nicht zusaetzlich verlangt; Anmelde- und Health-Pfade bleiben frei.
    """
    if not login_aktiv() or method == "OPTIONS":
        return 0
    if not pfad.startswith("/api/"):
        return 0
    if pfad in _FREI or pfad.startswith("/api/agent/"):
        return 0
    person_id = db.sitzung_person(token)
    if not person_id:
        return 401
    if _admin_only(method, pfad):
        person = planung.hole_person(person_id)
        if not person or person.get("rolle") != "admin":
            return 403
    return 0
