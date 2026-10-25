<script lang="ts">
  // Ordner: deine Ordner der Seitenleiste in ihrer Reihenfolge (Ziehen am Griff), umbenennen, löschen mit Rückfrage in
  // der Fläche (ihre Boards stehen danach ohne Ordner), neu anlegen; darunter jedes deiner Boards mit seinem Ordner zum
  // Einsortieren, in der Ordnung der Seitenleiste. Ordner ordnen nur, sie tragen keine Rechte; die anderen sortieren für
  // sich. Alles über die Anwendungsfälle.
  import { dragHandle, dragHandleZone, type DndEvent } from "svelte-dnd-action";
  import { boardGruppen } from "../../../daten/abfragen";
  import {
    ordnerAnlegen, ordnerLoeschen, ordnerOrdnen, ordnerSetzen, ordnerUmbenennen,
  } from "../../../daten/anwendung/boards.svelte";
  import { ordnerVon, stand } from "../../../daten/stand.svelte";
  import type { Ordner } from "../../../modell";

  // Ziehen ordnet erst die Anzeige, das Ablegen ruft den Anwendungsfall; danach gilt die Reihenfolge des Servers
  let items = $state<Ordner[]>([]);
  $effect(() => { items = [...stand.ordner]; });
  function erwaegen(e: CustomEvent<DndEvent<Ordner>>): void { items = e.detail.items; }
  async function abgelegt(e: CustomEvent<DndEvent<Ordner>>): Promise<void> {
    items = e.detail.items;
    await ordnerOrdnen(items.map((o) => o.id));
    items = [...stand.ordner];
  }

  const gruppen = $derived(boardGruppen());
  const boards = $derived(gruppen.flatMap((g) => g.boards));
  /** Boards eines Ordners, die du siehst */
  const inhalt = (o: Ordner) => gruppen.find((g) => g.ordner?.id === o.id)?.boards ?? [];
  const anzahl = (n: number) => `${n} ${n === 1 ? "Board" : "Boards"}`;

  async function umbenennen(o: Ordner, e: Event): Promise<void> {
    const feld = e.currentTarget as HTMLInputElement;
    if (feld.value.trim() === o.name || !(await ordnerUmbenennen(o.id, feld.value))) feld.value = o.name;
  }

  let loeschen = $state<string | null>(null);
  async function loeschenBestaetigen(o: Ordner): Promise<void> {
    if (await ordnerLoeschen(o.id)) loeschen = null;
  }

  let neuName = $state("");
  async function anlegen(): Promise<void> {
    if (await ordnerAnlegen(neuName)) neuName = "";
  }
</script>

<div class="rollfeld">
  <div class="pw-verwaltung-flaeche">
    <p class="pw-verwaltung-satz"><i class="fa-solid fa-circle-info"></i>Ordner ordnen nur deine Seitenleiste; sie tragen keine Rechte, und die
      anderen Mitglieder sortieren ihre Boards für sich. Boards ohne Ordner stehen dort zuletzt unter "Ohne Ordner".</p>

    <section class="bereich">
      <h2 class="etikett">Deine Ordner</h2>
      <div class="pw-verwaltung-liste" use:dragHandleZone={{ items, flipDurationMs: 160, type: "ordner", dropTargetStyle: {} }}
           onconsider={erwaegen} onfinalize={abgelegt}>
        {#each items as o (o.id)}
          {@const drin = inhalt(o)}
          <article class="pw-verwaltung-eintrag" class:gefahr={loeschen === o.id} aria-label="Ordner {o.name}">
            <div class="oben">
              <span class="pw-verwaltung-griff" use:dragHandle aria-label="Ordner {o.name} ziehen zum Umsortieren" title="Ziehen zum Umsortieren">
                <i class="fa-solid fa-grip-vertical"></i></span>
              <i class="fa-solid fa-folder pw-verwaltung-artsymbol"></i>
              <input class="eingabe pw-verwaltung-name" value={o.name} aria-label="Name des Ordners {o.name}" onchange={(e) => umbenennen(o, e)} />
              <span class="pw-angabe flaeche" title={drin.map((b) => b.name).join(", ") || "Noch leer"}>
                <i class="fa-solid fa-table-columns"></i>{anzahl(drin.length)}</span>
              <button class="knopf ohne symbol klein" title="Ordner {o.name} löschen" aria-label="Ordner {o.name} löschen" disabled={loeschen === o.id}
                      onclick={() => (loeschen = o.id)}><i class="fa-solid fa-trash-can"></i></button>
            </div>
            {#if loeschen === o.id}
              <div class="hinweis gefahr pw-verwaltung-rueckfrage" role="alert"><i class="fa-solid fa-trash-can"></i>
                <div><b>Ordner {o.name} löschen?</b>
                  {#if drin.length}{drin.length === 1 ? "Sein Board" : `Seine ${drin.length} Boards`} ({drin.map((b) => b.name).join(", ")})
                    {drin.length === 1 ? "steht" : "stehen"} danach ohne Ordner; an den Boards ändert sich nichts.{:else}Er ist leer.{/if}</div>
                <span class="rechts"><button class="knopf klein" onclick={() => (loeschen = null)}>Abbrechen</button>
                  <button class="knopf gefahr-voll klein" onclick={() => loeschenBestaetigen(o)}><i class="fa-solid fa-trash-can"></i>Ordner löschen</button></span>
              </div>
            {/if}
          </article>
        {:else}
          <div class="leer"><i class="fa-solid fa-folder"></i><p>Noch keine Ordner. Lege unten den ersten an; bis dahin stehen deine Boards unter
            "Ohne Ordner".</p></div>
        {/each}
      </div>
      <div class="pw-verwaltung-formular">
        <input class="eingabe" bind:value={neuName} placeholder="Name des Ordners" aria-label="Name des neuen Ordners"
               onkeydown={(e) => { if (e.key === "Enter") void anlegen(); }} />
        <button class="knopf haupt" disabled={!neuName.trim()} onclick={anlegen}><i class="fa-solid fa-plus"></i>Ordner anlegen</button>
      </div>
      <p class="pw-verwaltung-satz">Ein neuer Ordner kommt ans Ende; am Griff ziehen ordnet die Ordner in der Seitenleiste.</p>
    </section>

    {#if boards.length}
      <section class="bereich">
        <h2 class="etikett">Boards einsortieren</h2>
        {#each boards as b (b.id)}
          <div class="einstellung">
            <div><div class="name"><span class="pw-farbpunkt" data-farbe={b.farbe}></span>{b.name}</div>
              <div class="erklaerung">Kürzel <span class="pw-schluessel">{b.kuerzel}</span></div></div>
            <div class="wert">
              <select class="eingabe" value={ordnerVon(b.id)?.id ?? ""} aria-label="Ordner von {b.name}"
                      onchange={(ev) => ordnerSetzen(b.id, (ev.currentTarget as HTMLSelectElement).value)}>
                {#each stand.ordner as o (o.id)}<option value={o.id}>{o.name}</option>{/each}
                <option value="">Ohne Ordner</option>
              </select>
            </div>
          </div>
        {/each}
      </section>
    {/if}
  </div>
</div>
