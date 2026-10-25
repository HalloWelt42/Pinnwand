<script lang="ts">
  // Labels des Boards mit Name und Farbe: anlegen, umbenennen und umfärben (gilt sofort auf allen Karten, denn Karten
  // tragen das Label, nicht seinen Text), löschen mit Rückfrage, die sagt, an welchen Karten es hängt. Namen sind ohne
  // Beachtung von Groß und klein eindeutig. Alles über die Anwendungsfälle.
  import { untrack } from "svelte";
  import { labelAendern, labelAnlegen, labelLoeschen, labelVergeben } from "../../../daten/anwendung/boards.svelte";
  import { stand } from "../../../daten/stand.svelte";
  import type { Board, Farbe, Label } from "../../../modell";
  import Farbwahl from "../../../teile/Farbwahl.svelte";

  let { board }: { board: Board } = $props();

  const tragen = (id: string) => stand.karten.filter((k) => k.board === board.id && k.labels.includes(id));

  async function umbenennen(l: Label, e: Event): Promise<void> {
    const feld = e.currentTarget as HTMLInputElement;
    if (feld.value.trim() === l.name || !(await labelAendern(board.id, l.id, { name: feld.value }))) feld.value = l.name;
  }
  async function loeschenBestaetigen(l: Label): Promise<void> {
    if (await labelLoeschen(board.id, l.id)) loeschen = null;
  }

  let loeschen = $state<string | null>(null);
  $effect(() => { board.id; untrack(() => (loeschen = null)); });

  let neuName = $state("");
  let neuFarbe = $state<Farbe>("himmel");
  const neuDoppelt = $derived(neuName.trim() ? labelVergeben(board, neuName) : undefined);
  async function anlegen(): Promise<void> {
    if (await labelAnlegen(board.id, neuName, neuFarbe)) neuName = "";
  }
</script>

<div class="rollfeld">
  <div class="pw-verwaltung-flaeche">
    <p class="pw-verwaltung-satz"><i class="fa-solid fa-circle-info"></i>Karten tragen das Label selbst: Umbenennen und Umfärben gelten sofort
      auf allen Karten, auch im Filter.</p>

    <div class="pw-verwaltung-liste">
      {#each board.labels as l (l.id)}
        {@const n = tragen(l.id).length}
        <article class="pw-verwaltung-eintrag" class:gefahr={loeschen === l.id} aria-label="Label {l.name}">
          <div class="oben">
            <span class="pw-label" data-farbe={l.farbe}>{l.name}</span>
            <input class="eingabe pw-verwaltung-name" value={l.name} aria-label="Name des Labels {l.name}" onchange={(e) => umbenennen(l, e)} />
            <Farbwahl kompakt wert={l.farbe} waehlen={(f) => f && labelAendern(board.id, l.id, { farbe: f })} wofuer="Farbe des Labels {l.name}" />
            <span class="pw-angabe flaeche" title="Karten mit diesem Label"><i class="fa-regular fa-note-sticky"></i>an {n} {n === 1 ? "Karte" : "Karten"}</span>
            <button class="knopf ohne symbol klein" title="Label {l.name} löschen" aria-label="Label {l.name} löschen" disabled={loeschen === l.id}
                    onclick={() => (loeschen = l.id)}><i class="fa-solid fa-trash-can"></i></button>
          </div>
          {#if loeschen === l.id}
            <div class="hinweis gefahr pw-verwaltung-rueckfrage" role="alert"><i class="fa-solid fa-trash-can"></i>
              <div><b>Label {l.name} löschen?</b>
                {#if n}Es hängt an {n === 1 ? "einer Karte" : `${n} Karten`} ({tragen(l.id).map((k) => k.schluessel).join(", ")}); dort fällt es weg,
                  sonst ändert sich nichts an den Karten.{:else}Keine Karte trägt es.{/if}</div>
              <span class="rechts"><button class="knopf klein" onclick={() => (loeschen = null)}>Abbrechen</button>
                <button class="knopf gefahr-voll klein" onclick={() => loeschenBestaetigen(l)}>
                  <i class="fa-solid fa-trash-can"></i>Label löschen</button></span>
            </div>
          {/if}
        </article>
      {:else}
        <div class="leer"><i class="fa-solid fa-tags"></i><p>Noch keine Labels. Lege unten das erste an.</p></div>
      {/each}
    </div>

    <section class="bereich">
      <h2 class="etikett">Neues Label</h2>
      <div class="pw-verwaltung-formular">
        {#if neuName.trim()}<span class="pw-label" data-farbe={neuFarbe}>{neuName.trim()}</span>{/if}
        <input class="eingabe" bind:value={neuName} placeholder="Name des Labels" aria-label="Name des neuen Labels"
               onkeydown={(e) => { if (e.key === "Enter") anlegen(); }} />
        <button class="knopf haupt" disabled={!neuName.trim() || !!neuDoppelt} onclick={anlegen}><i class="fa-solid fa-plus"></i>Label anlegen</button>
      </div>
      {#if neuDoppelt}<span class="pw-verwaltung-fehler" role="alert">Das Label {neuDoppelt} gibt es schon; Groß und klein zählen nicht.</span>{/if}
      <div class="pw-verwaltung-formular">
        <span class="etikett">Farbe</span><Farbwahl wert={neuFarbe} waehlen={(f) => f && (neuFarbe = f)} wofuer="Farbe des neuen Labels" />
      </div>
    </section>
  </div>
</div>
