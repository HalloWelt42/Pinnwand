<script lang="ts">
  // Rückfrage für etwas ohne Rückweg (endgültig löschen, Konto zurücksetzen): eine Fläche mit Frage und Folgen, zur
  // Sicherheit ein Wort zum Eintippen (Schlüssel, Kürzel, Name; Groß und klein egal); der Knopf wirkt erst, wenn es
  // stimmt. Der Server prüft dasselbe Wort.
  import type { Snippet } from "svelte";

  let { frage, wort, knopf, bestaetigen, abbrechen, children }: {
    frage: string;
    /** das Wort, das eingetippt werden muss */
    wort: string;
    knopf: string;
    /** führt aus; true: erledigt (die Fläche schließt der Aufrufer) */
    bestaetigen: (eingabe: string) => Promise<boolean>;
    abbrechen: () => void;
    /** die Folgen in ganzen Sätzen */
    children: Snippet;
  } = $props();

  let eingabe = $state("");
  let laeuft = $state(false);
  const passt = $derived(eingabe.trim().toLocaleLowerCase("de") === wort.toLocaleLowerCase("de"));

  async function los(): Promise<void> {
    if (!passt || laeuft) return;
    laeuft = true;
    try {
      await bestaetigen(eingabe.trim());
    } finally {
      laeuft = false;
    }
  }
  const fokus = (feld: HTMLInputElement) => feld.focus();
</script>

<div class="hinweis gefahr pw-endgueltig" role="alertdialog" aria-label={frage}>
  <i class="fa-solid fa-triangle-exclamation"></i>
  <div class="pw-endgueltig-inhalt">
    <b>{frage}</b>
    <div>{@render children()}</div>
    <label class="pw-endgueltig-feld">Zur Sicherheit <b class="pw-schluessel">{wort}</b> eintippen:
      <input class="eingabe" bind:value={eingabe} use:fokus autocomplete="off" aria-label="Zur Sicherheit {wort} eintippen"
             onkeydown={(e) => { if (e.key === "Enter") void los(); if (e.key === "Escape") abbrechen(); }} /></label>
    <span class="pw-endgueltig-knoepfe">
      <button class="knopf klein" onclick={abbrechen}>Abbrechen</button>
      <button class="knopf gefahr-voll klein" disabled={!passt || laeuft} onclick={los}><i class="fa-solid fa-trash-can"></i>{knopf}</button>
    </span>
  </div>
</div>
