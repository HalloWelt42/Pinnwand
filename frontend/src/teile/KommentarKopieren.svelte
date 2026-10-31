<script lang="ts">
  // Rohtext eines Kommentars (Markdown) in die Zwischenablage (HELF-98), für eigene und fremde Kommentare, am Rechner
  // und am Telefon. Das Zeichen wird kurz zum Haken; über http im Heimnetz kopiert der Ersatzweg im Klick selbst
  // (teile/zwischenablage). Geht es nicht, sagt die Meldung, wie es von Hand geht.
  import { melden } from "../daten/anwendung/meldung.svelte";
  import { kopieren } from "./zwischenablage";

  let { text, klasse = "" }: { text: string; klasse?: string } = $props();

  let kopiert = $state(false);
  let uhr: ReturnType<typeof setTimeout> | undefined;

  async function klick(e: MouseEvent): Promise<void> {
    e.stopPropagation();
    if (await kopieren(text)) {
      kopiert = true;
      clearTimeout(uhr);
      uhr = setTimeout(() => (kopiert = false), 1500);
    } else {
      melden("Kopieren ging nicht; den Text markieren und selbst kopieren");
    }
  }
</script>

<button type="button" class="knopf ohne symbol {klasse}" title={kopiert ? "Kopiert" : "Text des Kommentars kopieren (Markdown)"}
        aria-label={kopiert ? "Kopiert" : "Text des Kommentars kopieren"} onclick={klick}>
  <i class="fa-solid {kopiert ? 'fa-check' : 'fa-copy'}"></i></button>
