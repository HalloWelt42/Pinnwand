"""Die Anwendung der Pinnwand: Rahmen jeder Änderung, Ereignisstrom und die Anwendungsfälle je Bereich, zusammengesetzt
für das Gerüst. Beim Start richtet der Begleiter das Schema ein und legt die mitgelieferten Vorlagen an."""

from __future__ import annotations

import json
from dataclasses import dataclass

from appkern.app import Begleiter
from appkern.datenbank import Datenbank

from ..uhr import Uhr
from ..verzeichnis import Verzeichnis, einrichten
from ..vorlagen import MITGELIEFERT
from .anhaenge import Ablage, Anhaenge
from .boards import Boards, Zugang
from .ereignisse import Ereignisse
from .inhalt import Inhalte
from .karten import Karten
from .konten import Konten
from .rahmen import Anwendung
from .stand import Abfragen


@dataclass
class Dienste:
    anwendung: Anwendung
    ereignisse: Ereignisse
    konten: Konten
    abfragen: Abfragen
    boards: Boards
    karten: Karten
    inhalte: Inhalte
    anhaenge: Anhaenge

    @classmethod
    def bauen(cls, db: Datenbank, zugang: Zugang, ablage: Ablage, uhr: Uhr | None = None) -> Dienste:
        ereignisse = Ereignisse()
        a = Anwendung(Verzeichnis(db), ereignisse, uhr)
        return cls(anwendung=a, ereignisse=ereignisse, konten=Konten(a), abfragen=Abfragen(a), boards=Boards(a, zugang),
                   karten=Karten(a), inhalte=Inhalte(a), anhaenge=Anhaenge(a, ablage))


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
