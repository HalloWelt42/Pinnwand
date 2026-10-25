<script lang="ts">
  // Eingabe einer Dauer, sekundengenau: "1:30", "1:30:15", "1,5", "90min", "2h". Enter oder Verlassen übernimmt,
  // Escape verwirft (die alte App übernahm beim Escape), Unlesbares bleibt stehen und wird rot mit Hinweis statt still
  // verworfen. Leer heißt null Sekunden.
  import { untrack } from "svelte";
  import { dauer } from "../../beispiel/format";
  import { dauerLesen } from "./regeln";

  let { sek, onwert, mitSekunden = false, gesperrt = false, titel = "", klasse = "", platzhalter = "", leerErlaubt = true }: {
    sek: number; onwert: (sek: number) => void; mitSekunden?: boolean; gesperrt?: boolean; titel?: string; klasse?: string;
    platzhalter?: string; leerErlaubt?: boolean;
  } = $props();

  function zeigen(s: number): string {
    if (!s) return "";
    return dauer(s, mitSekunden || s % 60 !== 0);
  }

  let text = $state("");
  let fehler = $state(false);
  let fokus = $state(false);
  let verwerfen = false;
  // nur ein neuer Wert von außen ersetzt den Text, nie das Verlassen des Felds (sonst wäre Unlesbares still weg)
  $effect(() => { const s = sek; untrack(() => { if (!fokus) { text = zeigen(s); fehler = false; } }); });

  function uebernehmen(): void {
    if (verwerfen) { verwerfen = false; text = zeigen(sek); fehler = false; return; }
    const t = text.trim();
    if (!t) {
      if (leerErlaubt) { fehler = false; if (sek) onwert(0); } else fehler = true;
      return;
    }
    const s = dauerLesen(t);
    if (s === null) { fehler = true; return; }
    fehler = false;
    if (s !== sek) onwert(s);
    text = zeigen(s);
  }

  function taste(e: KeyboardEvent): void {
    const el = e.currentTarget as HTMLInputElement;
    if (e.key === "Enter") { el.blur(); }
    if (e.key === "Escape") { verwerfen = true; el.blur(); e.stopPropagation(); }
  }
</script>

<input class="pw-zeit-dauer {klasse}" class:falsch={fehler} bind:value={text} disabled={gesperrt} placeholder={platzhalter} inputmode="decimal"
       title={fehler ? "Dauer bitte wie 1:30, 1:30:15, 1,5 oder 90min eingeben" : titel}
       aria-invalid={fehler} onfocus={() => (fokus = true)} onblur={() => { fokus = false; uebernehmen(); }} onkeydown={taste} />
