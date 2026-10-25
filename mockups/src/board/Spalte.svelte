<script lang="ts">
  // Eine Spalte: Kopf mit Farbe, Name, Zahl und Grenze, Einklappen und Menü; Erledigt-Spalten zeigen ihr Zeitfenster
  // (ältere Karten liegen im Archiv); Karten ziehen und ablegen über den einen Weg ablegen() (die Gruppe zieht mit,
  // Erledigt hält Timer an); unten Karte anlegen mit Schnelleingabe.
  import { dndzone, type DndEvent } from "svelte-dnd-action";
  import { erledigteOhneArchiv, passt, sichtbareKarten } from "../beispiel/abfragen";
  import { ablegen } from "../beispiel/anwendung/karten.svelte";
  import { gruppenmitglieder, karte, kartenDerSpalte } from "../beispiel/stand.svelte";
  import { ZEITFENSTER, ZEITFENSTER_VORGABE } from "../anzeige";
  import type { Board, Karte as KarteT, Spalte, Zeitfenster } from "../modell";
  import Karte from "./Karte.svelte";
  import Schnelleingabe from "./Schnelleingabe.svelte";
  import { boardPfad } from "../weg.svelte";

  let { board, spalte, schnell = false, suche = "", ziehenGesperrt = false, darstellung = {}, ziel, oeffnen }: {
    board: Board; spalte: Spalte; schnell?: boolean;
    /** Suche der Werkzeugleiste; Erledigte werden dabei ohne Zeitfenster durchsucht */
    suche?: string;
    ziehenGesperrt?: boolean;
    /** Darstellung einzelner Karten im Entwurf (gezogen, mitgezogen, offen, geaendert) */
    darstellung?: Record<string, "gezogen" | "mitgezogen" | "offen" | "geaendert">;
    /** Entwurf "Ziehen in Aktion": diese Karte wird gerade über dieser Spalte gehalten */
    ziel?: string;
    oeffnen: (id: string) => void;
  } = $props();
  const gezogen = $derived(ziel ? karte(ziel) : undefined);

  let eingeklappt = $state(false);
  let fenster = $state<Zeitfenster>(ZEITFENSTER_VORGABE);
  let neuOffen = $state(false);
  $effect(() => { eingeklappt = spalte.eingeklappt ?? false; fenster = spalte.zeitfenster ?? ZEITFENSTER_VORGABE; });
  $effect(() => { neuOffen = schnell; });
  let items = $state<KarteT[]>([]);
  $effect(() => {
    items = suche.trim() ? (spalte.erledigt ? erledigteOhneArchiv(board, spalte) : sichtbareKarten(board, spalte)).filter((k) => passt(k, board, suche))
      : sichtbareKarten(board, spalte, fenster);
  });

  const offene = $derived(spalte.erledigt ? 0 : items.length);
  const ueber = $derived(spalte.grenze !== undefined && offene > spalte.grenze);
  const geladen = $derived(spalte.erledigt ? erledigteOhneArchiv(board, spalte).length : items.length);

  function erwaegen(e: CustomEvent<DndEvent<KarteT>>): void { items = e.detail.items; }
  function abgelegt(e: CustomEvent<DndEvent<KarteT>>): void {
    items = e.detail.items;
    // die Spalte, aus der eine Karte weggezogen wurde, meldet nichts: die Zielspalte legt ab (ein Weg, eine Meldung)
    if (e.detail.info.trigger === "droppedIntoAnother") return;
    const sichtbar = items.map((k) => k.id);
    const ausserhalb = kartenDerSpalte(spalte.id).map((k) => k.id).filter((id) => !sichtbar.includes(id));
    ablegen(spalte.id, [...sichtbar, ...ausserhalb]);
  }
</script>

{#if eingeklappt}
  <section class="pw-spalte eingeklappt" data-farbe={spalte.farbe}>
    <div class="pw-spalte-kopf">
      <button class="knopf ohne symbol klein" title="Aufklappen" onclick={() => (eingeklappt = false)}><i class="fa-solid fa-angles-right"></i></button>
      <span class="pw-farbpunkt"></span>
      <span class="zaehler">{items.length}</span>
      <span class="senkrecht">{spalte.name}</span>
    </div>
  </section>
{:else}
  <section class="pw-spalte" class:ziel={!!ziel} data-farbe={spalte.farbe} aria-label="Spalte {spalte.name}">
    <div class="pw-spalte-kopf">
      <i class="fa-solid fa-grip-vertical griff" title="Spalte ziehen zum Umsortieren"></i>
      <span class="pw-farbpunkt"></span>
      <span class="name">{spalte.name}</span>
      {#if spalte.grenze !== undefined}
        <span class="zaehler pw-grenze" class:ueber title="Offene Karten und Grenze dieser Spalte">{offene}/{spalte.grenze}</span>
      {:else}
        <span class="zaehler">{items.length}</span>
      {/if}
      <span class="rechts">
        <button class="knopf ohne symbol klein" title="Einklappen" onclick={() => (eingeklappt = true)}><i class="fa-solid fa-angles-left"></i></button>
        <a class="knopf ohne symbol klein" href={boardPfad(board.kuerzel, "einstellungen/spalten")} title="Spalte bearbeiten: umbenennen, Farbe, Grenze, Erledigt-Spalte, löschen"><i class="fa-solid fa-ellipsis"></i></a>
      </span>
    </div>
    {#if spalte.erledigt}
      <div class="pw-spalte-leiste">
        <select class="eingabe" bind:value={fenster} title="Zeitfenster: welche erledigten Karten das Board zeigt">
          {#each Object.entries(ZEITFENSTER) as [w, n] (w)}<option value={w}>{n}</option>{/each}
        </select>
        <span title="Im Zeitfenster von allen erledigten außerhalb des Archivs">{items.length} von {geladen}</span>
      </div>
    {/if}
    <div class="pw-spalte-karten" use:dndzone={{ items, flipDurationMs: 160, type: "karte", dragDisabled: ziehenGesperrt, dropTargetStyle: {} }}
         onconsider={erwaegen} onfinalize={abgelegt}>
      {#if gezogen}
        <div class="pw-karte platzhalter pw-ablage">
          <span><b>{gezogen.schluessel}</b> hier ablegen</span>
          {#each gruppenmitglieder(gezogen) as m (m.id)}<span class="pw-angabe"><i class="fa-solid fa-link"></i>{m.schluessel} zieht mit</span>{/each}
        </div>
      {/if}
      {#each items as k (k.id)}
        <div><Karte karte={k} {board} erledigt={spalte.erledigt} art={darstellung[k.id] ?? ""} {oeffnen} /></div>
      {/each}
    </div>
    <div class="pw-spalte-fuss">
      {#if spalte.erledigt}
        <div class="pw-mehr"><span>Älter als {board.einstellungen.archivTage} Tage im Archiv</span><a href={boardPfad(board.kuerzel, "archiv")}>Archiv</a></div>
      {:else if neuOffen}
        <Schnelleingabe {board} {spalte} schliessen={() => (neuOffen = false)} />
      {:else}
        <button class="knopf ohne klein" onclick={() => (neuOffen = true)}><i class="fa-solid fa-plus"></i>Karte</button>
      {/if}
    </div>
  </section>
{/if}
