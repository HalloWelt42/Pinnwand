<script lang="ts">
  // Zeiterfassung an der Karte (Modul Zeiterfassung): Timer je Person, Ticketzeit mit Schätzung, Tag nachbuchen und
  // die Einträge je Tag und Person. Eigene Einträge bearbeitbar, fremde nur mit dem Recht "Zeiten anderer bearbeiten".
  import { ICH, ZEITEINTRAEGE } from "../beispiel/daten";
  import { datum, dauer, laufendSek } from "../beispiel/format";
  import type { Karte } from "../modell";
  import Person from "../board/Person.svelte";

  let { karte, gruppenSek = 0 }: { karte: Karte; gruppenSek?: number } = $props();
  const eintraege = $derived(ZEITEINTRAEGE.filter((z) => z.karte === karte.id).sort((a, b) => b.datum.localeCompare(a.datum)));
  const laeuftBeiMir = $derived(karte.laeuft?.konto === ICH);
  const gesamt = $derived(karte.erfasstSek + (karte.laeuft ? laufendSek(karte.laeuft.seit) : 0));
  const anteil = $derived(karte.schaetzungMin ? gesamt / 60 / karte.schaetzungMin : 0);
  const HERKUNFT = { timer: "Timer", hand: "nachgetragen", korrektur: "Korrektur", serie: "Serie" };
</script>

<section class="pw-abschnitt">
  <div class="etikett">Zeiterfassung</div>
  <div class="pw-zeitblock">
    <div class="oben">
      {#if laeuftBeiMir}
        <button class="knopf haupt"><i class="fa-solid fa-pause"></i>Anhalten</button>
        <button class="knopf"><i class="fa-solid fa-stop"></i>Stopp und buchen</button>
      {:else}
        <button class="knopf haupt"><i class="fa-solid fa-play"></i>Start</button>
      {/if}
      <span class="gross" class:laeuft={laeuftBeiMir} title="Ticketzeit: Summe aller Einträge; direkt änderbar, die Differenz wird heute gebucht">{dauer(gesamt, true)}</span>
      <span class="schaetzung">Schätzung <input class="eingabe" value={karte.schaetzungMin ? dauer(karte.schaetzungMin * 60) : ""} placeholder="0:00" /> Std</span>
    </div>
    {#if karte.schaetzungMin}
      <div class="pw-fortschritt zeit" class:ueber={anteil > 1}><span style="width: {Math.min(100, anteil * 100)}%"></span></div>
    {/if}
    {#if gruppenSek}
      <div class="schwach" style="font-size: var(--klein)"><i class="fa-solid fa-link"></i> Zusammen mit der Gruppe {dauer(gesamt + gruppenSek)}; jede Sekunde zählt einmal</div>
    {/if}
    <div class="pw-nachtragen">
      <input class="eingabe" value="27.10.2026" style="width: 130px" title="Tag" />
      <input class="eingabe" placeholder="0:30 oder 1,5" style="width: 150px" title="Dauer" />
      <button class="knopf klein"><i class="fa-solid fa-plus"></i>Tag buchen</button>
    </div>
    <div class="pw-tageszeilen">
      {#each eintraege as z (z.id)}
        <div class="pw-tageszeile">
          <span>{datum(z.datum, true)}{z.von ? ` ${z.von}` : ""}</span>
          <span class="wer"><Person id={z.konto} /><span class="schwach">{HERKUNFT[z.herkunft]}</span></span>
          <span class="dauer">{dauer(z.sekunden)}</span>
          {#if z.konto === ICH}
            <button class="knopf ohne symbol klein" title="Eintrag löschen (Rückgängig möglich)"><i class="fa-solid fa-xmark"></i></button>
          {:else}
            <i class="fa-solid fa-lock schwach" title="Eintrag einer anderen Person"></i>
          {/if}
        </div>
      {/each}
    </div>
  </div>
</section>
