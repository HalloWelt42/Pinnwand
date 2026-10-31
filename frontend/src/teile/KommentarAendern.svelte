<script lang="ts">
  // Eigenen Kommentar bearbeiten oder löschen (HELF-94), am Rechner und am Telefon gleich: das Feld mit der Schreibhilfe
  // für Markdown (HELF-92), Speichern, Abbrechen und Löschen (ohne Rückfrage; die Meldung bietet Rückgängig, der Text
  // steht im Verlauf). Escape bricht ab; am Rechner speichert Enter, Umschalt und Enter macht eine neue
  // Zeile (wie beim Schreiben). Lehnt der Server ab, bleibt das Feld offen und der Text stehen.
  import { onMount } from "svelte";
  import { kommentarBearbeiten, kommentarLoeschen } from "../daten/anwendung/karten.svelte";
  import type { Kennung, Kommentar } from "../modell";
  import MarkdownLeiste from "./MarkdownLeiste.svelte";
  import type { MarkdownOptionen } from "./markdown";
  import { enter } from "./taste";

  let { karte, kommentar, optionen = {}, gross = false, enterSpeichert = false, fertig }: {
    karte: Kennung;
    kommentar: Kommentar;
    optionen?: MarkdownOptionen;
    gross?: boolean;
    enterSpeichert?: boolean;
    /** schließt das Feld (nach dem Speichern oder beim Abbrechen) */
    fertig: () => void;
  } = $props();

  // svelte-ignore state_referenced_locally
  let entwurf = $state(kommentar.text);
  let feld = $state<HTMLTextAreaElement>();
  let laeuft = $state(false);
  const geht = $derived(!laeuft && !!entwurf.trim() && entwurf.trim() !== kommentar.text.trim());

  onMount(() => {
    feld?.focus();
    feld?.setSelectionRange(entwurf.length, entwurf.length);
  });

  async function speichern(): Promise<void> {
    if (!geht) return;
    laeuft = true;
    const ok = await kommentarBearbeiten(karte, kommentar.id, entwurf);
    laeuft = false;
    if (ok) fertig();
  }

  async function loeschen(): Promise<void> {
    laeuft = true;
    const ok = await kommentarLoeschen(karte, kommentar.id);
    laeuft = false;
    if (ok) fertig();
  }

  function taste(e: KeyboardEvent): void {
    if (e.key === "Escape") {
      e.preventDefault();
      e.stopPropagation();
      fertig();
    } else if (enterSpeichert && enter(e) && !e.shiftKey) {
      e.preventDefault();
      void speichern();
    }
  }
</script>

<div class="pw-kommentar-aendern">
  <MarkdownLeiste {feld} bind:text={entwurf} {optionen} {gross}>
    <textarea class="eingabe" rows="4" bind:this={feld} bind:value={entwurf} onkeydown={taste} aria-label="Kommentar bearbeiten"></textarea>
  </MarkdownLeiste>
  <div class="pw-kommentar-aendern-knoepfe">
    <button type="button" class="knopf ohne gefahr pw-kommentar-loeschen" class:klein={!gross} disabled={laeuft}
            title="Kommentar löschen; der Text bleibt im Verlauf, Rückgängig holt ihn zurück" onclick={loeschen}>
      <i class="fa-solid fa-trash-can"></i>Löschen</button>
    <button type="button" class="knopf ohne" class:klein={!gross} onclick={fertig}>Abbrechen</button>
    <button type="button" class="knopf" class:klein={!gross} disabled={!geht} onclick={speichern}>
      <i class="fa-solid fa-check"></i>Speichern</button>
  </div>
</div>
