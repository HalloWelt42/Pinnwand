"""Einstellungen von Pinnwand. Kellerwolke, Leitstelle und weitere Konten bringt das Gerüst mit; eigene Felder kommen
hier dazu (mit `Field(title=..., description=...)`, Auswahl über `Literal`, Geheimnisse als `SecretStr`). Die Seite
Einstellungen der Oberfläche entsteht daraus von selbst."""

from pydantic import Field

from appkern.app import Grundeinstellungen
from appkern.app.einstellungen import VERBINDUNGEN
from appkern.vorlesen import VorlesenEinstellungen

KI = {"gruppe": "KI an der Karte"}


class AppEinstellungen(Grundeinstellungen, VorlesenEinstellungen):
    transkription_adresse: str = Field("", title="Transkription", json_schema_extra=VERBINDUNGEN,
                                       description="Adresse der Transkription: Transkripte an Karten, Abspielen ab der "
                                                   "Stelle und die Spracheingabe beim Erfassen. Leer: ohne "
                                                   "Transkripte und Spracheingabe.")
    ki_modell: str = Field("", title="Modell", json_schema_extra=KI,
                           description="Textmodell der Leitstelle für Zusammenfassung, Checkliste, Labels und Karten aus "
                                       "Text. Leer: die Leitstelle wählt nach der Kette der App.")
