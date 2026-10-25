"""Das Fachmodell der Pinnwand, gleich dem der Oberfläche (frontend/src/modell.ts): dieselben Namen, im JSON in
derselben Schreibweise (camelCase über den Alias). Was sich aus anderen Werten ergibt, steht nicht darin, sondern wird
gerechnet."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

Kennung = str
Farbe = Literal["tuerkis", "minze", "honig", "petrol", "rose", "koralle", "sand", "himmel", "flieder", "violett", "stahl"]
Zeitfenster = Literal["heute", "gestern", "woche", "monat", "jahr", "alle"]
FeldArt = Literal["text", "zahl", "datum", "auswahl", "verweis"]
ModulKennung = Literal["zeiterfassung", "arbeitszeit", "serien", "berichte", "transkripte", "vorlesen", "ki"]
Prioritaet = Literal["keine", "niedrig", "mittel", "hoch", "dringend"]
HinweisArt = Literal["zugewiesen", "faellig", "erwaehnt", "termin", "kommentar", "verschoben"]
HinweisWeg = Literal["pinnwand", "push", "assistent"]
MODULE: tuple[str, ...] = ("zeiterfassung", "arbeitszeit", "serien", "berichte", "transkripte", "vorlesen", "ki")
#: Module, die diese Fassung der Pinnwand anbietet; die übrigen lassen sich in keinem Board einschalten
MODULE_DA: tuple[str, ...] = ("zeiterfassung", "arbeitszeit")
Kartenart = Literal["arbeit", "idee"]


class Modell(BaseModel):
    """Grundlage aller Modelle: Python schreibt snake_case, JSON trägt camelCase wie die Oberfläche."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="ignore")

    def json_daten(self) -> dict:
        return self.model_dump(by_alias=True, exclude_none=True, mode="json")


class Konto(Modell):
    """Eine Person mit ihrem Kellerwolke-Konto; die Pinnwand legt Konten nicht selbst an."""

    id: Kennung
    name: str
    kuerzel: str
    farbe: Farbe = "stahl"
    kellerwolke: str


class Ordner(Modell):
    """Persönlicher Ordner in der Seitenleiste: ordnet nur, trägt keine Rechte."""

    id: Kennung
    name: str
    boards: list[Kennung] = Field(default_factory=list)


class Label(Modell):
    id: Kennung
    name: str
    farbe: Farbe


class Spalte(Modell):
    id: Kennung
    name: str
    farbe: Farbe
    erledigt: bool = False
    grenze: int | None = None
    eingeklappt: bool | None = None
    zeitfenster: Zeitfenster | None = None


class Feld(Modell):
    id: Kennung
    name: str
    art: FeldArt
    optionen: list[str] | None = None
    auf_karte: bool = False


class Recht(Modell):
    id: Kennung
    modul: str
    name: str
    erklaerung: str


class Rolle(Modell):
    id: Kennung
    name: str
    rechte: list[Kennung] = Field(default_factory=list)
    vorgabe: bool | None = None


class Mitglied(Modell):
    """Mitglied eines Boards. Eingeladen wird per Kontoname der Kellerwolke; die Kennung des Kontos steht da, sobald die
    Person sich einmal angemeldet hat."""

    konto: Kennung = ""
    kellerwolke: str
    rolle: Kennung
    seit: str


class BoardEinstellungen(Modell):
    alterung_warnung: int = 4
    alterung_gefahr: int = 8
    ladeschritt: int = 50
    archiv_tage: int = 365


class Board(Modell):
    id: Kennung
    name: str
    kuerzel: str
    farbe: Farbe
    #: Art neuer Karten, wenn beim Anlegen keine gewählt ist
    kartenart: Kartenart = "arbeit"
    spalten: list[Spalte] = Field(default_factory=list)
    labels: list[Label] = Field(default_factory=list)
    felder: list[Feld] = Field(default_factory=list)
    rollen: list[Rolle] = Field(default_factory=list)
    mitglieder: list[Mitglied] = Field(default_factory=list)
    module: dict[str, bool] = Field(default_factory=lambda: {m: False for m in MODULE})
    einstellungen: BoardEinstellungen = Field(default_factory=BoardEinstellungen)
    fassung: int = 0


class Punkt(Modell):
    text: str
    erledigt: bool = False


class Kommentar(Modell):
    von: Kennung
    zeit: str
    text: str


AnhangArt = Literal["pdf", "bild", "tabelle", "text", "ton"]


class Anhang(Modell):
    """Eine Datei an einer Karte: hochgeladen in den Ordner des Boards in der Ablage der Pinnwand, oder aus der eigenen
    Kellerwolke verknüpft (die Datei bleibt, wo sie ist). Der Name ist an der Karte eindeutig."""

    name: str
    groesse: str
    art: AnhangArt
    verknuepft: bool | None = None
    #: Kennung der Datei in der Kellerwolke
    datei: str | None = None
    #: Weg der Datei in der Kellerwolke vom Konto aus, mit Namen ("Apps/Pinnwand/Haushalt/Skizze.png")
    pfad: str | None = None
    #: wer sie angehängt hat; bei einer verknüpften: in wessen Kellerwolke sie liegt
    von: Kennung | None = None


class TranskriptMarke(Modell):
    aufnahme: str
    stelle: str
    text: str


class Ereignis(Modell):
    """Eine Zeile im Verlauf einer Karte."""

    zeit: str
    von: Kennung
    text: str


class Karte(Modell):
    id: Kennung
    board: Kennung
    schluessel: str
    spalte: Kennung
    titel: str
    art: Kartenart = "arbeit"
    beschreibung: str | None = None
    notizen: str | None = None
    zustaendig: list[Kennung] = Field(default_factory=list)
    prioritaet: Prioritaet = "keine"
    start: str | None = None
    faellig: str | None = None
    labels: list[Kennung] = Field(default_factory=list)
    checkliste: list[Punkt] = Field(default_factory=list)
    kommentare: list[Kommentar] = Field(default_factory=list)
    cover: Farbe | None = None
    blockiert: str | None = None
    schaetzung_min: int | None = None
    bewegt_am: str
    erstellt_am: str
    abgeschlossen: str | None = None
    gruppe: Kennung | None = None
    serie: Kennung | None = None
    felder: dict[Kennung, str] = Field(default_factory=dict)
    anhaenge: list[Anhang] = Field(default_factory=list)
    transkripte: list[TranskriptMarke] = Field(default_factory=list)
    verlauf: list[Ereignis] = Field(default_factory=list)
    #: Platz in der Spalte (Gleitkomma mit Raum dazwischen); die Oberfläche ordnet danach
    reihe: float = 0
    fassung: int = 0


class Gruppe(Modell):
    """Verknüpfte Karten eines Boards: ziehen zusammen und teilen auf Wunsch ihre Zeit."""

    id: Kennung
    board: Kennung
    zeit_teilen: bool = True


class Laufnummer(Modell):
    """Die letzte vergebene Kartennummer eines Boards (Kennung: die des Boards). Läuft nur vorwärts: eine Nummer wird
    nie wieder vergeben, auch nicht nach Rückgängig oder Löschen."""

    id: Kennung
    board: Kennung
    zahl: int = 0


class Hinweis(Modell):
    id: Kennung
    konto: Kennung
    art: HinweisArt
    zeit: str
    von: Kennung | None = None
    board: Kennung
    karte: Kennung | None = None
    text: str
    gelesen: bool = False


class PersonEinstellungen(Modell):
    hinweise: dict[str, dict[str, bool]] = Field(default_factory=dict)


class VorlageSpalte(Modell):
    name: str
    farbe: Farbe
    erledigt: bool = False
    grenze: int | None = None


class VorlageFeld(Modell):
    name: str
    art: FeldArt
    optionen: list[str] | None = None
    auf_karte: bool = False


class VorlageLabel(Modell):
    name: str
    farbe: Farbe


class Vorlage(Modell):
    id: Kennung
    name: str
    beschreibung: str
    symbol: str
    spalten: list[VorlageSpalte]
    kartenart: Kartenart = "arbeit"
    felder: list[VorlageFeld] = Field(default_factory=list)
    labels: list[VorlageLabel] = Field(default_factory=list)
    module: list[str] = Field(default_factory=list)
    eigen: bool | None = None
    #: eigene Vorlagen gehören einem Konto
    konto: Kennung | None = None


class Stelle(Modell):
    spalte: Kennung | None = None
    platz: int = 0


class Geloescht(Modell):
    """Was im Papierkorb liegt, damit Wiederherstellen alles an seine alte Stelle bringt."""

    id: Kennung
    board: Kennung
    art: Literal["karte", "spalte", "board"]
    spalte: Spalte | None = None
    karten: list[Karte] = Field(default_factory=list)
    stelle: Stelle = Field(default_factory=Stelle)
    von: Kennung
    am: str
    #: bei einem Board: das Board selbst und sein Ordner
    inhalt: dict | None = None


Herkunft = Literal["timer", "hand", "korrektur", "serie"]


class Sitzung(Modell):
    von: str
    bis: str


class Deckel(Modell):
    """Vermerk an Einträgen einer Sitzung, die länger als 12 Stunden lief: gebucht sind die ersten 12, bis die Person
    das echte Ende nennt oder die 12 bestätigt. Die echte Sitzung als Zeitpunkte."""

    seit: str
    bis: str
    sekunden: int


class Zeiteintrag(Modell):
    """Gebuchte Zeit einer Person auf einer Karte an einem Tag; die Zeit einer Karte ist die Summe ihrer Einträge. Das
    Board der Karte steht dabei, danach richtet sich, wer den Eintrag sieht."""

    id: Kennung
    karte: Kennung
    board: Kennung
    konto: Kennung
    datum: str
    von: str | None = None
    bis: str | None = None
    sekunden: int
    herkunft: Herkunft
    notiz: str | None = None
    #: Timer-Sitzungen, die je Karte und Tag zu diesem einen Eintrag zusammengefasst sind
    sitzungen: list[Sitzung] | None = None
    #: an Mitternacht zerlegt: der andere Teil derselben Sitzung liegt an diesem Tag
    zerlegt: str | None = None
    gedeckelt: Deckel | None = None


class Timer(Modell):
    """Der eine Timer einer Person (Kennung gleich dem Konto): läuft seit `seit` oder ist angehalten."""

    id: Kennung
    konto: Kennung
    karte: Kennung
    board: Kennung
    seit: str | None = None


class Halbtagsregel(Modell):
    """Halber Arbeitstag an einem festen Tag im Jahr (etwa Heiligabend)."""

    monat: int
    tag: int
    name: str


class Zeitkonto(Modell):
    """Zeitkonto einer Person; eine neue Fassung gilt ab einem Tag, frühere Tage behalten ihr Soll. Tage zählen ab
    Sonntag (0) bis Samstag (6) wie in der Oberfläche."""

    id: Kennung
    konto: Kennung
    ab: str
    wochenstunden: float
    tage: list[int]
    bundesland: str
    urlaubsanspruch: float
    resturlaub_vorjahr: float = 0
    halbtage: list[Halbtagsregel] = Field(default_factory=list)


AbwesenheitArt = Literal["urlaub", "krank", "frei", "feiertag", "fortbildung"]


class Abwesenheit(Modell):
    id: Kennung
    konto: Kennung
    von: str
    bis: str
    art: AbwesenheitArt
    #: halber Tag: 0,5; leer: ganze Tage
    anteil: float | None = None
    notiz: str | None = None


class Kartenname(Modell):
    """Name einer Karte, auf die sichtbare Zeiteinträge zeigen, die selbst nicht im Stand ist (archiviert, Board
    verlassen)."""

    karte: Kennung
    board: Kennung
    schluessel: str
    titel: str


class Entfernt(Modell):
    """Eine endgültig entfernte Karte: ihr Name bleibt für die Zeiteinträge, die weiter gebucht sind."""

    karte: Kennung
    board: Kennung
    schluessel: str
    titel: str
    am: str
