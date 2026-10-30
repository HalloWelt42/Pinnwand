<script lang="ts">
  // Kennung einer Karte (HELF-12), mit einem Klick kopiert: am Rechner auf der Karte und im Kartendetail, am Telefon im
  // Kopf der Karte. Der Klick gilt nur der Kennung (die Karte öffnet sich dabei nicht); die Meldung bestätigt kurz. Über
  // http im Heimnetz kopiert der Ersatzweg im Klick selbst (teile/zwischenablage).
  import { melden } from "../daten/anwendung/meldung.svelte";
  import { kopieren } from "./zwischenablage";

  let { schluessel, klasse = "" }: { schluessel: string; klasse?: string } = $props();

  async function klick(e: MouseEvent): Promise<void> {
    e.preventDefault();
    e.stopPropagation();
    melden((await kopieren(schluessel)) ? `${schluessel} kopiert` : `Kopieren ging nicht; die Kennung lautet ${schluessel}`);
  }
</script>

<button type="button" class="pw-schluessel pw-kennung {klasse}" title="{schluessel} kopieren" aria-label="Kennung {schluessel} kopieren"
        onclick={klick} onkeydown={(e) => e.stopPropagation()}>{schluessel}</button>
