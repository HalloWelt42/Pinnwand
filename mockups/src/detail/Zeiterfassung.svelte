<script lang="ts">
  // Zeiterfassung an der Karte (Modul Zeiterfassung): dein Timer, die Ticketzeit (Summe aller Einträge; setzen bucht die
  // Differenz heute bei dir), die Schätzung, Zeit nachtragen und die Einträge je Tag und Person. Eigene Einträge sind
  // löschbar, fremde nur mit dem Recht "Zeiten anderer bearbeiten". Gebucht wird nur über die Anwendungsfälle.
  import { darf, laufendAuf, timerErlaubt, timerVon, zeitDerKarte } from "../beispiel/abfragen";
  import { bearbeiten } from "../beispiel/anwendung/karten.svelte";
  import { anhalten, fortsetzen, starten, stoppen } from "../beispiel/anwendung/timer.svelte";
  import { buchen, loeschen, ticketzeitSetzen } from "../beispiel/anwendung/zeiten.svelte";
  import { HEUTE, ICH } from "../beispiel/daten";
  import { datum, dauer } from "../beispiel/format";
  import { konto, stand } from "../beispiel/stand.svelte";
  import { HERKUNFT } from "../anzeige";
  import type { Board, Karte } from "../modell";
  import Person from "../board/Person.svelte";
  import DatumFeld from "../teile/DatumFeld.svelte";
  import DauerFeld from "../teile/DauerFeld.svelte";

  let { karte, board, gruppenSek = 0 }: { karte: Karte; board: Board; gruppenSek?: number } = $props();
  const andereSehen = $derived(darf(board, "zeit.andere.sehen"));
  const andereBearbeiten = $derived(darf(board, "zeit.andere.bearbeiten"));
  const eintraege = $derived(stand.zeiteintraege.filter((z) => z.karte === karte.id && (z.konto === ICH || andereSehen))
    .sort((a, b) => b.datum.localeCompare(a.datum) || (b.von ?? "").localeCompare(a.von ?? "")));
  const meiner = $derived(timerVon(ICH)?.karte === karte.id ? timerVon(ICH) : undefined);
  const fremde = $derived(laufendAuf(karte.id).filter((t) => t.konto !== ICH));
  const gesamt = $derived(zeitDerKarte(karte.id));
  const anteil = $derived(karte.schaetzungMin ? gesamt / 60 / karte.schaetzungMin : 0);
  let tag = $state(HEUTE);
  let nachtrag = $state(0);
</script>

<section class="pw-abschnitt">
  <div class="etikett">Zeiterfassung</div>
  <div class="pw-zeitblock">
    <div class="oben">
      {#if meiner?.seit}
        <button class="knopf haupt" onclick={anhalten}><i class="fa-solid fa-pause"></i>Anhalten</button>
        <button class="knopf" onclick={stoppen}><i class="fa-solid fa-stop"></i>Stopp und buchen</button>
      {:else if meiner}
        <button class="knopf haupt" onclick={fortsetzen}><i class="fa-solid fa-play"></i>Fortsetzen</button>
        <button class="knopf" onclick={stoppen}><i class="fa-solid fa-stop"></i>Beenden</button>
      {:else if timerErlaubt(karte)}
        <button class="knopf haupt" onclick={() => starten(karte.id)}><i class="fa-solid fa-play"></i>Start</button>
      {/if}
      <span class="gross" class:laeuft={!!meiner?.seit}>
        <DauerFeld sek={Math.round(gesamt)} mitSekunden klasse="gross" titel="Ticketzeit: Summe aller Einträge; ändern bucht die Differenz heute bei dir"
                   gesperrt={!!meiner?.seit || !darf(board, "zeit.buchen")} onwert={(s) => ticketzeitSetzen(karte.id, s)} />
      </span>
      <span class="schaetzung">Schätzung
        <DauerFeld sek={(karte.schaetzungMin ?? 0) * 60} klasse="feld" platzhalter="0:00" titel="Geschätzte Dauer wie 3:00 oder 2,5"
                   onwert={(s) => bearbeiten(karte.id, { schaetzungMin: s ? Math.round(s / 60) : undefined }, s ? `Schätzung ${dauer(s)}` : "Schätzung entfernt")} /></span>
    </div>
    {#each fremde as t (t.konto)}
      <div class="schwach pw-zeit-fremd"><i class="fa-solid fa-circle-play pw-akzent"></i> Timer von {konto(t.konto).name} läuft</div>
    {/each}
    {#if karte.schaetzungMin}
      <div class="pw-fortschritt zeit" class:ueber={anteil > 1} title="{Math.round(anteil * 100)} Prozent der Schätzung"><span style="width: {Math.min(100, anteil * 100)}%"></span></div>
    {/if}
    {#if gruppenSek}
      <div class="schwach pw-zeit-gruppe"><i class="fa-solid fa-link"></i> Zusammen mit der Gruppe {dauer(gesamt + gruppenSek)}; jede Sekunde zählt einmal</div>
    {/if}
    {#if darf(board, "zeit.buchen")}
      <div class="pw-nachtragen">
        <DatumFeld {tag} ontag={(t) => (tag = t)} breite="150px" titel="Tag des Eintrags" />
        <span class="pw-nachtragen-dauer"><DauerFeld sek={nachtrag} klasse="feld" platzhalter="0:30 oder 1,5" titel="Dauer wie 0:30, 1,5 oder 90min" onwert={(s) => (nachtrag = s)} /></span>
        <button class="knopf klein" disabled={!nachtrag} onclick={() => { buchen(karte.id, tag, nachtrag); nachtrag = 0; }}><i class="fa-solid fa-plus"></i>Tag buchen</button>
      </div>
    {/if}
    <div class="pw-tageszeilen">
      {#each eintraege as z (z.id)}
        <div class="pw-tageszeile">
          <span>{datum(z.datum, true)}{z.von ? ` ${z.von}` : ""}{z.bis ? ` bis ${z.bis}` : ""}</span>
          <span class="wer"><Person id={z.konto} /><span class="schwach">{HERKUNFT[z.herkunft]}{z.sitzungen ? `, ${z.sitzungen.length} Sitzungen` : ""}</span></span>
          <span class="dauer">{dauer(z.sekunden)}</span>
          {#if z.konto === ICH || andereBearbeiten}
            <button class="knopf ohne symbol klein" title="Eintrag löschen (Rückgängig möglich)" onclick={() => loeschen(z.id)}><i class="fa-solid fa-xmark"></i></button>
          {:else}
            <i class="fa-solid fa-lock schwach" title="Eintrag einer anderen Person"></i>
          {/if}
        </div>
      {:else}
        <div class="schwach pw-zeit-leer">Noch keine Zeit gebucht.</div>
      {/each}
    </div>
  </div>
</section>
