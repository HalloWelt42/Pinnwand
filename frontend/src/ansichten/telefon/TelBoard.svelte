<script lang="ts">
  // Ein Board am Telefon, spaltenweise: oben die Spalten als Reiter mit Zahl (offene Karten und Grenze), darunter die
  // Karten der gewählten Spalte groß und lesbar; Wischen nach links oder rechts wechselt die Spalte. Die gewählte Spalte
  // bleibt je Board gemerkt. Verschoben wird im Kartendetail; Erledigt zeigt das Zeitfenster des Boards. Die Karten
  // stehen in der Sortierung der Spalte (HELF-50, wie im Board an diesem Gerät, umstellbar über das Symbol) und laden
  // seitenweise nach dem Ladeschritt des Boards, beim Rollen ans Ende die nächsten.
  import { untrack } from "svelte";
  import { sichtbareKarten, spaltenOrdnung } from "../../daten/abfragen";
  import { ansichtEinrichten, ansichtVon, sortierungSetzen, sortierungVon } from "../../board/ansicht.svelte";
  import SortierWahl from "../../board/SortierWahl.svelte";
  import { nachladen } from "../../teile/nachladen";
  import { board, kartenDerSpalte, ordnerVon } from "../../daten/stand.svelte";
  import { ZEITFENSTER } from "../../anzeige";
  import type { Spalte } from "../../modell";
  import { geraet, geraetMerken } from "./geraet.svelte";
  import TelefonSchale from "./TelefonSchale.svelte";
  import TelKarte from "./TelKarte.svelte";
  import { telPfad } from "./weg";
  import { wischen } from "./wischen";

  let { boardId }: { boardId: string } = $props();

  const b = $derived(board(boardId));
  const aktiv = $derived(b.spalten.find((s) => s.id === geraet.spalte[b.id]) ?? b.spalten.find((s) => !s.erledigt) ?? b.spalten[0]);
  $effect.pre(() => { const brett = b; untrack(() => ansichtEinrichten(brett)); });
  const ansicht = $derived(ansichtVon(b.id));
  const art = $derived(sortierungVon(ansicht, aktiv));
  /** offene Spalten zeigen alle Karten, Erledigt-Spalten ihr Zeitfenster; in der Sortierung der Spalte */
  const karten = $derived(spaltenOrdnung(sichtbareKarten(b, aktiv), art));
  // seitenweise; eine andere Spalte oder Sortierung fängt vorn an
  const ladeSchluessel = $derived(`${aktiv.id}|${art}`);
  let geladen = $state({ fuer: "", seiten: 1 });
  const seiten = $derived(geladen.fuer === ladeSchluessel ? geladen.seiten : 1);
  const gezeigt = $derived(karten.slice(0, seiten * b.einstellungen.ladeschritt));
  function mehrLaden(): void {
    if (gezeigt.length < karten.length) geladen = { fuer: ladeSchluessel, seiten: seiten + 1 };
  }
  const ordner = $derived(ordnerVon(b.id)?.name ?? "");
  const zahl = (s: Spalte): number => (s.erledigt ? sichtbareKarten(b, s) : kartenDerSpalte(s.id)).length;
  const ueber = (s: Spalte): boolean => !s.erledigt && s.grenze !== undefined && zahl(s) > s.grenze;

  function waehlen(s: Spalte): void {
    geraet.spalte[b.id] = s.id;
    geraetMerken();
  }
  function nachbar(schritt: number): void {
    const i = b.spalten.indexOf(aktiv) + schritt;
    if (i >= 0 && i < b.spalten.length) waehlen(b.spalten[i]);
  }

  // die gewählte Spalte rückt im Streifen in Sicht (nur der Streifen rollt, nie die Seite)
  let streifen = $state<HTMLElement>();
  $effect(() => {
    const knopf = streifen?.querySelector<HTMLElement>(`[data-spalte="${aktiv.id}"]`);
    if (streifen && knopf) streifen.scrollLeft = knopf.offsetLeft - (streifen.clientWidth - knopf.offsetWidth) / 2;
  });
</script>

<TelefonSchale titel={b.name} unter={ordner ? `${b.kuerzel} · ${ordner}` : b.kuerzel} reiter="boards" zurueck={telPfad("/boards")}>
  {#snippet leiste()}
    <div class="pw-tel-spalten" bind:this={streifen} aria-label="Spalten des Boards">
      {#each b.spalten as s (s.id)}
        <button data-spalte={s.id} data-farbe={s.farbe} class:aktiv={s.id === aktiv.id} aria-pressed={s.id === aktiv.id} onclick={() => waehlen(s)}
                title={s.grenze !== undefined ? `Offene Karten und Grenze dieser Spalte` : `Karten in ${s.name}`}>
          <span class="pw-farbpunkt"></span>{s.name}
          <span class="zaehler" class:warnung={ueber(s)}>{zahl(s)}{s.grenze !== undefined ? `/${s.grenze}` : ""}</span>
        </button>
      {/each}
    </div>
  {/snippet}

  <div class="pw-tel-wischfeld" use:wischen={{ links: () => nachbar(1), rechts: () => nachbar(-1) }}>
    {#if ueber(aktiv)}
      <div class="hinweis warnung"><i class="fa-solid fa-triangle-exclamation"></i>
        <div>{aktiv.name} ist über der Grenze: <span class="zahl">{zahl(aktiv)}</span> offene Karten, Grenze <span class="zahl">{aktiv.grenze}</span>.</div></div>
    {/if}
    <div class="pw-tel-fenster schwach">
      {#if aktiv.erledigt}<i class="fa-solid fa-circle-check"></i>Zeitfenster: {ZEITFENSTER[aktiv.zeitfenster ?? "woche"]}{/if}
      <span class="rechts"><SortierWahl spalte={aktiv} {art} mitName setzen={(neu) => sortierungSetzen(b.id, aktiv, neu)} /></span>
    </div>
    {#each gezeigt as k (k.id)}
      <TelKarte karte={k} von="board" />
    {:else}
      <div class="leer"><i class="fa-regular fa-folder-open"></i><p>Keine Karten in {aktiv.name}.</p></div>
    {/each}
    {#if gezeigt.length < karten.length}
      <div class="pw-nachladen" use:nachladen={{ mehr: mehrLaden, gezeigt: gezeigt.length }}>
        <button class="knopf ohne" onclick={mehrLaden}><i class="fa-solid fa-angles-down"></i>{gezeigt.length} von {karten.length}, mehr laden</button>
      </div>
    {/if}
    {#if !aktiv.erledigt}
      <a class="knopf pw-tel-breit" href={telPfad("/erfassen", { board: b.kuerzel.toLowerCase(), spalte: aktiv.id })}><i class="fa-solid fa-plus"></i>Karte in {aktiv.name}</a>
    {/if}
  </div>
</TelefonSchale>
