"""Abhaengigkeitsgraph eines Boards: Schichtung, kritischer Pfad, Zyklen.

Eine Karte kann durch andere Karten blockiert sein (Feld blockiert_von). Daraus
ergibt sich ein gerichteter Graph mit Kanten "Blocker -> abhaengige Karte". Diese
Datei berechnet daraus zentral und testbar:

- eine schichtweise Anordnung (laengster Weg von den Wurzeln, Topologie),
- den kritischen Pfad (laengste Kette, gewichtet nach Schaetzung, sonst nach Laenge),
- erkannte Zyklen (Rueckwaertskanten),
- je Karte den Status erledigt / startklar / blockiert.

Die Ansicht rendert das Ergebnis nur noch.
"""
from __future__ import annotations

from .models import BoardDetail


def _valide_kanten(detail: BoardDetail) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """Baut Nachfolger- und Vorgaenger-Listen aus blockiert_von.

    Kante B -> C bedeutet: B blockiert C (B muss vor C fertig sein). Ungueltige
    Verweise (unbekannte oder Selbst-IDs) und Doubletten werden verworfen.
    """
    ids = {k.id for k in detail.karten}
    succ: dict[str, list[str]] = {k.id: [] for k in detail.karten}
    pred: dict[str, list[str]] = {k.id: [] for k in detail.karten}
    for c in detail.karten:
        gesehen: set[str] = set()
        for b in c.blockiert_von or []:
            if b in ids and b != c.id and b not in gesehen:
                gesehen.add(b)
                succ[b].append(c.id)
                pred[c.id].append(b)
    return succ, pred


def _rueckwaertskanten(karten, succ: dict[str, list[str]]) -> set[tuple[str, str]]:
    """Findet Zyklus-verursachende Rueckwaertskanten per iterativer Tiefensuche."""
    WEISS, GRAU, SCHWARZ = 0, 1, 2
    farbe = {k.id: WEISS for k in karten}
    back: set[tuple[str, str]] = set()
    for start in [k.id for k in karten]:
        if farbe[start] != WEISS:
            continue
        farbe[start] = GRAU
        stack: list[tuple[str, object]] = [(start, iter(succ[start]))]
        while stack:
            u, it = stack[-1]
            weiter = False
            for v in it:  # type: ignore[assignment]
                if farbe[v] == GRAU:
                    back.add((u, v))
                elif farbe[v] == WEISS:
                    farbe[v] = GRAU
                    stack.append((v, iter(succ[v])))
                    weiter = True
                    break
            if not weiter:
                farbe[u] = SCHWARZ
                stack.pop()
    return back


def berechne(detail: BoardDetail) -> dict:
    karten = detail.karten
    done = {s.id for s in detail.spalten if s.erledigt}
    by_id = {k.id: k for k in karten}
    reihenfolge = {k.id: i for i, k in enumerate(karten)}

    succ, pred = _valide_kanten(detail)
    back = _rueckwaertskanten(karten, succ)

    # Fuer Schichtung und kritischen Pfad einen Zyklen-freien Graphen verwenden.
    dag_succ = {kid: [v for v in succ[kid] if (kid, v) not in back] for kid in succ}
    dag_pred = {kid: [u for u in pred[kid] if (u, kid) not in back] for kid in pred}

    # Topologische Reihenfolge (Kahn), stabil nach Kartenreihenfolge.
    indeg = {k.id: len(dag_pred[k.id]) for k in karten}
    queue = sorted([k.id for k in karten if indeg[k.id] == 0], key=lambda i: reihenfolge[i])
    topo: list[str] = []
    while queue:
        u = queue.pop(0)
        topo.append(u)
        frei: list[str] = []
        for v in dag_succ[u]:
            indeg[v] -= 1
            if indeg[v] == 0:
                frei.append(v)
        for v in sorted(frei, key=lambda i: reihenfolge[i]):
            queue.append(v)
    # Sicherheitsnetz: sollte nach Entfernen der Rueckwaertskanten leer sein.
    rest = [k.id for k in karten if k.id not in set(topo)]
    topo.extend(sorted(rest, key=lambda i: reihenfolge[i]))

    # Schicht = laengster Weg von einer Wurzel.
    layer = {k.id: 0 for k in karten}
    for u in topo:
        for v in dag_succ[u]:
            if layer[u] + 1 > layer[v]:
                layer[v] = layer[u] + 1

    # Kritischer Pfad = laengste Kette, primaer nach Schaetzungs-Summe, sekundaer
    # nach Anzahl Karten (damit auch ohne Schaetzungen die laengste Kette gewinnt).
    gewicht = {k.id: max(int(k.schaetzung_min or 0), 0) for k in karten}
    dist: dict[str, tuple[int, int]] = {k.id: (gewicht[k.id], 1) for k in karten}
    cp_pred: dict[str, str | None] = {k.id: None for k in karten}
    for u in topo:
        for v in dag_succ[u]:
            kand = (dist[u][0] + gewicht[v], dist[u][1] + 1)
            if kand > dist[v]:
                dist[v] = kand
                cp_pred[v] = u

    # Endpunkt nur unter Knoten waehlen, deren laengste Kette mindestens zwei
    # Knoten (also eine Kante) hat. Sonst koennte ein schwerer, isolierter
    # Einzelknoten eine real existierende Kette verdraengen und den kritischen
    # Pfad faelschlich leeren.
    pfad: list[str] = []
    kandidaten = [i for i in topo if dist[i][1] >= 2]
    if kandidaten:
        ende = max(kandidaten, key=lambda i: (dist[i], -reihenfolge[i]))
        cur: str | None = ende
        while cur is not None:
            pfad.append(cur)
            cur = cp_pred[cur]
        pfad.reverse()
    pfad_set = set(pfad)
    pfad_kanten = {(pfad[i], pfad[i + 1]) for i in range(len(pfad) - 1)}
    dauer_min = dist[pfad[-1]][0] if pfad else 0

    # Alle Knoten eines Zyklus markieren, nicht nur die Endpunkte der Rueckkante:
    # je Rueckkante u->v den Vorwaertsweg v..u suchen und den ganzen Ring markieren.
    zyklus_knoten: set[str] = set()
    for u, v in back:
        vorg: dict[str, str | None] = {v: None}
        schlange = [v]
        while schlange:
            x = schlange.pop(0)
            if x == u:
                break
            for w in dag_succ[x]:
                if w not in vorg:
                    vorg[w] = x
                    schlange.append(w)
        if u in vorg:
            knoten: str | None = u
            while knoten is not None:
                zyklus_knoten.add(knoten)
                knoten = vorg[knoten]
        else:
            zyklus_knoten.add(u)
            zyklus_knoten.add(v)

    def status(k) -> str:
        if k.spalte in done:
            return "erledigt"
        offen = [b for b in pred[k.id] if by_id[b].spalte not in done]
        return "blockiert" if offen else "startklar"

    nodes = [
        {
            "id": k.id,
            "schluessel": k.schluessel,
            "titel": k.titel,
            "spalte": k.spalte,
            "schaetzung_min": int(k.schaetzung_min or 0),
            "blockiert_von": pred[k.id],
            "layer": layer[k.id],
            "status": status(k),
            "auf_kritischem_pfad": k.id in pfad_set,
            "in_zyklus": k.id in zyklus_knoten,
        }
        for k in sorted(karten, key=lambda x: (layer[x.id], reihenfolge[x.id]))
    ]

    edges = [
        {
            "von": kid,
            "nach": v,
            "auf_kritischem_pfad": (kid, v) in pfad_kanten,
            "zyklus": (kid, v) in back,
        }
        for kid in succ
        for v in succ[kid]
    ]

    return {
        "nodes": nodes,
        "edges": edges,
        "kritischer_pfad": {"karten": pfad, "dauer_min": dauer_min},
        "zyklus_kanten": [{"von": u, "nach": v} for u, v in sorted(back)],
        "layer_anzahl": (max(layer.values()) + 1) if karten else 0,
    }
