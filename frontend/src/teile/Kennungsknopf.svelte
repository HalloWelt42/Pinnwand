<script lang="ts">
  // Kennung einer Karte, mit einem Klick kopiert: der Schlüssel im Board (HELF-12) und die Gesamtnummer (# 101), am
  // Rechner auf der Karte, in der Liste und im Kartendetail, am Telefon im Kopf der Karte. Der Klick gilt nur der Kennung (die Karte öffnet sich dabei nicht); die Meldung bestätigt kurz. Über
  // http im Heimnetz kopiert der Ersatzweg im Klick selbst (teile/zwischenablage).
  import { melden } from "../daten/anwendung/meldung.svelte";
  import { kopieren } from "./zwischenablage";

  let { wert, klasse = "" }: { wert: string; klasse?: string } = $props();

  async function klick(e: MouseEvent): Promise<void> {
    e.preventDefault();
    e.stopPropagation();
    melden((await kopieren(wert)) ? `${wert} kopiert` : `Kopieren ging nicht; die Kennung lautet ${wert}`);
  }
</script>

<button type="button" class="pw-schluessel pw-kennung {klasse}" title="{wert} kopieren" aria-label="Kennung {wert} kopieren"
        onclick={klick} onkeydown={(e) => e.stopPropagation()}>{wert}</button>
