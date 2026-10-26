"""Einstellungen von Pinnwand. Kellerwolke, Leitstelle und weitere Konten bringt das Gerüst mit; eigene Felder kommen
hier dazu (mit `Field(title=..., description=...)`, Auswahl über `Literal`, Geheimnisse als `SecretStr`). Die Seite
Einstellungen der Oberfläche entsteht daraus von selbst."""

from pydantic import Field

from appkern.app import Grundeinstellungen
from appkern.app.einstellungen import VERBINDUNGEN

KI = {"gruppe": "KI an der Karte"}
VORLESEN = {"gruppe": "Vorlesen"}


class AppEinstellungen(Grundeinstellungen):
    transkription_adresse: str = Field("", title="Transkription", json_schema_extra=VERBINDUNGEN,
                                       description="Adresse der Transkription: Transkripte an Karten, Abspielen ab der "
                                                   "Stelle und die Spracheingabe beim Erfassen. Leer: ohne "
                                                   "Transkripte und Spracheingabe.")
    vertonung_adresse: str = Field("", title="Vertonung", json_schema_extra=VERBINDUNGEN,
                                   description="Adresse der Vertonung: Vorlesen an Karten, in Heute und bei Berichten. "
                                               "Leer: ohne Vorlesen.")
    vorlesen_stimme: str = Field("", title="Stimme", json_schema_extra=VORLESEN,
                                 description="Stimme der Vertonung: aus ihrem Katalog oder eine private Stimme, die die "
                                             "Vertonung der Pinnwand freigibt. Leer: die Vorgabe der Vertonung.")
    vorlesen_tempo: float = Field(1.0, ge=0.5, le=2.0, title="Tempo", json_schema_extra={**VORLESEN, "schritt": 0.05},
                                  description="1 ist das gewohnte Tempo; kleiner liest langsamer, größer schneller.")
    ki_modell: str = Field("", title="Modell", json_schema_extra=KI,
                           description="Textmodell der Leitstelle für Zusammenfassung, Checkliste, Labels und Karten aus "
                                       "Text. Leer: die Leitstelle wählt nach der Kette der App.")
