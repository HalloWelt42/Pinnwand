"""Die Anwendung der Pinnwand: Rahmen jeder Änderung, Ereignisstrom und die Anwendungsfälle je Bereich, zusammengesetzt
für das Gerüst. Beim Start richtet der Begleiter das Schema ein und legt die mitgelieferten Vorlagen an."""

from __future__ import annotations

import json
from dataclasses import dataclass

from appkern.app import Begleiter
from appkern.datenbank import Datenbank
from appkern.push import Push

from ..uhr import Uhr
from ..verzeichnis import Verzeichnis, einrichten
from ..vorlagen import MITGELIEFERT
from .anhaenge import Ablage, Anhaenge
from .arbeitszeit import Arbeitszeit
from .aufbau import Aufbau
from .berichte import Berichte
from .boards import Boards, Zugang
from .ereignisse import Ereignisse
from .hinweise import Hinweise
from .inhalt import Inhalte
from .karten import Karten
from .konten import Konten
from .mitglieder import Mitglieder
from .mitteilungen import Mitteilungen
from .ordner import Persoenliches
from .papierkorb import Papierkorb
from .rahmen import Anwendung
from .serien import Serien
from .stand import Abfragen
from .termine import Termine
from .zeiterfassung import Zeiterfassung


@dataclass
class Dienste:
    anwendung: Anwendung
    ereignisse: Ereignisse
    konten: Konten
    abfragen: Abfragen
    boards: Boards
    karten: Karten
    inhalte: Inhalte
    hinweise: Hinweise
    papierkorb: Papierkorb
    aufbau: Aufbau
    mitglieder: Mitglieder
    persoenlich: Persoenliches
    anhaenge: Anhaenge
    zeiterfassung: Zeiterfassung
    arbeitszeit: Arbeitszeit
    serien: Serien
    termine: Termine
    berichte: Berichte
    mitteilungen: Mitteilungen

    @classmethod
    def bauen(cls, db: Datenbank, zugang: Zugang, ablage: Ablage, uhr: Uhr | None = None, push: Push | None = None) -> Dienste:
        ereignisse = Ereignisse()
        a = Anwendung(Verzeichnis(db), ereignisse, uhr)
        konten = Konten(a)
        return cls(anwendung=a, ereignisse=ereignisse, konten=konten, abfragen=Abfragen(a), boards=Boards(a, zugang),
                   karten=Karten(a), inhalte=Inhalte(a), hinweise=Hinweise(a), papierkorb=Papierkorb(a), aufbau=Aufbau(a),
                   mitglieder=Mitglieder(a), persoenlich=Persoenliches(a), anhaenge=Anhaenge(a, ablage),
                   zeiterfassung=Zeiterfassung(a), arbeitszeit=Arbeitszeit(a), serien=Serien(a), termine=Termine(a),
                   berichte=Berichte(a, ablage), mitteilungen=Mitteilungen(a, push))


class Start(Begleiter):
    """Schema einrichten und die mitgelieferten Vorlagen anlegen oder auf den neuen Stand bringen."""

    def __init__(self, db: Datenbank) -> None:
        self.db = db

    async def starten(self) -> None:
        await einrichten(self.db)
        for v in MITGELIEFERT:
            await self.db.ausfuehren("INSERT INTO vorlagen (id, fassung, daten, konto) VALUES (?, 1, ?, NULL) "
                                     "ON CONFLICT(id) DO UPDATE SET daten=excluded.daten",
                                     (v.id, json.dumps(v.json_daten(), ensure_ascii=False)))
