<script lang="ts">
  // Checkliste der Karte (M-60): abhaken, ein Klick auf den Text benennt um (Enter oder Verlassen speichert, Escape
  // verwirft, leer wird abgewiesen), X entfernt mit Rückgängig, Enter im Feld darunter fügt an. Oben "n/m" und der
  // Fortschrittsbalken, grün wie auf der Karte. Jede Änderung über bearbeiten.
  import { tick } from "svelte";
  import { bearbeiten } from "../beispiel/anwendung/karten.svelte";
  import type { Karte, Punkt } from "../modell";
  import { verlassen, verwerfbar } from "../teile/verwerfen";

  let { karte, schreiben, ki = false }: { karte: Karte; schreiben: boolean; ki?: boolean } = $props();

  const erledigt = $derived(karte.checkliste.filter((p) => p.erledigt).length);
  const anteil = $derived(karte.checkliste.length ? erledigt / karte.checkliste.length : 0);
  let neu = $state("");
  /** welcher Punkt gerade umbenannt wird */
  let umbenennen = $state<number | null>(null);

  function setzen(liste: Punkt[], text: string): boolean {
    return bearbeiten(karte.id, { checkliste: liste }, text);
  }

  function umschalten(i: number): void {
    const liste = karte.checkliste.map((p, j) => (j === i ? { ...p, erledigt: !p.erledigt } : p));
    setzen(liste, liste[i].erledigt ? `Punkt "${liste[i].text}" erledigt` : `Punkt "${liste[i].text}" wieder offen`);
  }

  async function bearbeitenAb(i: number): Promise<void> {
    umbenennen = i;
    await tick();
    document.querySelector<HTMLInputElement>(`#pw-punkt-${karte.id}-${i}`)?.select();
  }

  /** neuer Name beim Verlassen; leer oder gleich bleibt der alte */
  function uebernehmen(i: number, feld: HTMLInputElement): void {
    umbenennen = null;
    const t = feld.value.trim();
    const alt = karte.checkliste[i]?.text;
    if (!t || t === alt) return;
    setzen(karte.checkliste.map((p, j) => (j === i ? { ...p, text: t } : p)), `Punkt "${alt}" heißt jetzt "${t}"`);
  }

  function entfernen(i: number): void {
    setzen(karte.checkliste.filter((_, j) => j !== i), `Punkt "${karte.checkliste[i].text}" entfernt`);
  }

  function hinzu(): void {
    const t = neu.trim();
    if (t && setzen([...karte.checkliste, { text: t, erledigt: false }], `Punkt "${t}" hinzugefügt`)) neu = "";
  }
</script>

<section class="pw-abschnitt">
  <div class="etikett">Checkliste {#if karte.checkliste.length}<span class="zaehler" class:erfolg={anteil === 1}>{erledigt}/{karte.checkliste.length}</span>{/if}
    {#if ki}<span class="rechts"><button class="knopf ohne klein" title="Vorschlag über die Leitstelle"><i class="fa-solid fa-wand-magic-sparkles"></i>Vorschlagen</button></span>{/if}
  </div>
  {#if karte.checkliste.length}
    <div class="pw-fortschritt pw-checkliste-balken" title="{Math.round(anteil * 100)} Prozent erledigt" role="progressbar" aria-label="Fortschritt der Checkliste"
         aria-valuemin={0} aria-valuemax={karte.checkliste.length} aria-valuenow={erledigt}><span style="width: {anteil * 100}%"></span></div>
  {/if}
  {#each karte.checkliste as p, i (i)}
    <div class="pw-punkt" class:erledigt={p.erledigt}>
      <input type="checkbox" checked={p.erledigt} disabled={!schreiben} aria-label="{p.text} {p.erledigt ? 'wieder öffnen' : 'abhaken'}" onchange={() => umschalten(i)} />
      {#if umbenennen === i}
        <input id="pw-punkt-{karte.id}-{i}" class="eingabe pw-punkt-name" value={p.text} aria-label="Punkt umbenennen" use:verwerfbar
               onblur={(e) => uebernehmen(i, e.currentTarget)} onkeydown={(e) => { if (e.key === "Enter") verlassen(e.currentTarget); }} />
      {:else if schreiben}
        <button class="pw-punkt-text" title="Klick benennt um" onclick={() => bearbeitenAb(i)}>{p.text}</button>
      {:else}
        <span class="pw-punkt-text">{p.text}</span>
      {/if}
      {#if schreiben && umbenennen !== i}
        <button class="knopf ohne symbol klein weg" title="Punkt entfernen (Rückgängig möglich)" onclick={() => entfernen(i)}><i class="fa-solid fa-xmark"></i></button>
      {/if}
    </div>
  {/each}
  {#if schreiben}
    <input class="eingabe" placeholder="Punkt hinzufügen, Enter" aria-label="Punkt hinzufügen" bind:value={neu} use:verwerfbar
           onkeydown={(e) => { if (e.key === "Enter") hinzu(); }} />
  {/if}
</section>
