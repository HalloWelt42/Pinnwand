<script lang="ts">
  // Ein Board: fester Kopf (Name, Ansichten, Mitglieder, Einstellungen), Werkzeugleiste (Suche, Filter, Sortierung) und
  // der Spaltenstreifen oder eine andere Ansicht (Liste, Kalender, Zeitachse). Das Kartendetail fährt rechts über das
  // Board und hat seinen eigenen Pfad (/board/prod/131); Schließen führt zurück auf /board/prod.
  import { board, karte, stand } from "../beispiel/stand.svelte";
  import Kartendetail from "../detail/Kartendetail.svelte";
  import { boardPfad, gehe } from "../weg.svelte";
  import { BOARDANSICHTEN } from "./ansichten";
  import Person from "./Person.svelte";
  import Spalte from "./Spalte.svelte";
  import type { BoardZustand } from "./zustand";

  let { boardId, ansicht = "board", detail, entwurf = "" }: {
    boardId: string; ansicht?: string; detail?: string; entwurf?: string;
  } = $props();

  /** vorgeführte Zustände der Entwürfe (?entwurf=...) */
  const ENTWUERFE: Record<string, BoardZustand> = {
    bearbeiten: { bearbeiten: "beschreibung" },
    ziehen: { ziehen: { karte: "c-137", nach: "s-arbeit" } },
    schnell: { schnell: "s-eingang" },
    suche: { filter: "Gehäuse" },
    live: { fremd: "c-115", meldung: "Anna Berger hat PROD-115 geändert: fällig Mi 28.10." },
    konflikt: { konflikt: true },
    erledigt: { meldung: "PROD-131 erledigt: Timer angehalten, 0:44 gebucht" },
  };
  const zustand = $derived(ENTWUERFE[entwurf] ?? {});
  const b = $derived(board(boardId));
  const Andere = $derived(BOARDANSICHTEN[ansicht]);
  $effect(() => { if (zustand.meldung) stand.meldung = zustand.meldung; });

  function oeffnen(id: string): void {
    const k = karte(id);
    if (k) gehe(boardPfad(b.kuerzel, k.schluessel.split("-")[1]));
  }

  const darstellung = $derived.by(() => {
    const d: Record<string, "gezogen" | "mitgezogen" | "offen" | "geaendert"> = {};
    if (zustand.ziehen) {
      d[zustand.ziehen.karte] = "gezogen";
      const g = karte(zustand.ziehen.karte)?.gruppe;
      for (const k of stand.karten) if (g && k.gruppe === g && k.id !== zustand.ziehen.karte) d[k.id] = "mitgezogen";
    }
    if (zustand.fremd) d[zustand.fremd] = "geaendert";
    if (detail) d[detail] = "offen";
    return d;
  });
  const ANSICHTEN = [["board", "Board", "fa-table-columns"], ["liste", "Liste", "fa-table-list"], ["kalender", "Kalender", "fa-calendar-days"],
    ["zeitachse", "Zeitachse", "fa-bars-progress"]] as const;
  const eigeneRolle = $derived(b.rollen.find((r) => r.id === b.mitglieder.find((m) => m.konto === "k-max")?.rolle)?.name ?? "");
</script>

<div class="rahmen-kopf">
  <div class="seitenkopf pw-boardkopf">
    <h1><span class="pw-farbpunkt" data-farbe={b.farbe}></span>{b.name}</h1>
    <nav class="reiter" style="margin: 0" aria-label="Ansichten des Boards">
      {#each ANSICHTEN as [id, name, symbol] (id)}
        <a class="knopf ohne" class:aktiv={ansicht === id} href={boardPfad(b.kuerzel, id === "board" ? "" : id)}><i class="fa-solid {symbol}"></i>{name}</a>
      {/each}
    </nav>
    <div class="rechts">
      <span class="pw-personen" title="Mitglieder">{#each b.mitglieder as m (m.konto)}<Person id={m.konto} />{/each}</span>
      <a class="knopf klein" href={boardPfad(b.kuerzel, "einstellungen/mitglieder")}><i class="fa-solid fa-user-plus"></i>Einladen</a>
      <a class="knopf symbol klein" href={boardPfad(b.kuerzel, "einstellungen")} title="Board-Einstellungen: Spalten, Felder, Labels, Rollen, Module"><i class="fa-solid fa-sliders"></i></a>
    </div>
    <div class="pfad"><i class="fa-solid fa-folder"></i>{b.ordner === "o-privat" ? "Privat" : "Firma"}<span class="pw-schluessel">Kürzel {b.kuerzel}</span>
      <span>· {b.mitglieder.length} {b.mitglieder.length === 1 ? "Mitglied" : "Mitglieder"} · du bist {eigeneRolle}</span></div>
  </div>
</div>
<div class="pw-werkzeuge">
  <label class="suche"><i class="fa-solid fa-magnifying-glass"></i><input placeholder="Im Board suchen: Titel, Inhalt, Labels, Kommentare" value={zustand.filter ?? ""} /></label>
  <button class="chip" class:aktiv={!!zustand.filter}><i class="fa-solid fa-filter"></i>Filter{#if zustand.filter}<span class="zaehler">1</span>{/if}</button>
  <button class="chip"><i class="fa-solid fa-user"></i>Alle Personen</button>
  <button class="chip"><i class="fa-solid fa-arrow-down-wide-short"></i>Manuell</button>
  {#if zustand.filter}
    <span class="pausiert" title="Bei Suche und Filter ist Ziehen gesperrt; die Erledigten werden ohne Zeitfenster durchsucht"><i class="fa-solid fa-hand"></i>Verschieben pausiert</span>
  {/if}
  <div class="rechts">
    <a class="chip" href={boardPfad(b.kuerzel, "archiv")}><i class="fa-solid fa-box-archive"></i>Archiv</a>
    <a class="chip" href={boardPfad(b.kuerzel, "papierkorb")}><i class="fa-solid fa-trash-can"></i>Papierkorb<span class="zaehler">2</span></a>
  </div>
</div>
<div class="pw-detail-raum">
  {#if Andere}
    <Andere board={b} {entwurf} />
  {:else}
    <div class="pw-streifen">
      {#each b.spalten as s (s.id)}
        <Spalte board={b} spalte={s} schnell={zustand.schnell === s.id} ziehenGesperrt={!!zustand.filter} {darstellung}
                ziel={zustand.ziehen?.nach === s.id ? zustand.ziehen.karte : undefined} {oeffnen} />
      {/each}
      <div class="pw-neue-spalte">
        <button class="knopf"><i class="fa-solid fa-plus"></i>Spalte</button>
      </div>
    </div>
  {/if}
  {#if detail}
    <Kartendetail kartenId={detail} board={b} bearbeiten={zustand.bearbeiten} konflikt={zustand.konflikt}
                  schliessen={() => gehe(boardPfad(b.kuerzel, ansicht === "board" ? "" : ansicht))} />
  {/if}
  {#if stand.meldung}
    <div class="pw-meldungen">
      <div class="pw-meldung"><i class="fa-solid fa-circle-info zeichen"></i><span>{stand.meldung}</span>
        <button class="knopf klein">Rückgängig</button>
        <button class="knopf ohne symbol klein" title="Schließen" onclick={() => (stand.meldung = "")}><i class="fa-solid fa-xmark"></i></button></div>
    </div>
  {/if}
</div>
