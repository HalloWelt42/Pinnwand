<script lang="ts">
  // Checkliste der Karte (M-60): abhaken, ein Klick auf den Text benennt um (Enter oder Verlassen speichert, Escape
  // verwirft, leer wird abgewiesen), X entfernt mit Rückgängig, Enter im Feld darunter fügt an. Oben "n/m" und der
  // Fortschrittsbalken, grün wie auf der Karte. Jede Änderung über bearbeiten. Mit dem Modul KI an der Karte schlägt
  // "Vorschlagen" neue Punkte vor; übernommen werden nur die angehakten, ans Ende der Liste.
  import { tick } from "svelte";
  import { punkteHolen, Vorschlagslauf } from "../daten/anwendung/ki.svelte";
  import { bearbeiten } from "../daten/anwendung/karten.svelte";
  import type { Karte, Punkt } from "../modell";
  import { verlassen, verwerfbar } from "../teile/verwerfen";
  import Vorschlag from "./Vorschlag.svelte";

  let { karte, schreiben, ki = false }: {
    karte: Karte;
    schreiben: boolean;
    /** Vorschläge der KI gehen in diesem Board */
    ki?: boolean;
  } = $props();

  const erledigt = $derived(karte.checkliste.filter((p) => p.erledigt).length);
  const anteil = $derived(karte.checkliste.length ? erledigt / karte.checkliste.length : 0);
  let neu = $state("");
  /** welcher Punkt gerade umbenannt wird */
  let umbenennen = $state<number | null>(null);

  function setzen(liste: Punkt[], text: string): Promise<boolean> {
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

  const vorschlag = new Vorschlagslauf<{ punkte: string[] }>();
  /** welche vorgeschlagenen Punkte übernommen werden (anfangs alle) */
  let gewaehlt = $state<boolean[]>([]);
  $effect(() => () => vorschlag.schliessen());

  async function vorschlagen(): Promise<void> {
    if (await vorschlag.holen(punkteHolen(karte.id))) gewaehlt = vorschlag.wert?.punkte.map(() => true) ?? [];
  }

  async function vorschlagUebernehmen(punkte: string[]): Promise<void> {
    const neu = punkte.filter((_, i) => gewaehlt[i]);
    const text = neu.length === 1 ? `Punkt "${neu[0]}" hinzugefügt` : `${neu.length} Punkte aus dem Vorschlag hinzugefügt`;
    if (await setzen([...karte.checkliste, ...neu.map((t) => ({ text: t, erledigt: false }))], text)) vorschlag.schliessen();
  }

  async function hinzu(): Promise<void> {
    const t = neu.trim();
    if (t && await setzen([...karte.checkliste, { text: t, erledigt: false }], `Punkt "${t}" hinzugefügt`)) neu = "";
  }
</script>

<section class="pw-abschnitt">
  <div class="etikett">Checkliste {#if karte.checkliste.length}<span class="zaehler" class:erfolg={anteil === 1}>{erledigt}/{karte.checkliste.length}</span>{/if}
    {#if ki && schreiben}
      <span class="rechts"><button class="knopf ohne klein" title="Neue Punkte vorschlagen (über die Leitstelle)" aria-pressed={vorschlag.offen}
                                   onclick={() => (vorschlag.offen ? vorschlag.schliessen() : vorschlagen())}><i class="fa-solid fa-wand-magic-sparkles"></i>Vorschlagen</button></span>
    {/if}
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
  {#if vorschlag.offen}
    <Vorschlag titel="Vorschlag: nächste Schritte aus dem Inhalt der Karte" lauf={vorschlag} nochmal={vorschlagen}>
      {#snippet children(v)}
        {#each v.punkte as p, i (i)}
          <label class="pw-punkt"><input type="checkbox" bind:checked={gewaehlt[i]} /><span class="pw-punkt-text">{p}</span></label>
        {:else}
          <div class="pw-vorschlag-text">Keine neuen Punkte; die Checkliste deckt die Karte schon ab.</div>
        {/each}
      {/snippet}
      {#snippet knoepfe(v)}
        {#if v.punkte.length}<button class="knopf klein" disabled={!gewaehlt.some(Boolean)} onclick={() => vorschlagUebernehmen(v.punkte)}>Übernehmen</button>{/if}
      {/snippet}
    </Vorschlag>
  {/if}
  {#if schreiben}
    <input class="eingabe" placeholder="Punkt hinzufügen, Enter" aria-label="Punkt hinzufügen" bind:value={neu} use:verwerfbar
           onkeydown={(e) => { if (e.key === "Enter") hinzu(); }} />
  {/if}
</section>
