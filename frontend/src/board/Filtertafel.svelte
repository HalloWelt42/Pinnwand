<script lang="ts">
  // Filtertafel unter der Werkzeugleiste (Mechanik M-92 und M-93), als feste Leiste statt schwebend: Personen,
  // Prioritäten, Labels und die eigenen Auswahlfelder des Boards. Innerhalb einer Zeile reicht ein Treffer, über die
  // Zeilen muss alles passen. Angeboten wird alles, was das Board kennt (in der alten App fehlten Labels, die nur an
  // erledigten Karten hingen). Gilt in Board, Liste, Kalender und Zeitachse und wird je Board an diesem Gerät gemerkt.
  import { PRIORITAETEN } from "../anzeige";
  import type { Kartenfilter } from "../daten/abfragen";
  import { konto, mitKonto } from "../daten/stand.svelte";
  import type { Board } from "../modell";
  import { feldUmschalten, filterUmschalten, filterZuruecksetzen } from "./ansicht.svelte";
  import Person from "./Person.svelte";

  let { board, filter, schluessel, schliessen }: {
    board: Board; filter: Kartenfilter;
    schluessel: string; schliessen: () => void;
  } = $props();

  const auswahlfelder = $derived(board.felder.filter((f) => f.art === "auswahl" && f.optionen?.length));
  const gewaehlt = $derived(filter.personen.length + filter.prioritaeten.length + filter.labels.length
    + Object.values(filter.felder).reduce((n, w) => n + w.length, 0));
</script>

<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
<section class="pw-filtertafel" aria-label="Filter des Boards" onkeydown={(e) => { if (e.key === "Escape") schliessen(); }}>
  <div class="pw-filtertafel-zeile" role="group" aria-label="Personen">
    <span class="etikett" title="Karten, für die eine der gewählten Personen zuständig ist">Zuständig</span>
    {#each mitKonto(board) as m (m.konto)}
      <button class="chip" class:aktiv={filter.personen.includes(m.konto)} aria-pressed={filter.personen.includes(m.konto)}
              onclick={() => filterUmschalten(schluessel, "personen", m.konto)}><Person id={m.konto} />{konto(m.konto).name}</button>
    {/each}
  </div>
  <div class="pw-filtertafel-zeile" role="group" aria-label="Priorität">
    <span class="etikett">Priorität</span>
    {#each PRIORITAETEN.slice().reverse() as [p, name] (p)}
      <button class="chip" class:aktiv={filter.prioritaeten.includes(p)} aria-pressed={filter.prioritaeten.includes(p)}
              title={p === "keine" ? "Karten ohne Priorität" : undefined} onclick={() => filterUmschalten(schluessel, "prioritaeten", p)}>
        {#if p !== "keine"}<span class="pw-prio" data-prioritaet={p}></span>{/if}{p === "keine" ? "Ohne" : name}</button>
    {/each}
  </div>
  {#if board.labels.length}
    <div class="pw-filtertafel-zeile" role="group" aria-label="Labels">
      <span class="etikett">Labels</span>
      {#each board.labels as l (l.id)}
        <button class="chip" class:aktiv={filter.labels.includes(l.id)} aria-pressed={filter.labels.includes(l.id)} data-farbe={l.farbe}
                onclick={() => filterUmschalten(schluessel, "labels", l.id)}><span class="pw-farbpunkt"></span>{l.name}</button>
      {/each}
    </div>
  {/if}
  {#each auswahlfelder as f (f.id)}
    <div class="pw-filtertafel-zeile" role="group" aria-label={f.name}>
      <span class="etikett" title="Eigenes Feld des Boards">{f.name}</span>
      {#each f.optionen ?? [] as o (o)}
        <button class="chip" class:aktiv={filter.felder[f.id]?.includes(o)} aria-pressed={!!filter.felder[f.id]?.includes(o)}
                onclick={() => feldUmschalten(schluessel, f.id, o)}>{o}</button>
      {/each}
    </div>
  {/each}
  <div class="pw-filtertafel-fuss">
    <span class="schwach">In einer Zeile reicht eins, über die Zeilen gilt alles.</span>
    {#if gewaehlt}
      <button class="knopf ohne klein" onclick={() => filterZuruecksetzen(schluessel)} title="Personen, Prioritäten, Labels und Felder zurücksetzen; die Suche bleibt">
        <i class="fa-solid fa-filter-circle-xmark"></i>Filter zurücksetzen</button>
    {/if}
    <button class="knopf ohne klein" onclick={schliessen} title="Die Filter gelten weiter"><i class="fa-solid fa-chevron-up"></i>Einklappen</button>
  </div>
</section>
