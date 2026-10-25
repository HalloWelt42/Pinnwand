<script lang="ts">
  // Ein Board: fester Kopf (Name, Ansichten, Mitglieder, Einstellungen), Werkzeugleiste (Suche, Filter, Personen,
  // Sortierung) mit der Filtertafel darunter und der Spaltenstreifen oder eine andere Ansicht (Liste, Kalender,
  // Zeitachse), die dieselben Filter bekommt. Suche, Filter, Sortierung, eingeklappte Spalten und Zeitfenster sind der
  // Ansichtszustand je Board an diesem Gerät (ansicht.svelte.ts). Solange gefiltert oder sortiert wird, ist Ziehen
  // gesperrt; ein Klick auf "Verschieben pausiert" setzt alles zurück. Spalten ordnen sich am Griff, neue entstehen am
  // Ende des Streifens. Das Kartendetail fährt rechts über das Board und hat seinen eigenen Pfad (/board/prod/131).
  import { untrack } from "svelte";
  import { dragHandleZone, type DndEvent } from "svelte-dnd-action";
  import { FARBEN } from "../anzeige";
  import { darf, filterAktiv, kartenNummer, papierkorbVon, type Sortierung } from "../daten/abfragen";
  import { spalteAnlegen, spaltenOrdnen } from "../daten/anwendung/boards.svelte";
  import { ICH } from "../daten/ich";
  import { board, karte, karteAusNummer, karteHolen, konto, mitKonto, ordnerVon } from "../daten/stand.svelte";
  import { melden } from "../daten/anwendung/meldung.svelte";
  import Kartendetail from "../detail/Kartendetail.svelte";
  import type { Farbe, Spalte as SpalteT } from "../modell";
  import Farbwahl from "../teile/Farbwahl.svelte";
  import { boardPfad, gehe } from "../weg.svelte";
  import { allesZuruecksetzen, ansichtEinrichten, ansichtVon, istEingeklappt, sucheSetzen, wirksamerFilter } from "./ansicht.svelte";
  import { BOARDANSICHTEN } from "./ansichten";
  import Filtertafel from "./Filtertafel.svelte";
  import { kette, ketteAbbrechen } from "./kette.svelte";
  import Person from "./Person.svelte";
  import { abheben, istSchatten } from "./schatten";
  import Spalte from "./Spalte.svelte";

  let { boardId, ansicht = "board", nummer = "" }: { boardId: string; ansicht?: string; nummer?: string } = $props();

  const b = $derived(board(boardId));
  const Andere = $derived(BOARDANSICHTEN[ansicht]);

  // Ansichtszustand je Board an diesem Gerät: vor dem Zeichnen eingerichtet
  const schluessel = $derived(boardId);
  $effect.pre(() => { const id = boardId; untrack(() => ansichtEinrichten(board(id))); });
  const a = $derived(ansichtVon(schluessel));
  const filter = $derived(wirksamerFilter(a.filter, b));
  const gefiltert = $derived(filterAktiv(filter));
  const gesperrt = $derived(gefiltert || (ansicht === "board" && a.sortierung !== "manuell"));
  const filterZahl = $derived(filter.prioritaeten.length + filter.labels.length + Object.values(filter.felder).reduce((n, w) => n + w.length, 0));
  const personenText = $derived(filter.personen.length === 0 ? "Alle Personen"
    : filter.personen.length === 1 ? konto(filter.personen[0]).name : `${filter.personen.length} Personen`);
  const SORTIERUNG_NAME: Record<Sortierung, string> = { manuell: "Manuell", faellig: "Fällig", prioritaet: "Priorität" };

  // Ansichtssachen: Filtertafel, offenes Spaltenmenü, Eingabe einer neuen Spalte
  let tafel = $state(false);
  let menue = $state<string | null>(null);
  let neueSpalte = $state(false);

  function oeffnen(id: string): void {
    const k = karte(id);
    if (k) gehe(boardPfad(b.kuerzel, kartenNummer(k)));
  }
  const zurueck = () => gehe(boardPfad(b.kuerzel, ansicht === "board" ? "" : ansicht));
  // liegt die offene Karte nicht mehr im Board (Papierkorb, von anderen gelöscht), schließt das Detail
  // die Karte im Pfad: liegt sie nicht im Zustand (archiviert), holt das Board sie einzeln; gibt es sie nicht (mehr) oder
  // verschwindet sie (Papierkorb, von anderen gelöscht), schließt das Detail
  const detail = $derived(nummer ? karteAusNummer(b, nummer)?.id : undefined);
  $effect(() => {
    if (!nummer || detail) return;
    const schluessel = `${b.kuerzel}-${nummer}`;
    void untrack(async () => {
      if (!(await karteHolen(schluessel)) && nummer && !karteAusNummer(b, nummer)) {
        melden(`Die Karte ${schluessel} gibt es nicht (mehr)`);
        zurueck();
      }
    });
  });

  const darstellung = $derived<Record<string, "offen">>(detail ? { [detail]: "offen" } : {});
  const ANSICHTEN = [["board", "Board", "fa-table-columns"], ["liste", "Liste", "fa-table-list"], ["kalender", "Kalender", "fa-calendar-days"],
    ["zeitachse", "Zeitachse", "fa-bars-progress"]] as const;
  const eigeneRolle = $derived(b.rollen.find((r) => r.id === b.mitglieder.find((m) => m.konto === ICH)?.rolle)?.name ?? "");
  const ordner = $derived(ordnerVon(b.id)?.name ?? "Ohne Ordner");
  const imPapierkorb = $derived(papierkorbVon(b.id).length);
  const verwalten = $derived(darf(b, "board.verwalten"));

  // Spalten am Griff ordnen (M-16): der Zug ordnet erst die Anzeige, das Ablegen ruft den Anwendungsfall
  let spaltenZug = $state.raw<SpalteT[] | null>(null);
  const spalten = $derived(spaltenZug ?? b.spalten);
  function spaltenErwaegen(e: CustomEvent<DndEvent<SpalteT>>): void { spaltenZug = e.detail.items; }
  async function spaltenAbgelegt(e: CustomEvent<DndEvent<SpalteT>>): Promise<void> {
    spaltenZug = e.detail.items;
    await spaltenOrdnen(b.id, spaltenZug.map((s) => s.id));
    spaltenZug = null;
  }

  // Neue Spalte (M-12): Name in der Fläche, Enter legt an, Escape bricht ab; ans Ende, ohne Grenze, offen
  let neuName = $state("");
  let neuFarbe = $state<Farbe>("himmel");
  function neueOeffnen(): void {
    neuName = "";
    neuFarbe = FARBEN.find((f) => !b.spalten.some((s) => s.farbe === f)) ?? "himmel";
    neueSpalte = true;
  }
  async function neueAnlegen(): Promise<void> {
    if (await spalteAnlegen(b.id, neuName, neuFarbe)) neueSpalte = false;
  }
  function neueTaste(e: KeyboardEvent): void {
    if (e.key === "Enter") neueAnlegen();
    if (e.key === "Escape") neueSpalte = false;
  }

  let breite = $state(1440);
  function taste(e: KeyboardEvent): void {
    if (e.key === "Escape" && kette.quelle) ketteAbbrechen();
  }
</script>

<svelte:window bind:innerWidth={breite} onkeydown={taste} />

<div class="rahmen-kopf">
  <div class="seitenkopf pw-boardkopf">
    <h1><span class="pw-farbpunkt" data-farbe={b.farbe}></span>{b.name}</h1>
    <nav class="reiter" aria-label="Ansichten des Boards">
      {#each ANSICHTEN as [id, name, symbol] (id)}
        <a class:aktiv={ansicht === id} href={boardPfad(b.kuerzel, id === "board" ? "" : id)}><i class="fa-solid {symbol}"></i>{name}</a>
      {/each}
    </nav>
    <div class="rechts">
      <span class="pw-personen" title="Mitglieder">{#each mitKonto(b) as m (m.konto)}<Person id={m.konto} />{/each}</span>
      {#if darf(b, "mitglieder.verwalten")}<a class="knopf klein" href={boardPfad(b.kuerzel, "einstellungen/mitglieder")}><i class="fa-solid fa-user-plus"></i>Einladen</a>{/if}
      <a class="knopf symbol klein" href={boardPfad(b.kuerzel, "einstellungen")} title="Board-Einstellungen: Spalten, Felder, Labels, Rollen, Module"><i class="fa-solid fa-sliders"></i></a>
    </div>
    <div class="pfad"><i class="fa-solid fa-folder"></i>{ordner}<span class="pw-schluessel">Kürzel {b.kuerzel}</span>
      <span>· {b.mitglieder.length} {b.mitglieder.length === 1 ? "Mitglied" : "Mitglieder"} · du bist {eigeneRolle}</span></div>
  </div>
</div>
<div class="pw-werkzeuge">
  <label class="suche"><i class="fa-solid fa-magnifying-glass"></i>
    <input placeholder="Im Board suchen: Titel, Inhalt, Labels, Kommentare" value={a.filter.suche} aria-label="Im Board suchen"
           oninput={(e) => sucheSetzen(schluessel, e.currentTarget.value)} onkeydown={(e) => { if (e.key === "Escape") sucheSetzen(schluessel, ""); }} /></label>
  <button class="chip" class:aktiv={filterZahl > 0} aria-expanded={tafel} onclick={() => (tafel = !tafel)}
          title="Filter nach Priorität, Labels und eigenen Feldern; gilt in Board, Liste, Kalender und Zeitachse">
    <i class="fa-solid fa-filter"></i>Filter{#if filterZahl}<span class="zaehler">{filterZahl}</span>{/if}</button>
  <button class="chip" class:aktiv={filter.personen.length > 0} aria-expanded={tafel} onclick={() => (tafel = !tafel)}
          title="Nur Karten bestimmter Personen zeigen (zuständig ist eine davon)">
    <i class="fa-solid {filter.personen.length > 1 ? 'fa-users' : 'fa-user'}"></i>{personenText}</button>
  {#if ansicht === "board"}
    <button class="chip" class:aktiv={a.sortierung !== "manuell"} aria-expanded={tafel} onclick={() => (tafel = !tafel)}
            title="Sortierung der offenen Spalten: Manuell, Fällig oder Priorität; Erledigt bleibt nach Abschluss">
      <i class="fa-solid fa-arrow-down-wide-short"></i>{SORTIERUNG_NAME[a.sortierung]}</button>
  {/if}
  <!-- der Platz bleibt auch ohne Sperre stehen, damit Werkzeugleiste und Tafel nicht springen, wenn sie erscheint -->
  <button class="pw-pausiert" class:frei={!gesperrt} disabled={!gesperrt} aria-hidden={!gesperrt} tabindex={gesperrt ? 0 : -1}
          onclick={() => allesZuruecksetzen(schluessel)}
          title="Bei Suche, Filter oder Sortierung ist Ziehen gesperrt und Erledigte zeigen alle außerhalb des Archivs. Klick setzt Suche, Filter, Personen und Sortierung zurück">
    <i class="fa-solid fa-lock"></i>Verschieben pausiert<i class="fa-solid fa-xmark"></i></button>
  <div class="rechts">
    <a class="chip" href={boardPfad(b.kuerzel, "archiv")}><i class="fa-solid fa-box-archive"></i>Archiv</a>
    <a class="chip" href={boardPfad(b.kuerzel, "papierkorb")}><i class="fa-solid fa-trash-can"></i>Papierkorb{#if imPapierkorb}<span class="zaehler">{imPapierkorb}</span>{/if}</a>
  </div>
</div>
{#if tafel}
  <Filtertafel board={b} {filter} sortierung={ansicht === "board" ? a.sortierung : undefined} {schluessel} schliessen={() => (tafel = false)} />
{/if}
<div class="pw-detail-raum">
  {#if Andere}
    <Andere board={b} {filter} ziehenGesperrt={gefiltert} />
  {:else}
    <div class="pw-streifen">
      <div class="pw-spaltenreihe" use:dragHandleZone={{ items: spalten, type: "spalte", flipDurationMs: 160, dragDisabled: !verwalten, useCursorForDetection: true, dropTargetStyle: {},
                                                         transformDraggedElement: abheben("pw-spalte-gezogen") }}
           onconsider={spaltenErwaegen} onfinalize={spaltenAbgelegt}>
        {#each spalten as s (s.id)}
          {#if istSchatten(s)}
            <section class="pw-spalte pw-spalten-platz" class:eingeklappt={istEingeklappt(a, s)} aria-label="Hier landet die Spalte {s.name}">
              <div class="pw-schatten"><i class="fa-solid fa-table-columns"></i>{istEingeklappt(a, s) ? "" : `${s.name} hier ablegen`}</div></section>
          {:else}
            <Spalte board={b} spalte={s} ansicht={a} {schluessel} {filter} sortierung={a.sortierung} ziehenGesperrt={gesperrt}
                    {darstellung} {oeffnen} menueOffen={menue === s.id} menue={(offen) => (menue = offen ? s.id : null)} />
          {/if}
        {/each}
      </div>
      {#if verwalten}
        <div class="pw-neue-spalte">
          {#if neueSpalte}
            <div class="pw-neue-spalte-flaeche">
              <!-- svelte-ignore a11y_autofocus -->
              <input class="eingabe" bind:value={neuName} autofocus placeholder="Name der neuen Spalte" aria-label="Name der neuen Spalte" onkeydown={neueTaste} />
              <Farbwahl kompakt wert={neuFarbe} waehlen={(f) => f && (neuFarbe = f)} wofuer="Farbe der neuen Spalte" />
              <div class="zeile-knoepfe">
                <button class="knopf haupt klein" disabled={!neuName.trim()} onclick={neueAnlegen}>Anlegen</button>
                <button class="knopf ohne klein" onclick={() => (neueSpalte = false)}>Abbrechen</button>
              </div>
              <span class="hinweistext">Kommt ans Ende, ohne Grenze und offen; Enter legt an, Escape bricht ab</span>
            </div>
          {:else}
            <button class="knopf" onclick={neueOeffnen} title="Neue Spalte am Ende anlegen"><i class="fa-solid fa-plus"></i>Spalte</button>
          {/if}
        </div>
      {/if}
    </div>
  {/if}
  {#if detail && karte(detail)}
    <Kartendetail kartenId={detail} board={b} schliessen={zurueck} />
  {/if}
</div>
{#if kette.quelle}
  {@const ziel = kette.ziel ? karte(kette.ziel) : undefined}
  <div class="pw-kettenmarke" class:bereit={!!ziel} class:links={kette.x > breite - 300} style="left: {kette.x}px; top: {kette.y}px" role="status">
    <i class="fa-solid fa-link"></i>{ziel ? `Hier verknüpfen: ${ziel.schluessel}` : "Auf eine Arbeitskarte ziehen"}</div>
{/if}
