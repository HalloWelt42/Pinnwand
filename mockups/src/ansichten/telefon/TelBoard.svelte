<script lang="ts">
  // Ein Board am Telefon, spaltenweise: oben die Spalten als Reiter mit Zahl (offene Karten und Grenze), darunter die
  // Karten der gewählten Spalte groß und lesbar; Wischen nach links oder rechts wechselt die Spalte. Die gewählte Spalte
  // bleibt je Board gemerkt. Verschoben wird im Kartendetail; Erledigt zeigt das Zeitfenster des Boards.
  import { sichtbareKarten } from "../../beispiel/abfragen";
  import { board, kartenDerSpalte, ordnerVon } from "../../beispiel/stand.svelte";
  import { ZEITFENSTER } from "../../anzeige";
  import type { Spalte } from "../../modell";
  import { geraet } from "./geraet.svelte";
  import TelefonSchale from "./TelefonSchale.svelte";
  import TelKarte from "./TelKarte.svelte";
  import { telPfad } from "./weg";
  import { wischen } from "./wischen";

  let { boardId }: { boardId: string } = $props();

  const b = $derived(board(boardId));
  const aktiv = $derived(b.spalten.find((s) => s.id === geraet.spalte[b.id]) ?? b.spalten.find((s) => !s.erledigt) ?? b.spalten[0]);
  /** offene Spalten zeigen alle Karten, Erledigt-Spalten ihr Zeitfenster */
  const karten = $derived(sichtbareKarten(b, aktiv));
  const ordner = $derived(ordnerVon(b.id)?.name ?? "");
  const zahl = (s: Spalte): number => (s.erledigt ? sichtbareKarten(b, s) : kartenDerSpalte(s.id)).length;
  const ueber = (s: Spalte): boolean => !s.erledigt && s.grenze !== undefined && zahl(s) > s.grenze;

  function waehlen(s: Spalte): void { geraet.spalte[b.id] = s.id; }
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

<TelefonSchale titel={b.name} unter="{b.kuerzel} · {ordner}" reiter="boards" zurueck={telPfad("/boards")}>
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
    {#if aktiv.erledigt}
      <div class="pw-tel-fenster schwach"><i class="fa-solid fa-circle-check"></i>Zeitfenster: {ZEITFENSTER[aktiv.zeitfenster ?? "woche"]}</div>
    {/if}
    {#each karten as k (k.id)}
      <TelKarte karte={k} von="board" />
    {:else}
      <div class="leer"><i class="fa-regular fa-folder-open"></i><p>Keine Karten in {aktiv.name}.</p></div>
    {/each}
    {#if !aktiv.erledigt}
      <a class="knopf pw-tel-breit" href={telPfad("/erfassen", { board: b.kuerzel.toLowerCase(), spalte: aktiv.id })}><i class="fa-solid fa-plus"></i>Karte in {aktiv.name}</a>
    {/if}
  </div>
</TelefonSchale>
