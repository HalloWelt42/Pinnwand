"""Feiertags-Vorschau aus der gebuendelten Offline-Bibliothek.

Liefert Feiertage zu Land/Region/Jahr als Vorschau (nicht gespeichert). Die
Uebernahme erfolgt bewusst in einem zweiten Schritt (Vorschau vor Anwenden).
"""
from __future__ import annotations

try:
    import holidays

    _OK = True
except Exception:  # pragma: no cover
    _OK = False


def verfuegbar() -> bool:
    return _OK


def laender() -> dict:
    """Unterstuetzte Laender mit ihren Regionen (Subdivisionen)."""
    if not _OK:
        return {}
    out: dict[str, list[str]] = {}
    for land, regionen in holidays.list_supported_countries().items():
        out[land] = list(regionen)
    return out


def vorschau(land: str, region: str | None, jahr: int) -> list[dict]:
    """Feiertage als Vorschau. Jeder Eintrag traegt seine tatsaechliche Region:
    None = bundesweit, sonst der Subdivisions-Code (z.B. 'BY'). So koennen Personen
    spaeter nur die fuer ihr Bundesland geltenden Feiertage angerechnet bekommen.
    """
    if not _OK:
        return []
    try:
        h = holidays.country_holidays(land, subdiv=region or None, years=jahr)
    except Exception:
        return []
    bundesweit: set = set()
    if region:
        try:
            bundesweit = set(holidays.country_holidays(land, subdiv=None, years=jahr).keys())
        except Exception:
            bundesweit = set()
    out: list[dict] = []
    for d in sorted(h):
        reg = None if (not region or d in bundesweit) else region
        out.append({"datum": d.isoformat(), "name": h[d], "region": reg})
    return out
