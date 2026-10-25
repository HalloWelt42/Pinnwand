"""Eine nachgestellte Kellerwolke für Tests und den Probebetrieb (tools/probebetrieb.py): drei Personen mit dem
Passwort "geheim", anna besitzt den App-Schlüssel, bert und cora dürfen erst nach einer Einladung. Dazu die Ablage im
Speicher (`ABLAGE`), so weit der Zugang des Appkerns sie für Anhänge ruft: Ordner, Dateien schreiben, lesen und in den
Papierkorb legen im Zweig der App, und die Dateiwahl mit der Anmeldung einer Person in ihren eigenen Dateien. Dazu die
Leitstelle (`LEITSTELLE`) mit Antworten des Modells der Reihe nach."""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass, field

import httpx

PERSONEN = {"anna": "1", "bert": "2", "cora": "3"}
PASSWORT = "geheim"
#: Einrichtung der App gegen diese Kellerwolke (Adresse und App-Schlüssel nur zum Schein)
EINRICHTUNG = {"kellerwolke_adresse": "http://kw.test", "kellerwolke_schluessel": "kw_app_x"}
#: Konto, dem der App-Schlüssel gehört, und der Zweig der App darin
BESITZER = "anna"
ZWEIG = "Apps/Pinnwand"
ZEIT = "2026-10-27T10:00:00Z"


def benutzer(name: str) -> dict:
    return {"id": PERSONEN[name], "name": name, "rolle": "mitglied", "aktiv": True}


@dataclass
class Eintrag:
    id: str
    konto: str
    name: str
    typ: str
    eltern: str | None
    inhalt: bytes = b""
    inhaltstyp: str | None = None
    weg: bool = False


@dataclass
class Ablage:
    """Dateien und Ordner je Konto. Die App sieht mit ihrem Schlüssel nur ihren Zweig im Konto des Besitzers; eine
    Person sieht in der Dateiwahl ihre eigenen Dateien. `schreiben_frei` lässt nur so viele Dateien schreiben (danach:
    nicht erreichbar), `loeschen_geht` schaltet das Löschen ab."""

    eintraege: dict[str, Eintrag] = field(default_factory=dict)
    schreiben_frei: int | None = None
    loeschen_geht: bool = True

    def leeren(self) -> None:
        self.eintraege.clear()
        self.schreiben_frei = None
        self.loeschen_geht = True

    # --- Inhalt ---------------------------------------------------------------------------------------------------

    def pfad(self, e: Eintrag) -> str:
        teile = [e.name]
        while e.eltern:
            e = self.eintraege[e.eltern]
            teile.append(e.name)
        return "/".join(reversed(teile))

    def kinder(self, konto: str, eltern: str | None) -> list[Eintrag]:
        da = [e for e in self.eintraege.values() if e.konto == konto and e.eltern == eltern and not e.weg]
        return sorted(da, key=lambda e: (e.typ != "ordner", e.name.lower()))

    def finden(self, konto: str, pfad: str) -> Eintrag | None:
        eltern: str | None = None
        gefunden = None
        for teil in pfad.split("/"):
            gefunden = next((e for e in self.kinder(konto, eltern) if e.name == teil), None)
            if gefunden is None:
                return None
            eltern = gefunden.id
        return gefunden

    def ordner(self, konto: str, pfad: str) -> Eintrag:
        eltern: str | None = None
        e = None
        for teil in pfad.split("/"):
            e = next((x for x in self.kinder(konto, eltern) if x.name == teil), None)
            if e is None:
                e = Eintrag(str(uuid.uuid4()), konto, teil, "ordner", eltern)
                self.eintraege[e.id] = e
            eltern = e.id
        assert e is not None
        return e

    def datei(self, konto: str, pfad: str, inhalt: bytes, inhaltstyp: str | None = None) -> Eintrag:
        """Eine Datei im Konto einer Person (für Tests: was sie in ihrer Kellerwolke hat)."""
        ordner, _, name = pfad.rpartition("/")
        e = Eintrag(str(uuid.uuid4()), konto, name, "datei", self.ordner(konto, ordner).id if ordner else None, inhalt,
                    inhaltstyp)
        self.eintraege[e.id] = e
        return e

    def im_zweig(self) -> list[Eintrag]:
        """Lebende Dateien im Zweig der App (für Tests)."""
        return [e for e in self.eintraege.values() if e.typ == "datei" and not e.weg and self.fuer_app(e)]

    def fuer_app(self, e: Eintrag) -> bool:
        return e.konto == BESITZER and not e.weg and (self.pfad(e) + "/").startswith(ZWEIG + "/")

    def knoten(self, e: Eintrag) -> dict:
        return {"id": e.id, "parent_id": e.eltern, "name": e.name, "typ": e.typ, "pfad": self.pfad(e), "recht": "schreiben",
                "etag": f"e{len(e.inhalt)}" if e.typ == "datei" else None, "groesse": len(e.inhalt) if e.typ == "datei" else None,
                "inhaltstyp": e.inhaltstyp, "erstellt_am": ZEIT, "geaendert_am": ZEIT}

    # --- Wege -----------------------------------------------------------------------------------------------------

    def antwort(self, request: httpx.Request, weg: str) -> httpx.Response:
        if weg == "/wahl" and request.method == "GET":
            return self._wahl(request)
        if weg == "/ordner" and request.method == "POST":
            pfad = json.loads(request.content)["pfad"]
            if not (pfad + "/").startswith(ZWEIG + "/"):
                return httpx.Response(403, json={"detail": "nur im eigenen Zweig"})
            return httpx.Response(200, json=self.knoten(self.ordner(BESITZER, pfad)))
        if weg == "/pfad":
            e = self.finden(BESITZER, request.url.params["pfad"])
            return httpx.Response(200, json=self.knoten(e)) if e and self.fuer_app(e) else _fehlt()
        if weg == "/datei" and request.method == "PUT":
            return self._schreiben(request)
        if m := re.fullmatch(r"/knoten/([^/]+)(/kinder|/inhalt)?", weg):
            e = self.eintraege.get(m.group(1))
            if e is None or not self.fuer_app(e):
                return _fehlt()
            if m.group(2) == "/kinder":
                ab, anzahl = int(request.url.params.get("ab", 0)), int(request.url.params.get("anzahl", 200))
                return httpx.Response(200, json=[self.knoten(k) for k in self.kinder(e.konto, e.id)[ab:ab + anzahl]])
            if m.group(2) == "/inhalt":
                return _inhalt(e, request)
            if request.method == "DELETE":
                if not self.loeschen_geht:
                    return httpx.Response(503, json={"detail": "Speicher gerade nicht verfügbar"})
                e.weg = True
                return httpx.Response(204)
            return httpx.Response(200, json=self.knoten(e))
        return _fehlt()

    def _schreiben(self, request: httpx.Request) -> httpx.Response:
        if self.schreiben_frei is not None:
            if self.schreiben_frei <= 0:
                return httpx.Response(503, json={"detail": "Speicher gerade nicht verfügbar"})
            self.schreiben_frei -= 1
        ordner, _, name = request.url.params["pfad"].rpartition("/")
        eltern = self.finden(BESITZER, ordner) if ordner else None
        if eltern is None or eltern.typ != "ordner" or not self.fuer_app(eltern):
            return httpx.Response(404, json={"detail": "Ordner nicht gefunden"})
        if any(k.name == name for k in self.kinder(BESITZER, eltern.id)):
            return httpx.Response(412, json={"detail": "Die Datei gibt es schon"})
        typ = request.headers.get("content-type")
        e = Eintrag(str(uuid.uuid4()), BESITZER, name, "datei", eltern.id, request.content,
                    None if typ in (None, "application/octet-stream") else typ)
        self.eintraege[e.id] = e
        return httpx.Response(200, json=self.knoten(e))

    def _wahl(self, request: httpx.Request) -> httpx.Response:
        name = (request.headers.get("x-kellerwolke-sitzung") or "").removeprefix("t-")
        if name not in PERSONEN:
            return httpx.Response(401, json={"detail": "Anmeldung erforderlich"})
        kette: list[dict] = [{"id": None, "name": "Meine Dateien"}]
        ordner = request.url.params.get("ordner")
        if ordner:
            e = self.eintraege.get(ordner)
            if e is None or e.konto != name or e.typ != "ordner" or e.weg:
                return httpx.Response(404, json={"detail": "Ordner nicht gefunden"})
            weg = []
            while e:
                weg.append({"id": e.id, "name": e.name})
                e = self.eintraege[e.eltern] if e.eltern else None
            kette += reversed(weg)
        eintraege = [{"id": e.id, "name": e.name, "typ": e.typ, "groesse": len(e.inhalt) if e.typ == "datei" else None,
                      "inhaltstyp": e.inhaltstyp, "geaendert_am": ZEIT,
                      "kinder_anzahl": len(self.kinder(name, e.id)) if e.typ == "ordner" else None}
                     for e in self.kinder(name, ordner or None)]
        return httpx.Response(200, json={"kette": kette, "eintraege": eintraege})


def _fehlt() -> httpx.Response:
    return httpx.Response(404, json={"detail": "nicht da"})


def _inhalt(e: Eintrag, request: httpx.Request) -> httpx.Response:
    kopf = {"content-type": e.inhaltstyp or "application/octet-stream"}
    bereich = re.fullmatch(r"bytes=(\d+)-(\d*)", request.headers.get("range", ""))
    if bereich:
        start = int(bereich.group(1))
        ende = int(bereich.group(2)) if bereich.group(2) else len(e.inhalt) - 1
        return httpx.Response(206, content=e.inhalt[start:ende + 1], headers=kopf)
    return httpx.Response(200, content=e.inhalt, headers=kopf)


ABLAGE = Ablage()


#: was beim nachgestellten Push-Dienst ankommt (Host push.test): je Mitteilung die Anfrage
PUSH_EINGANG: list[httpx.Request] = []
#: Leitstelle für die Einstellungen der App (Adresse und Schlüssel nur zum Schein)
LEITSTELLE_EINRICHTUNG = {"leitstelle_adresse": "http://ls.test", "leitstelle_schluessel": "ls_x"}


@dataclass
class Leitstelle:
    """Die Fassade der Leitstelle (Host ls.test), so weit KI an der Karte sie ruft: Modelle und Chat. Die Antworten des
    Modells kommen der Reihe nach aus `antworten` (Text, wie das Modell ihn schreibt); jede Anfrage steht mit ihren
    Köpfen in `anfragen`. `fehler` antwortet stattdessen mit diesem Status und Grundwort."""

    antworten: list[str] = field(default_factory=list)
    anfragen: list[httpx.Request] = field(default_factory=list)
    fehler: tuple[int, str] | None = None
    ende: str = "stop"

    def leeren(self) -> None:
        self.antworten.clear()
        self.anfragen.clear()
        self.fehler = None
        self.ende = "stop"

    def koerper(self, i: int = -1) -> dict:
        return json.loads(self.anfragen[i].content)

    def antwort(self, request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/models":
            return httpx.Response(200, json={"data": [
                {"id": "gross", "x-leitstelle": {"name": "Groß", "faehigkeiten": ["text"], "geladen": True}}]})
        if request.url.path != "/v1/chat/completions":
            return _fehlt()
        self.anfragen.append(request)
        if self.fehler:
            status, grund = self.fehler
            return httpx.Response(status, json={"error": {"code": grund, "message": "Die Leitstelle hält gerade an"}})
        text = self.antworten.pop(0)
        return httpx.Response(200, json={"choices": [{"message": {"content": text}, "finish_reason": self.ende}],
                                         "model": "gross"}, headers={"x-leitstelle-modell": "gross"})


LEITSTELLE = Leitstelle()


def kellerwolke(request: httpx.Request) -> httpx.Response:
    pfad = request.url.path
    if request.url.host == "push.test":
        PUSH_EINGANG.append(request)
        return httpx.Response(201)
    if request.url.host == "ls.test":
        return LEITSTELLE.antwort(request)
    if pfad == "/api/v1/ablage/ich":
        return httpx.Response(200, json={"app": "Pinnwand", "konto": "anna", "rechte": []})
    if pfad.startswith("/api/v1/ablage/"):
        return ABLAGE.antwort(request, pfad.removeprefix("/api/v1/ablage"))
    if pfad == "/api/v1/auth/login":
        e = json.loads(request.content)
        if e["kennung"] not in PERSONEN or e["passwort"] != PASSWORT:
            return httpx.Response(401, json={"detail": "Anmeldung fehlgeschlagen"})
        return httpx.Response(200, json={"token": f"t-{e['kennung']}", "benutzer": benutzer(e["kennung"])})
    if pfad == "/api/v1/auth/status":
        name = (request.headers.get("x-kellerwolke-sitzung") or "").removeprefix("t-")
        ok = name in PERSONEN
        return httpx.Response(200, json={"angemeldet": ok, "benutzer": benutzer(name) if ok else None})
    if pfad.startswith("/api/v1/auth/"):
        return httpx.Response(200, json={})
    return httpx.Response(404, json={"detail": "nicht da"})
