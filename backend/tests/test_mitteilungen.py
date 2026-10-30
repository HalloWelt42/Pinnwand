"""Hinweise als Mitteilung aufs Telefon: ein Gerät meldet sein Abo, eine Zuweisung kommt verschlüsselt mit dem Weg zur
Karte an; Push gilt je Art (Vorgabe: was die Person selbst betrifft) und lässt sich je Art abschalten."""

from __future__ import annotations

import base64
import json

import http_ece
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

from conftest import Pinnwand
from nachgestellt import PUSH_EINGANG
from test_hinweise import bearbeiten, zu_dritt
from test_verwaltung import ok

AUTH = b"0123456789abcdef"


@pytest.fixture(autouse=True)
def leerer_eingang():
    PUSH_EINGANG.clear()
    yield
    PUSH_EINGANG.clear()


def b64(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


async def telefon(pw: Pinnwand, wer: str) -> ec.EllipticCurvePrivateKey:
    """Ein Telefon mit Abo für diese Person; Ergebnis: sein Schlüssel zum Entschlüsseln."""
    schluessel = ec.generate_private_key(ec.SECP256R1())
    punkt = schluessel.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    abo = {"endpoint": f"https://push.test/{wer}", "keys": {"p256dh": b64(punkt), "auth": b64(AUTH)}}
    r = await pw.c.post("/api/v1/push/abo", headers=pw.kopf[wer], json={"abo": abo, "geraet": "iPhone, Web-App"})
    assert r.status_code == 200, r.text
    return schluessel


def angekommen(schluessel: ec.EllipticCurvePrivateKey) -> list[dict]:
    return [json.loads(http_ece.decrypt(r.content, private_key=schluessel, auth_secret=AUTH, version="aes128gcm"))
            for r in PUSH_EINGANG]


async def test_zuweisung_kommt_aufs_telefon(pw: Pinnwand):
    b = await zu_dritt(pw)
    mitteilungen = pw.app.state.dienste.mitteilungen
    schluessel = await telefon(pw, "bert")
    k = await pw.karte("anna", b, "Fenster")
    await bearbeiten(pw, "anna", k, {"zustaendig": ["1", "2"]})
    await mitteilungen.leeren()
    [m] = angekommen(schluessel)
    assert (m["titel"], m["url"], m["tag"][:8]) == ("Zugewiesen, Haushalt", "/board/haus/1", "hinweis-")
    assert "HAUS-1" in m["text"]

    # Kommentare kommen nur in der Pinnwand, solange bert nichts schaltet; Zuweisungen schaltet er ab
    await pw.post("anna", f"/karten/{k['id']}/kommentieren", {"text": "Bitte bis Freitag"})
    await ok(pw, "bert", "/hinweise/weg", {"art": "zugewiesen", "weg": "push", "an": False})
    await bearbeiten(pw, "anna", await pw.karte("anna", b, "Keller"), {"zustaendig": ["2"]})
    await mitteilungen.leeren()
    assert len(PUSH_EINGANG) == 1

    s = await pw.stand("bert")
    assert s["hinweiswege"]["da"] == ["pinnwand", "push"]
    assert s["hinweiswege"]["vorgabe"]["faellig"] == {"pinnwand": True, "push": True}
    assert s["hinweiswege"]["vorgabe"]["kommentar"] == {"pinnwand": True, "push": False}


async def test_buendel_klingelt_nur_bei_wichtigerem(pw: Pinnwand):
    """HELF-54: ein Bündel klingelt am Telefon, wenn eine wichtigere Art dazukommt (eine Zuweisung zu einem Kommentar),
    nicht bei jedem weiteren Anlass."""
    b = await zu_dritt(pw)
    mitteilungen = pw.app.state.dienste.mitteilungen
    schluessel = await telefon(pw, "bert")
    k = await pw.karte("bert", b, "Fenster")                       # bert ist zuständig
    await pw.post("anna", f"/karten/{k['id']}/kommentieren", {"text": "Ursache gefunden"})
    await mitteilungen.leeren()
    assert PUSH_EINGANG == []                                       # Kommentar: nur in der Pinnwand
    await bearbeiten(pw, "anna", k, {"zustaendig": ["2", "3"]})     # cora dazu: an bert nichts Neues
    await pw.post("anna", f"/karten/{k['id']}/verschieben", {"nach": next(s["id"] for s in b["spalten"] if s["name"] == "Dran")})
    await mitteilungen.leeren()
    assert PUSH_EINGANG == []
    k2 = await pw.karte("anna", b, "Keller")
    await pw.post("anna", f"/karten/{k2['id']}/kommentieren", {"text": "@bert schau bitte"})      # erwähnt: klingelt
    await bearbeiten(pw, "anna", k2, {"zustaendig": ["1", "2"]})                                  # zugewiesen: wichtiger
    await pw.post("anna", f"/karten/{k2['id']}/kommentieren", {"text": "Danke"})                  # Kommentar: still
    await mitteilungen.leeren()
    texte = [(m["titel"], m["text"]) for m in angekommen(schluessel)]
    assert texte == [("Erwähnt, Haushalt", "anna hat dich in HAUS-2 erwähnt"),
                     ("Zugewiesen, Haushalt", "anna bei HAUS-2: dich erwähnt und dir zugewiesen")]
