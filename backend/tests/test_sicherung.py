"""Nachtsicherung: erst ab 3 Uhr, einmal je Nacht, eine lesbare Kopie, die jüngsten zehn bleiben."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from conftest import Zeiger

from app.sicherung import BEHALTEN, Nachtsicherung
from app.uhr import Uhr


def datenbank(pfad: Path) -> Path:
    v = sqlite3.connect(pfad)
    v.execute("CREATE TABLE karten (id TEXT)")
    v.execute("INSERT INTO karten VALUES ('c-1')")
    v.commit()
    v.close()
    return pfad


async def test_einmal_je_nacht(tmp_path: Path):
    zeiger = Zeiger(datetime(2026, 10, 27, 2, 30))
    s = Nachtsicherung(datenbank(tmp_path / "pinnwand.sqlite"), tmp_path / "sicherungen", "pinnwand", Uhr(zeiger))
    assert await s.pruefen() is None                                      # vor 3 Uhr noch nicht
    zeiger.zeit = datetime(2026, 10, 27, 3, 5, 9)
    kopie = await s.pruefen()
    assert kopie is not None and kopie.name == "pinnwand-20261027-030509.sqlite"
    assert sqlite3.connect(kopie).execute("SELECT id FROM karten").fetchall() == [("c-1",)]
    zeiger.zeit = datetime(2026, 10, 27, 23, 0)
    assert await s.pruefen() is None                                      # in derselben Nacht nur eine


async def test_die_juengsten_bleiben(tmp_path: Path):
    zeiger = Zeiger(datetime(2026, 10, 1, 4, 0))
    s = Nachtsicherung(datenbank(tmp_path / "pinnwand.sqlite"), tmp_path / "sicherungen", "pinnwand", Uhr(zeiger))
    for _ in range(BEHALTEN + 3):
        assert await s.pruefen() is not None
        zeiger.zeit += timedelta(days=1)
    namen = sorted(k.name for k in (tmp_path / "sicherungen").iterdir())
    assert len(namen) == BEHALTEN and namen[0] == "pinnwand-20261004-040000.sqlite"
