"""Die Uhr der Pinnwand: Ortszeit als ISO ohne Zone, wie die Oberfläche sie rechnet (Tage "2026-10-27", Zeitpunkte
"2026-10-27T10:42:00"). Die Zone kommt aus TZ oder /etc/localtime; Tests setzen eine feste Uhr ein."""

from __future__ import annotations

import functools
import os
from collections.abc import Callable
from datetime import datetime, tzinfo
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


@functools.cache
def ortszone() -> tzinfo:
    name = os.environ.get("TZ", "").lstrip(":")
    if name:
        try:
            return ZoneInfo(name)
        except (ZoneInfoNotFoundError, ValueError):
            pass
    try:
        with open("/etc/localtime", "rb") as f:
            return ZoneInfo.from_file(f, key="localtime")
    except (OSError, ValueError):
        return datetime.now().astimezone().tzinfo or ZoneInfo("UTC")


class Uhr:
    """`jetzt()` als "JJJJ-MM-TTTHH:MM:SS" in Ortszeit, `heute()` als "JJJJ-MM-TT"."""

    def __init__(self, quelle: Callable[[], datetime] | None = None) -> None:
        self._quelle = quelle or (lambda: datetime.now(ortszone()))

    def jetzt(self) -> str:
        return self._quelle().replace(microsecond=0, tzinfo=None).isoformat()

    def heute(self) -> str:
        return self.jetzt()[:10]
