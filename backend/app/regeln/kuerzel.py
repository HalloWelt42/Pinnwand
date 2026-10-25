"""Regeln der Kürzel als reine Funktionen, gleich frontend/src/regeln/kuerzel.ts: Kürzel eines Boards (2 bis 6 Zeichen,
vorne ein Buchstabe, Vorschlag aus dem Namen, Umlaute ausgeschrieben) und das Kürzel einer Person."""

from __future__ import annotations

import re
from collections.abc import Callable

UMLAUTE = {"Ä": "AE", "Ö": "OE", "Ü": "UE"}
KUERZEL_LAENGE = 6
KUERZEL_MUSTER = re.compile(r"^[A-Z][A-Z0-9]{1,5}$")

#: Wem ein Kürzel gehört: Name eines sichtbaren Boards, "" für ein fremdes, None für niemanden
Inhaber = Callable[[str], "str | None"]


def ausschreiben(text: str) -> str:
    return re.sub("[ÄÖÜ]", lambda m: UMLAUTE[m.group(0)], text.upper())


def kuerzel_saeubern(eingabe: str) -> str:
    return re.sub("[^A-Z0-9]", "", ausschreiben(eingabe))[:KUERZEL_LAENGE]


def grundform(name: str) -> str:
    w = [x for x in re.split("[^A-Z0-9]+", ausschreiben(name)) if x]
    if not w:
        return ""
    k = w[0][:4] if len(w) == 1 else "".join(x if x.isdigit() else x[0] for x in w[:4])[:KUERZEL_LAENGE]
    if len(k) < 2:
        k = w[0][:4]
    return ("B" + k)[:KUERZEL_LAENGE] if k[:1].isdigit() else k


def abwandlungen(k: str, inhaber: Inhaber) -> list[str]:
    frei: list[str] = []
    for n in range(2, 10):
        if len(frei) >= 3:
            break
        v = k[:KUERZEL_LAENGE - 1] + str(n)
        if inhaber(v) is None:
            frei.append(v)
    return frei


def kuerzel_vorschlag(name: str, inhaber: Inhaber) -> str:
    k = grundform(name)
    if not k or inhaber(k) is None:
        return k
    return (abwandlungen(k, inhaber) or [k])[0]


def kuerzel_fehler(k: str, inhaber: Inhaber) -> str | None:
    """Grund, warum ein Kürzel nicht geht, sonst None."""
    if not k:
        return "Ein Kürzel braucht jedes Board, es steht vor jeder Kartennummer."
    if not KUERZEL_MUSTER.match(k):
        return "2 bis 6 Zeichen, vorne ein Buchstabe."
    wer = inhaber(k)
    if wer is not None:
        return f"{k} ist schon vergeben" + (f", an das Board {wer}." if wer else ", an ein Board, das du nicht siehst.")
    return None


def person_kuerzel(name: str) -> str:
    """Kürzel einer Person aus ihrem Namen: Anfänge von Vor- und Nachname (Umlaute ausgeschrieben)."""
    w = [x for x in re.split("[^A-Z]+", ausschreiben(name)) if x]
    if len(w) > 1:
        return w[0][0] + w[-1][0]
    return (w[0] if w else "?")[:2] or "?"
