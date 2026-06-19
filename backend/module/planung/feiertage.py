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


# Lesbare Namen der deutschen Bundeslaender (die Bibliothek liefert nur Codes).
_DE_NAMEN = {
    "BW": "Baden-Württemberg", "BY": "Bayern", "BE": "Berlin", "BB": "Brandenburg",
    "HB": "Bremen", "HH": "Hamburg", "HE": "Hessen", "MV": "Mecklenburg-Vorpommern",
    "NI": "Niedersachsen", "NW": "Nordrhein-Westfalen", "RP": "Rheinland-Pfalz",
    "SL": "Saarland", "SN": "Sachsen", "ST": "Sachsen-Anhalt",
    "SH": "Schleswig-Holstein", "TH": "Thüringen",
}


def _region_name(land: str, code: str) -> str:
    if land == "DE":
        return _DE_NAMEN.get(code, code)
    return code


def laender() -> dict:
    """Unterstuetzte Laender mit ihren Regionen als {code, name}.

    Fuer Deutschland werden die ausgeschriebenen Bundesland-Namen geliefert; fuer
    andere Laender bleibt der Code als Name stehen.
    """
    if not _OK:
        return {}
    out: dict[str, list[dict]] = {}
    for land, regionen in holidays.list_supported_countries().items():
        out[land] = [{"code": r, "name": _region_name(land, r)} for r in regionen]
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
