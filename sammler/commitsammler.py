#!/usr/bin/env python3
"""Commitsammler der Pinnwand (HELF-35): ein eigenes kleines Programm neben der App. Es liest Commits aus Git-Repos auf
diesem Rechner und spielt sie in die Pinnwand ein; die Pinnwand hängt jeden Commit an die Karten, deren Schlüssel in
seiner Nachricht steht (etwa HELF-12). Zugänge zu Git-Verwaltungen und alle Einstellungen bleiben hier, die Pinnwand
bekommt nur die Werte.

    commitsammler.py                  alle Repos abgleichen (neue Commits seit dem letzten Lauf)
    commitsammler.py --alles          die ganze Geschichte noch einmal (Nachtrag; die Pinnwand übernimmt nur Neues)
    commitsammler.py --zeigen         nur zeigen, welche Repos mit welchem Ziel gefunden werden, nichts senden

Einstellungen in ~/.config/pinnwand/commits.toml (Vorlage: sammler/commits.beispiel.toml im Repo der Pinnwand):
Adresse der Pinnwand, Schlüsseldatei, die Git-Verwaltungen (beliebig viele, gleichberechtigt), wo Repos liegen und
wessen Repos zählen, je Repo das Ziel des Verweises. Der Stand (letzter Commit je Repo) liegt daneben in
commits.stand.json. Nur Python und git, keine weiteren Pakete.
"""

from __future__ import annotations

import argparse
import json
import re
import ssl
import subprocess
import sys
import tomllib
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

EINSTELLUNGEN = Path("~/.config/pinnwand/commits.toml").expanduser()
#: so viele Commits je Sendung; die Pinnwand nimmt höchstens 500
PAKET = 200
#: Trenner der Felder im Format von git log (kommt in Nachrichten nicht vor)
FELD = "\x1f"
SATZ = "\x1e"


@dataclass
class Quelle:
    """Eine Git-Verwaltung: Name, Rechner (wie im Remote) und das Muster des Verweises auf einen Commit."""

    name: str
    rechner: str
    muster: str


@dataclass
class Repo:
    pfad: Path
    kennung: str
    name: str
    quelle: str
    verweis: str | None


def einstellungen(datei: Path) -> dict:
    if not datei.exists():
        sys.exit(f"Keine Einstellungen: {datei} fehlt (Vorlage sammler/commits.beispiel.toml)")
    return tomllib.loads(datei.read_text())


def git(pfad: Path, *argumente: str) -> str:
    return subprocess.run(["git", "-C", str(pfad), *argumente], capture_output=True, text=True, check=True).stdout


def remote(pfad: Path) -> tuple[str, str] | None:
    """Rechner und Weg (Besitzer/Name) des Remotes origin; ohne Remote: None."""
    try:
        url = git(pfad, "remote", "get-url", "origin").strip()
    except subprocess.CalledProcessError:
        return None
    m = re.match(r"^(?:https?://(?:[^@/]+@)?|ssh://(?:[^@/]+@)?|[^@]+@)([^/:]+)(?::\d+)?[:/](.+?)(?:\.git)?/?$", url)
    return (m.group(1), m.group(2)) if m else None


def repos_finden(e: dict) -> list[Repo]:
    """Alle Repos unter den Wurzeln, die zählen: lokal ohne Remote oder mit einem Besitzer aus der Liste."""
    quellen = [Quelle(q["name"], q["rechner"], q["verweis"]) for q in e.get("quelle", [])]
    besitzer = {b.lower() for b in e.get("besitzer", [])}
    eigene = {str(Path(p).expanduser()): z for p, z in (e.get("repo") or {}).items()}
    tiefe = int(e.get("tiefe", 3))
    gefunden: list[Repo] = []
    for wurzel in (Path(w).expanduser() for w in e.get("wurzeln", [])):
        for g in (p for t in range(1, tiefe + 1) for p in sorted(wurzel.glob("/".join(["*"] * t) + "/.git"))):
            pfad = g.parent
            r = remote(pfad)
            eigen = eigene.get(str(pfad), {})
            if eigen.get("aus"):
                continue
            if r and r[1].split("/")[0].lower() not in besitzer and not eigen:
                continue
            quelle = next((q for q in quellen if r and q.rechner == r[0]), None)
            ziel = eigen.get("ziel", quelle.name if quelle else "lokal")
            q = next((x for x in quellen if x.name == ziel), None)
            weg = eigen.get("weg", r[1] if r else None)
            verweis = q.muster.replace("{weg}", weg) if q and weg else None
            gefunden.append(Repo(pfad=pfad, kennung=weg or f"lokal/{pfad.name}", name=pfad.name,
                                 quelle=q.name if q else "lokal", verweis=verweis))
    return gefunden


def commits(r: Repo, seit: str | None) -> list[dict]:
    bereich = [f"{seit}..HEAD"] if seit else ["HEAD"]
    try:
        roh = git(r.pfad, "log", *bereich, "--no-merges", "--name-only",
                  f"--format={SATZ}%H{FELD}%an{FELD}%aI{FELD}%B{FELD}")
    except subprocess.CalledProcessError:
        # der gemerkte Stand ist weg (Geschichte umgeschrieben): noch einmal alles, die Pinnwand nimmt nur Neues;
        # ein leeres Repo hat nichts
        return commits(r, None) if seit else []
    liste = []
    for satz in roh.split(SATZ)[1:]:
        h, autor, zeit, nachricht, dateien = satz.split(FELD)
        liste.append({"hash": h, "autor": autor, "zeit": zeit[:19], "nachricht": nachricht.strip()[:4000],
                      "dateien": [d for d in dateien.strip().split("\n") if d][:100]})
    return list(reversed(liste))


def senden(e: dict, r: Repo, liste: list[dict]) -> dict:
    schluessel = Path(e["schluessel"]).expanduser().read_text().strip()
    daten = {"repo": {"kennung": r.kennung, "name": r.name, "quelle": r.quelle, "verweis": r.verweis}, "commits": liste}
    anfrage = urllib.request.Request(e["adresse"].rstrip("/") + "/commits/einspielen", data=json.dumps(daten).encode(),
                                     headers={"Authorization": "Bearer " + schluessel, "Content-Type": "application/json"},
                                     method="POST")
    kontext = ssl._create_unverified_context() if e.get("hauszertifikat", True) else None
    with urllib.request.urlopen(anfrage, context=kontext, timeout=120) as antwort:
        return json.load(antwort)


def main() -> None:
    a = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    a.add_argument("--alles", action="store_true", help="die ganze Geschichte senden (Nachtrag)")
    a.add_argument("--zeigen", action="store_true", help="nur die gefundenen Repos zeigen")
    a.add_argument("--einstellungen", type=Path, default=EINSTELLUNGEN, help=f"andere Datei (Vorgabe {EINSTELLUNGEN})")
    args = a.parse_args()
    e = einstellungen(args.einstellungen)
    stand_datei = args.einstellungen.with_name(args.einstellungen.stem + ".stand.json")
    repos = repos_finden(e)
    if args.zeigen:
        for r in repos:
            print(f"{r.kennung:50} {r.quelle:12} {r.verweis or '(zeigt die Pinnwand selbst)'}")
        print(f"{len(repos)} Repos")
        return
    stand = {} if args.alles or not stand_datei.exists() else json.loads(stand_datei.read_text())
    gesamt = {"commits": 0, "neu": 0, "verknuepft": 0}
    for r in repos:
        liste = commits(r, stand.get(r.kennung))
        for i in range(0, len(liste), PAKET):
            try:
                antwort = senden(e, r, liste[i:i + PAKET])
            except urllib.error.HTTPError as f:
                sys.exit(f"{r.kennung}: abgelehnt ({f.code}) {f.read().decode()[:300]}")
            gesamt["commits"] += len(liste[i:i + PAKET])
            gesamt["neu"] += antwort.get("neu", 0)
            gesamt["verknuepft"] += antwort.get("verknuepft", 0)
        if liste:
            stand[r.kennung] = liste[-1]["hash"]
            stand_datei.write_text(json.dumps(stand, indent=1))
    print(f"{len(repos)} Repos, {gesamt['commits']} Commits gesendet, {gesamt['neu']} neu, {gesamt['verknuepft']} an Karten gehängt")


if __name__ == "__main__":
    main()
