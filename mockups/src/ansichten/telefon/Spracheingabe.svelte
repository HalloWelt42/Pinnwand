<script lang="ts">
  // Erfassen per Sprache: die Aufnahme läuft über die App Transkription, der Pegel zeigt, dass sie hört, der Text
  // erscheint live (die letzten Wörter sind noch vorläufig). Stopp übernimmt den Text: der erste Satz wird Titel, der
  // ganze Text Beschreibung. Verwerfen beendet ohne Übernahme.
  import { PEGEL, SPRACHE } from "./daten";

  let { vorfuehren = false, uebernehmen, verwerfen }: {
    /** Entwurf: Aufnahme mitten im Satz, ohne weiterzuschreiben */
    vorfuehren?: boolean;
    uebernehmen: (text: string) => void;
    verwerfen: () => void;
  } = $props();

  const WOERTER = SPRACHE.text.split(" ");
  let anzahl = $state(0);
  $effect(() => {
    if (vorfuehren) {
      anzahl = Math.round(WOERTER.length * SPRACHE.erkannt);
      return;
    }
    anzahl = 0;
    const uhr = setInterval(() => { if (anzahl < WOERTER.length) anzahl += 1; }, 1000 / SPRACHE.tempo);
    return () => clearInterval(uhr);
  });
  const fertig = $derived(anzahl >= WOERTER.length);
  const grenze = $derived(fertig ? anzahl : Math.max(0, anzahl - SPRACHE.vorlaeufig));
  const sicher = $derived(WOERTER.slice(0, grenze).join(" "));
  const vorlaeufig = $derived(WOERTER.slice(grenze, anzahl).join(" "));
  const sek = $derived(Math.round(anzahl / SPRACHE.tempo));
</script>

<section class="pw-tel-sprache" aria-label="Aufnahme">
  <div class="kopfzeile">
    <span class="zustand laeuft"><i class="fa-solid fa-microphone"></i>Aufnahme läuft</span>
    <span class="zahl dauer">{Math.floor(sek / 60)}:{String(sek % 60).padStart(2, "0")}</span>
  </div>
  <div class="pegel" aria-hidden="true">
    {#each PEGEL as p, i (i)}<span style="--h: {p}; --v: {i}"></span>{/each}
  </div>
  <div class="mitschrift" aria-live="polite">
    {#if anzahl}{sicher}{#if vorlaeufig}{" "}<span class="vorlaeufig">{vorlaeufig}</span>{/if}{:else}<span class="vorlaeufig">Sprich einfach los.</span>{/if}
  </div>
  <span class="quelle"><i class="fa-solid fa-wave-square"></i>Transkription schreibt mit; der erste Satz wird Titel, alles Beschreibung.</span>
  <div class="knoepfe">
    <button class="knopf ohne" onclick={verwerfen}><i class="fa-solid fa-xmark"></i>Verwerfen</button>
    <button class="knopf haupt" disabled={!anzahl} onclick={() => uebernehmen(WOERTER.slice(0, anzahl).join(" "))}>
      <i class="fa-solid fa-stop"></i>Stopp und übernehmen</button>
  </div>
</section>
