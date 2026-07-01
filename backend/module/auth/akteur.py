"""Der handelnde Nutzer einer UI-Sitzung als typisiertes Objekt.

Spiegelt das Akteur-Muster der Agenten-API (module/agent_api/auth.py) fuer die
menschliche Anmeldung: eine Sitzung wird zu einem Akteur mit Rolle aufgeloest.
Bei deaktiviertem Login gibt es einen offenen Akteur mit Vollzugriff, damit der
passwortlose Modus unveraendert offen bleibt.

Feinberechtigungen, die vom Zielobjekt abhaengen (wessen Urlaub? wessen Zeiteintrag?),
werden ueber diesen Akteur in den Endpunkten geprueft (siehe rechte.py) - die
Middleware (dienst.zugriff_pruefen) bleibt der Grobfilter fuer rein-globale Bereiche.
"""
from __future__ import annotations

from dataclasses import dataclass

from fastapi import Header, HTTPException

from module.planung import persistence as planung

from . import dienst
from . import persistence as db


@dataclass(frozen=True)
class Akteur:
    """Ein authentifizierter UI-Nutzer mit seiner Rolle."""

    person_id: str | None
    kuerzel: str | None
    rolle: str

    @property
    def ist_admin(self) -> bool:
        return self.rolle == "admin"

    @classmethod
    def offen(cls) -> "Akteur":
        """Vollzugriff-Akteur fuer den passwortlosen Modus (kein aktiver Login)."""
        return cls(person_id=None, kuerzel=None, rolle="admin")

    @classmethod
    def aus_person(cls, person: dict) -> "Akteur":
        return cls(
            person_id=person["id"],
            kuerzel=person.get("kuerzel"),
            rolle=person.get("rolle", "mitarbeiter"),
        )


def aktueller_akteur(x_pinnwand_sitzung: str | None = Header(default=None)) -> Akteur:
    """FastAPI-Abhaengigkeit: loest die Sitzung zum handelnden Nutzer auf.

    Ohne aktiven Login ist alles offen -> offener Akteur. Bei aktivem Login muss
    eine gueltige Sitzung vorliegen, sonst 401 (Backstop; geschuetzte Pfade fangt
    die Middleware ohnehin schon ab).
    """
    if not dienst.login_aktiv():
        return Akteur.offen()
    person_id = db.sitzung_person(x_pinnwand_sitzung) if x_pinnwand_sitzung else None
    person = planung.hole_person(person_id) if person_id else None
    if person is None:
        raise HTTPException(status_code=401, detail="Anmeldung erforderlich")
    return Akteur.aus_person(person)
