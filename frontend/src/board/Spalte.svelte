<script lang="ts">
  // Eine Spalte: Kopf mit Griff, Farbe, Name, Zahl und Grenze aus allen Karten der Spalte (nie aus den Treffern einer
  // Suche), darunter der Füllbalken der Grenze; Einklappen und das Menü der Spalte. Erledigt-Spalten zeigen neueste
  // zuerst nach Abschluss, ihr Zeitfenster (bei Suche, Filter oder Sortierung alle außerhalb des Archivs) und laden
  // seitenweise nach dem Ladeschritt des Boards. Karten ziehen und ablegen über den einen Weg ablegen(); lehnt er ab
  // (getrennt), zeigt die Spalte wieder den Stand und die Karte springt zurück. Eingeklappt bleibt die Spalte Ablagezone,
  // mit einem Strich je Karte.
  import { dndzone, dragHandle, TRIGGERS, type DndEvent } from "svelte-dnd-action";
  import { ZEITFENSTER } from "../anzeige";
  import { darf, filterAktiv, spalteninhalt, type Kartenfilter, type Sortierung } from "../daten/abfragen";
  import { ablegen } from "../daten/anwendung/karten.svelte";
  import { kartenDerSpalte } from "../daten/stand.svelte";
  import type { Board, Karte as KarteT, Spalte, Zeitfenster } from "../modell";
  import { boardPfad } from "../weg.svelte";
  import { einklappen, fensterSetzen, fensterVon, istEingeklappt, type Ansichtszustand } from "./ansicht.svelte";
  import Karte from "./Karte.svelte";
  import { abheben, istSchatten } from "./schatten";
  import Schnelleingabe from "./Schnelleingabe.svelte";
  import SpaltenMenue from "./SpaltenMenue.svelte";

  let { board, spalte, ansicht, schluessel, filter, sortierung, ziehenGesperrt = false, darstellung = {}, oeffnen,
        menueOffen = false, menue }: {
    board: Board; spalte: Spalte;
    /** Ansichtszustand des Boards an diesem Gerät (eingeklappt, Zeitfenster) und sein Schlüssel zum Ändern */
    ansicht: Ansichtszustand; schluessel: string;
    /** Suche und Filter der Werkzeugleiste; Sortierung der offenen Spalten */
    filter: Kartenfilter; sortierung: Sortierung;
    ziehenGesperrt?: boolean;
    /** Darstellung einzelner Karten (offen: im Detail geöffnet) */
    darstellung?: Record<string, "offen">;
    oeffnen: (id: string) => void;
    /** das Menü dieser Spalte ist offen; menue() öffnet oder schließt es (eins zur Zeit, das Board weiß welches) */
    menueOffen?: boolean;
    menue: (offen: boolean) => void;
  } = $props();

  const verwalten = $derived(darf(board, "board.verwalten"));
  const sperre = $derived(ziehenGesperrt || !darf(board, "karten.verschieben"));
  const eingeklappt = $derived(istEingeklappt(ansicht, spalte));
  const fenster = $derived(fensterVon(ansicht, spalte));
  const inhalt = $derived(spalteninhalt(board, spalte, filter, sortierung, fenster));
  const gefiltert = $derived(filterAktiv(filter));
  let neuOffen = $state(false);
  let menueKnopf = $state<HTMLElement>();

  // Erledigt lädt seitenweise nach dem Ladeschritt des Boards (M-26); ein neues Fenster oder ein neuer Filter fängt vorn an
  const ladeschritt = $derived(board.einstellungen.ladeschritt);
  const ladeSchluessel = $derived(`${fenster}|${sortierung}|${JSON.stringify(filter)}`);
  let geladen = $state({ fuer: "", seiten: 1 });
  const seiten = $derived(geladen.fuer === ladeSchluessel ? geladen.seiten : 1);
  const gezeigt = $derived(spalte.erledigt ? inhalt.karten.slice(0, seiten * ladeschritt) : inhalt.karten);
  const weitere = $derived(inhalt.karten.length - gezeigt.length);
  function mehrLaden(): void {
    geladen = { fuer: ladeSchluessel, seiten: seiten + 1 };
  }
  function rollen(e: Event): void {
    const feld = e.currentTarget as HTMLElement;
    if (weitere > 0 && feld.scrollTop + feld.clientHeight >= feld.scrollHeight - 80) mehrLaden();
  }

  // Grenze (M-14): aus allen Karten der Spalte; Bernstein genau an der Grenze, rot darüber
  const grenze = $derived(spalte.erledigt ? undefined : spalte.grenze);
  const stufe = $derived(grenze === undefined ? "" : inhalt.alle > grenze ? "ueber" : inhalt.alle === grenze ? "voll" : "");
  const zahlKlasse = $derived(stufe === "ueber" ? "gefahr" : stufe === "voll" ? "akzent" : "");
  const zahlTitel = $derived(grenze === undefined
    ? spalte.erledigt ? `${inhalt.alle} erledigte Karten außerhalb des Archivs` : `${inhalt.alle} Karten in dieser Spalte`
    : stufe === "ueber" ? `${inhalt.alle} Karten bei Grenze ${grenze}: über der Grenze; sie warnt nur und hält nichts auf`
    : stufe === "voll" ? `${inhalt.alle} von ${grenze}: die Grenze ist erreicht, jede weitere Karte liegt darüber`
    : `${inhalt.alle} von höchstens ${grenze} Karten`);
  const geladenTitel = $derived(inhalt.ohneFenster ? `${gezeigt.length} geladen von ${inhalt.karten.length} passenden außerhalb des Archivs`
    : `${gezeigt.length} geladen von ${inhalt.karten.length} im Zeitfenster ${ZEITFENSTER[fenster]}; neueste zuerst nach Abschluss`);

  // Ziehen: während eines Zugs zeigt die Spalte, was die Bibliothek vorschlägt, sonst immer den Stand (M-70: lehnt ablegen()
  // ab, steht die Karte danach wieder an ihrem Platz)
  let zug = $state.raw<KarteT[] | null>(null);
  const items = $derived(zug ?? gezeigt);

  /** Erledigt hat eine feste Ordnung (M-28): eine eigene Karte bleibt an ihrem Platz, eine neue landet oben (heute erledigt) */
  function feststehend(vorschlag: KarteT[]): KarteT[] {
    const schatten = vorschlag.find(istSchatten);
    if (!schatten) return vorschlag;
    const rest = vorschlag.filter((k) => k !== schatten);
    rest.splice(Math.max(0, gezeigt.findIndex((k) => k.id === schatten.id)), 0, schatten);
    return rest;
  }
  function erwaegen(e: CustomEvent<DndEvent<KarteT>>): void {
    zug = spalte.erledigt ? feststehend(e.detail.items) : e.detail.items;
  }
  function abgelegt(e: CustomEvent<DndEvent<KarteT>>): void {
    const reihe = e.detail.items.filter((k) => !istSchatten(k)).map((k) => k.id);
    zug = null;
    // die Spalte, aus der eine Karte weggezogen wurde, meldet nichts: die Zielspalte legt ab (ein Weg, eine Meldung)
    if (e.detail.info.trigger === TRIGGERS.DROPPED_INTO_ANOTHER) return;
    const vorher = kartenDerSpalte(spalte.id).map((k) => k.id);
    if (spalte.erledigt) {
      const neu = reihe.filter((id) => !vorher.includes(id));
      if (neu.length) ablegen(spalte.id, [...vorher, ...neu]);
      return;
    }
    const danach = [...reihe, ...vorher.filter((id) => !reihe.includes(id))];
    if (danach.join() !== vorher.join()) ablegen(spalte.id, danach);
  }
</script>

{#if eingeklappt}
  <section class="pw-spalte eingeklappt" data-farbe={spalte.farbe} aria-label="Spalte {spalte.name}, eingeklappt">
    <div class="pw-spalte-kopf">
      {#if verwalten}
        <span class="pw-spalte-griff" use:dragHandle aria-label="Spalte {spalte.name} ziehen zum Umsortieren" title="Ziehen zum Umsortieren">
          <i class="fa-solid fa-grip-vertical"></i></span>
      {/if}
      <button class="pw-aufklappen" title="Spalte {spalte.name} aufklappen; Karten lassen sich auch eingeklappt hineinziehen"
              onclick={() => einklappen(schluessel, spalte.id, false)}>
        <i class="fa-solid fa-angles-right"></i>
        <span class="zaehler {zahlKlasse}" title={zahlTitel}>{inhalt.alle}{grenze !== undefined ? `/${grenze}` : ""}</span>
        <span class="senkrecht">{spalte.name}</span>
      </button>
    </div>
    <div class="pw-striche" use:dndzone={{ items, type: "karte", dragDisabled: true, dropFromOthersDisabled: sperre, flipDurationMs: 0,
                                         useCursorForDetection: true, zoneItemTabIndex: -1, dropTargetStyle: {}, dropTargetClasses: ["pw-ablagezone"] }}
         onconsider={erwaegen} onfinalize={abgelegt}>
      {#each items as k (k.id)}
        {#if istSchatten(k)}<span class="pw-strich pw-schatten"></span>{:else}<span class="pw-strich" title="{k.schluessel} {k.titel}"></span>{/if}
      {/each}
    </div>
  </section>
{:else}
  <section class="pw-spalte" data-farbe={spalte.farbe} aria-label="Spalte {spalte.name}">
    <div class="pw-spalte-kopf">
      {#if verwalten}
        <span class="pw-spalte-griff" use:dragHandle aria-label="Spalte {spalte.name} ziehen zum Umsortieren" title="Ziehen zum Umsortieren">
          <i class="fa-solid fa-grip-vertical"></i></span>
      {/if}
      <span class="pw-farbpunkt"></span>
      <span class="name" title={spalte.name}>{spalte.name}</span>
      <span class="zaehler {zahlKlasse}" title={zahlTitel}>{inhalt.alle}{grenze !== undefined ? `/${grenze}` : ""}</span>
      <span class="rechts">
        <button class="knopf ohne symbol klein" title="Einklappen: nur für dich an diesem Gerät" aria-label="Spalte {spalte.name} einklappen"
                onclick={() => einklappen(schluessel, spalte.id, true)}><i class="fa-solid fa-angles-left"></i></button>
        {#if verwalten}
          <button class="knopf ohne symbol klein" class:aktiv={menueOffen} bind:this={menueKnopf} aria-expanded={menueOffen} aria-haspopup="dialog"
                  title="Spalte bearbeiten: Name, Farbe, Grenze, Reihenfolge, löschen" aria-label="Menü der Spalte {spalte.name}"
                  onclick={() => menue(!menueOffen)}><i class="fa-solid fa-ellipsis"></i></button>
        {/if}
      </span>
    </div>
    {#if grenze !== undefined}
      <div class="pw-grenzbalken {stufe}" title={zahlTitel}><span style="width: {Math.min(100, (100 * inhalt.alle) / grenze)}%"></span></div>
    {/if}
    {#if menueOffen}
      <SpaltenMenue {board} {spalte} anker={menueKnopf} einklappen={() => einklappen(schluessel, spalte.id, true)} schliessen={() => menue(false)} />
    {/if}
    {#if spalte.erledigt}
      <div class="pw-spalte-leiste">
        {#if inhalt.ohneFenster}
          <span title="Bei Suche, Filter oder Sortierung zeigt die Spalte alle passenden Karten außerhalb des Archivs">Ohne Zeitfenster</span>
        {:else}
          <select class="eingabe" value={fenster} aria-label="Zeitfenster der Spalte {spalte.name}"
                  title="Zeitfenster: welche erledigten Karten du siehst; nur für dich an diesem Gerät"
                  onchange={(e) => fensterSetzen(schluessel, spalte.id, e.currentTarget.value as Zeitfenster)}>
            {#each Object.entries(ZEITFENSTER) as [w, n] (w)}<option value={w}>{n}</option>{/each}
          </select>
        {/if}
        <span class="pw-spalte-geladen" title={geladenTitel}>{gezeigt.length} von {inhalt.karten.length}</span>
      </div>
    {:else if gefiltert}
      <div class="pw-spalte-leiste"><span title="{inhalt.karten.length} von {inhalt.alle} Karten dieser Spalte passen zu Suche und Filter">
        {inhalt.karten.length} von {inhalt.alle} passen</span></div>
    {/if}
    <div class="pw-spalte-karten" use:dndzone={{ items, flipDurationMs: 160, type: "karte", dragDisabled: sperre, dropFromOthersDisabled: sperre,
                                               useCursorForDetection: true, dropTargetStyle: {}, transformDraggedElement: abheben("gezogen", ".pw-karte") }}
         onconsider={erwaegen} onfinalize={abgelegt} onscroll={rollen}>
      {#each items as k (k.id)}
        {#if istSchatten(k)}
          <div><div class="pw-karte platzhalter pw-schatten"><span>hier ablegen</span></div></div>
        {:else}
          <div><Karte karte={k} {board} erledigt={spalte.erledigt} art={darstellung[k.id] ?? ""} {oeffnen} aktionen /></div>
        {/if}
      {/each}
    </div>
    <div class="pw-spalte-fuss">
      {#if spalte.erledigt}
        {#if weitere > 0}
          <button class="knopf ohne klein" onclick={mehrLaden} title="Lädt die nächsten {ladeschritt} (Ladeschritt des Boards); Rollen ans Ende lädt auch">
            <i class="fa-solid fa-angles-down"></i>Mehr laden ({Math.min(weitere, ladeschritt)} weitere)</button>
        {/if}
        <div class="pw-mehr"><span>Älter als {board.einstellungen.archivTage} Tage im Archiv</span><a href={boardPfad(board.kuerzel, "archiv")}>Archiv</a></div>
      {:else if neuOffen}
        <Schnelleingabe {board} {spalte} schliessen={() => (neuOffen = false)} />
      {:else if darf(board, "karten.anlegen")}
        <button class="knopf ohne klein" onclick={() => (neuOffen = true)}><i class="fa-solid fa-plus"></i>Karte</button>
      {/if}
    </div>
  </section>
{/if}
