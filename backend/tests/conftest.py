"""Vorrichtung der Tests: die Pinnwand gegen eine nachgestellte Kellerwolke mit drei Personen (anna besitzt den
App-Schlüssel, bert und cora dürfen erst nach einer Einladung), feste Uhr, Anmeldung je Person."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import httpx
import pytest

from app.main import app_bauen
from app.uhr import Uhr
from nachgestellt import EINRICHTUNG, PASSWORT, kellerwolke

@dataclass
class Zeiger:
    """Die feste Uhr der Tests; `zeit` lässt sich vorstellen."""

    zeit: datetime = field(default_factory=lambda: datetime(2026, 10, 27, 10, 0))

    def __call__(self) -> datetime:
        return self.zeit


@dataclass
class Pinnwand:
    c: httpx.AsyncClient
    app: object
    zeiger: Zeiger
    kopf: dict[str, dict[str, str]] = field(default_factory=dict)

    async def anmelden(self, name: str) -> httpx.Response:
        r = await self.c.post("/api/v1/anmeldung", json={"kennung": name, "passwort": PASSWORT})
        if r.status_code == 200:
            self.kopf[name] = {"X-Kellerwolke-Sitzung": r.json()["token"]}
        return r

    async def get(self, wer: str, pfad: str, **kw) -> httpx.Response:
        return await self.c.get(f"/api/v1{pfad}", headers=self.kopf[wer], **kw)

    async def post(self, wer: str, pfad: str, daten: dict | None = None) -> httpx.Response:
        return await self.c.post(f"/api/v1{pfad}", headers=self.kopf[wer], json=daten or {})

    async def stand(self, wer: str) -> dict:
        r = await self.get(wer, "/stand")
        assert r.status_code == 200, r.text
        return r.json()

    async def board(self, wer: str, name: str = "Haushalt", kuerzel: str = "HAUS", vorlage: str = "v-aufgaben",
                    **mehr) -> dict:
        """Legt ein Board an und gibt es aus dem neuen Stand zurück."""
        r = await self.post(wer, "/boards", {"vorlage": vorlage, "name": name, "kuerzel": kuerzel, **mehr})
        assert r.status_code == 200, r.text
        return next(b for b in (await self.stand(wer))["boards"] if b["kuerzel"] == kuerzel)

    async def karte(self, wer: str, board: dict, titel: str, spalte: str | None = None, **mehr) -> dict:
        r = await self.post(wer, f"/boards/{board['id']}/karten", {"titel": titel, "spalte": spalte, **mehr})
        assert r.status_code == 200, r.text
        return next(g["daten"] for g in r.json()["geaendert"] if g["tabelle"] == "karten")


@pytest.fixture
async def pw(tmp_path: Path):
    """Eingerichtet, anna angemeldet."""
    zeiger = Zeiger()
    app = app_bauen(tmp_path / "daten", transport=httpx.MockTransport(kellerwolke), uhr=Uhr(zeiger))
    await app.state.geruest.starten()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as c:
        r = await c.post("/api/v1/einrichtung", json=EINRICHTUNG)
        assert r.status_code == 200, r.text
        p = Pinnwand(c, app, zeiger)
        assert (await p.anmelden("anna")).status_code == 200
        yield p
    await app.state.geruest.stoppen()
