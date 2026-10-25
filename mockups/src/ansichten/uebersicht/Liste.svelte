<script lang="ts">
  // Liste eines Boards unter Kopf und Werkzeugleiste des Boards: dieselben Karten wie die Spalten (offene und die
  // Erledigten im Zeitfenster der Spalte) als Tabelle mit Schlüssel, Titel, Status, Zuständig, Priorität, Fällig,
  // Labels, den eigenen Feldern des Boards und Zeit. Ein Klick auf den Spaltenkopf sortiert, ein zweiter dreht die
  // Richtung; Status sortiert nach der Spaltenfolge des Boards. Kopf und die ersten Spalten bleiben beim Rollen stehen.
  // Kästchen wählen Karten für Sammelaktionen (verschieben, zuweisen, Label, Priorität, Papierkorb); ein Klick auf eine
  // Zeile öffnet die Karte über ihren Pfad.
  import { kartenNummer, laufendAuf, passt, sichtbareKarten, woerter, zeitDerKarte } from "../../beispiel/abfragen";
  import { sammelLabel, sammelPrioritaet, sammelVerschieben, sammelZuweisen } from "../../beispiel/anwendung/karten.svelte";
  import { inPapierkorb } from "../../beispiel/anwendung/papierkorb.svelte";
  import { dauer, datum, faelligText } from "../../beispiel/format";
  import { konto } from "../../beispiel/stand.svelte";
  import Person from "../../board/Person.svelte";
  import { PRIORITAETEN, ZEITFENSTER } from "../../anzeige";
  import type { Board, Karte, Prioritaet, Spalte } from "../../modell";
  import Personenwahl from "../../teile/Personenwahl.svelte";
  import { boardPfad, gehe } from "../../weg.svelte";

  let { board, entwurf = "", suche = "" }: { board: Board; entwurf?: string; suche?: string } = $props();

  /** vorgeführter Zustand "auswahl": drei Karten gewählt, die Sammelleiste zeigt ihre Aktionen */
  const VORGABE_AUSWAHL = ["c-148", "c-139", "c-122"];
  /** Name und Rang je Priorität (dringend zuerst) */
  const PRIO = Object.fromEntries(PRIORITAETEN.map(([p, name], i) => [p, { name, rang: PRIORITAETEN.length - 1 - i }])) as
    Record<Prioritaet, { name: string; rang: number }>;

  interface Zeile { karte: Karte; spalte: Spalte; rang: number }
  // dieselben Karten wie die Spalten: offene alle, erledigte im Zeitfenster der Spalte; die Suche der Werkzeugleiste filtert
  const zeilen = $derived.by(() => {
    const w = woerter(suche);
    return board.spalten.flatMap((s, si) => sichtbareKarten(board, s).map((karte, i) => ({ karte, spalte: s, rang: si * 10000 + i })))
      .filter((z) => passt(z.karte, board, w));
  });
  const erledigtSpalte = $derived(board.spalten.find((s) => s.erledigt));
  const fertigZahl = $derived(zeilen.filter((z) => z.spalte.erledigt).length);
  const mitZeit = $derived(board.module.zeiterfassung);

  // Sortierung: Feld (fest oder Kennung eines eigenen Felds) und Richtung; Vorgabe Status aufsteigend
  let sortierung = $state({ feld: "status", auf: true });
  const SPALTEN = $derived([
    { feld: "schluessel", name: "Schlüssel", zahl: false }, { feld: "titel", name: "Titel", zahl: false },
    { feld: "status", name: "Status", zahl: false }, { feld: "zustaendig", name: "Zuständig", zahl: false },
    { feld: "prioritaet", name: "Priorität", zahl: false }, { feld: "faellig", name: "Fällig", zahl: false },
    { feld: "labels", name: "Labels", zahl: false },
    ...board.felder.map((f) => ({ feld: f.id, name: f.name, zahl: f.art === "zahl" })),
    ...(mitZeit ? [{ feld: "zeit", name: "Zeit", zahl: true }] : []),
  ]);

  function zeitSek(k: Karte): number {
    return zeitDerKarte(k.id);
  }
  function wert(z: Zeile, feld: string): string | number {
    const k = z.karte;
    switch (feld) {
      case "schluessel": return Number(k.schluessel.split("-")[1]);
      case "titel": return k.titel;
      case "status": return z.rang;
      case "zustaendig": return k.zustaendig.map((p) => konto(p).name).join(", ") || "￿";
      case "prioritaet": return PRIO[k.prioritaet].rang;
      case "faellig": return k.faellig ?? "9999";
      case "labels": return board.labels.find((l) => l.id === k.labels[0])?.name ?? "￿";
      case "zeit": return zeitSek(k);
    }
    const f = board.felder.find((x) => x.id === feld);
    const w = k.felder[feld] ?? "";
    return f?.art === "zahl" ? (w === "" ? Infinity : Number(w)) : w || "￿";
  }
  const sortiert = $derived([...zeilen].sort((a, b) => {
    const x = wert(a, sortierung.feld);
    const y = wert(b, sortierung.feld);
    const v = typeof x === "number" && typeof y === "number" ? x - y : String(x).localeCompare(String(y), "de");
    return (sortierung.auf ? v : -v) || a.rang - b.rang;
  }));
  function sortieren(feld: string): void {
    sortierung = { feld, auf: sortierung.feld === feld ? !sortierung.auf : true };
  }

  // Auswahl: räumt sich selbst auf, wenn Karten verschwinden (verschoben in ein anderes Board, im Papierkorb)
  let auswahl = $state<string[]>([]);
  // nur beim Wechsel des Entwurfs neu setzen, nicht bei jeder Änderung des Zustands (abgeleitet, damit gleiche Werte nicht wirken)
  const auswahlVorgefuehrt = $derived(entwurf === "auswahl");
  $effect(() => { auswahl = auswahlVorgefuehrt ? [...VORGABE_AUSWAHL] : []; });
  const gewaehlt = $derived(auswahl.filter((id) => zeilen.some((z) => z.karte.id === id)));
  const alleGewaehlt = $derived(zeilen.length > 0 && gewaehlt.length === zeilen.length);
  function umschalten(id: string): void {
    auswahl = auswahl.includes(id) ? auswahl.filter((x) => x !== id) : [...auswahl, id];
  }

  // Zuweisen: Textfeld mit Vorschlägen aus den Mitgliedern des Boards
  let person = $state("");
  const mitglieder = $derived(board.mitglieder.map((m) => ({ kennung: konto(m.konto).kellerwolke, name: konto(m.konto).name, konto: m.konto })));

  function pfad(k: Karte): string {
    return boardPfad(board.kuerzel, kartenNummer(k));
  }
  function gewaehltWert(e: Event & { currentTarget: HTMLSelectElement }, tun: (wert: string) => void): void {
    const w = e.currentTarget.value;
    e.currentTarget.value = "";
    if (w) tun(w);
  }
</script>

<div class="pw-uebersicht-flaeche">
  <div class="pw-uebersicht-sammel" class:aktiv={gewaehlt.length > 0} aria-label="Sammelaktionen">
    {#if gewaehlt.length}
      <span class="anzahl"><span class="zaehler akzent">{gewaehlt.length}</span>ausgewählt</span>
      <select class="eingabe" aria-label="Verschieben nach" onchange={(e) => gewaehltWert(e, (w) => sammelVerschieben(gewaehlt, w))}>
        <option value="">Verschieben nach ...</option>
        {#each board.spalten as s (s.id)}<option value={s.id}>{s.name}</option>{/each}
      </select>
      <div class="pw-uebersicht-person">
        <Personenwahl kandidaten={mitglieder} bind:text={person} platzhalter="Zuweisen: Name tippen"
                      waehlen={(p) => { if (p.konto) sammelZuweisen(gewaehlt, p.konto); }} />
      </div>
      <select class="eingabe" aria-label="Label setzen" onchange={(e) => gewaehltWert(e, (w) => sammelLabel(gewaehlt, w))}>
        <option value="">Label ...</option>
        {#each board.labels as l (l.id)}<option value={l.id}>{l.name}</option>{/each}
      </select>
      <select class="eingabe" aria-label="Priorität setzen" onchange={(e) => gewaehltWert(e, (w) => sammelPrioritaet(gewaehlt, w as Prioritaet))}>
        <option value="">Priorität ...</option>
        {#each PRIORITAETEN as [w, name] (w)}<option value={w}>{name}</option>{/each}
      </select>
      <span class="rechts">
        <button class="knopf ohne gefahr klein" title="Mit Zeiten, Kommentaren, Anhängen und Verknüpfungen; im Papierkorb wiederherstellbar"
                onclick={() => { inPapierkorb(gewaehlt); auswahl = []; }}><i class="fa-solid fa-trash-can"></i>In den Papierkorb</button>
        <button class="knopf ohne klein" onclick={() => (auswahl = [])}><i class="fa-solid fa-xmark"></i>Auswahl aufheben</button>
      </span>
    {:else}
      <span class="anzahl"><span class="zaehler">{zeilen.length}</span>Karten: {zeilen.length - fertigZahl} offen, {fertigZahl} erledigt
        {#if erledigtSpalte}<span class="schwach" title="Wie im Board: die Erledigt-Spalte zeigt ihr Zeitfenster">im Zeitfenster {ZEITFENSTER[erledigtSpalte.zeitfenster ?? "woche"]}</span>{/if}
        {#if suche}<span class="schwach">· Suche "{suche}"</span>{/if}</span>
      <span class="rechts schwach">Kästchen wählen für Sammelaktionen</span>
    {/if}
  </div>

  <div class="tabellen-raum pw-uebersicht-tabelle">
    <table class="tabelle pw-uebersicht-liste">
      <thead>
        <tr>
          <th class="sp-wahl"><input type="checkbox" checked={alleGewaehlt} aria-label="Alle auswählen"
                                  onchange={() => (auswahl = alleGewaehlt ? [] : zeilen.map((z) => z.karte.id))} /></th>
          {#each SPALTEN as s (s.feld)}
            <th class:zahl={s.zahl} class:sp-nr={s.feld === "schluessel"} class:sp-titel={s.feld === "titel"}
                aria-sort={sortierung.feld === s.feld ? (sortierung.auf ? "ascending" : "descending") : "none"}>
              <button class="pw-uebersicht-sort" class:aktiv={sortierung.feld === s.feld} onclick={() => sortieren(s.feld)}
                      title="Nach {s.name} sortieren">{s.name}<i class="fa-solid {sortierung.feld !== s.feld ? 'fa-sort' : sortierung.auf ? 'fa-sort-up' : 'fa-sort-down'}"></i></button>
            </th>
          {/each}
        </tr>
      </thead>
      <tbody>
        {#each sortiert as z (z.karte.id)}
          {@const k = z.karte}
          {@const faellig = k.faellig && !z.spalte.erledigt ? faelligText(k.faellig) : null}
          {@const sek = zeitSek(k)}
          {@const ueber = !!k.schaetzungMin && sek > k.schaetzungMin * 60}
          <!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_noninteractive_element_interactions -->
          <tr class:gewaehlt={gewaehlt.includes(k.id)} class:fertig={z.spalte.erledigt} onclick={() => gehe(pfad(k))}>
            <td class="sp-wahl"><input type="checkbox" checked={gewaehlt.includes(k.id)} aria-label="{k.schluessel} auswählen"
                                    onclick={(e) => e.stopPropagation()} onchange={() => umschalten(k.id)} /></td>
            <td class="sp-nr"><span class="pw-schluessel">{k.schluessel}</span></td>
            <td class="sp-titel">
              <a href={pfad(k)} onclick={(e) => e.stopPropagation()}>
                {#if k.art === "idee"}<i class="fa-solid fa-lightbulb pw-uebersicht-idee" title="Idee"></i>{/if}
                {#if k.blockiert}<i class="fa-solid fa-ban pw-uebersicht-blockiert" title="Blockiert: {k.blockiert}"></i>{/if}{k.titel}</a>
            </td>
            <td><span class="pw-uebersicht-status" data-farbe={z.spalte.farbe}><span class="pw-farbpunkt"></span>{z.spalte.name}</span></td>
            <td>{#if k.zustaendig.length}<span class="pw-personen" title={k.zustaendig.map((p) => konto(p).name).join(", ")}>
              {#each k.zustaendig as p (p)}<Person id={p} />{/each}</span>{:else}<span class="schwach">niemand</span>{/if}</td>
            <td>{#if k.prioritaet === "keine"}<span class="schwach">keine</span>
              {:else}<span class="pw-uebersicht-prio {k.prioritaet}"><i class="fa-solid fa-flag"></i>{PRIO[k.prioritaet].name}</span>{/if}</td>
            <td>
              {#if z.spalte.erledigt && k.abgeschlossen}<span class="pw-angabe gut" title="Abgeschlossen"><i class="fa-solid fa-check"></i>{datum(k.abgeschlossen, true)}</span>
              {:else if faellig}<span class="pw-angabe {faellig.klasse}"><i class="fa-regular fa-calendar"></i>{faellig.text}</span>{/if}
            </td>
            <td><span class="pw-uebersicht-labels">{#each k.labels as l (l)}{@const lab = board.labels.find((x) => x.id === l)}
              {#if lab}<span class="pw-label" data-farbe={lab.farbe}>{lab.name}</span>{/if}{/each}</span></td>
            {#each board.felder as f (f.id)}<td class:zahl={f.art === "zahl"} class:sp-text={f.art !== "zahl"}>{k.felder[f.id] ?? ""}</td>{/each}
            {#if mitZeit}
              <td class="zahl">
                {#if k.art === "arbeit" && (sek || k.schaetzungMin)}
                  {@const laeuft = laufendAuf(k.id)}
                  <span class="pw-uebersicht-zeit" class:laeuft={laeuft.length > 0} class:ueber
                        title={laeuft.length ? `Timer läuft: ${laeuft.map((t) => konto(t.konto).name).join(", ")}` : ueber ? "Über der Schätzung" : "Gebucht und Schätzung"}>
                    {#if laeuft.length}<i class="fa-solid fa-circle-play"></i>{:else if ueber}<i class="fa-solid fa-triangle-exclamation"></i>{/if}
                    {dauer(sek)}{#if k.schaetzungMin}<span class="soll"> / {dauer(k.schaetzungMin * 60)}</span>{/if}</span>
                {/if}
              </td>
            {/if}
          </tr>
        {:else}
          <tr><td colspan={SPALTEN.length + 1}><div class="leer"><i class="fa-solid fa-table-list"></i><p>{suche ? `Keine Karte passt zu "${suche}".` : "Keine Karten in diesem Board."}</p></div></td></tr>
        {/each}
      </tbody>
    </table>
  </div>
</div>
