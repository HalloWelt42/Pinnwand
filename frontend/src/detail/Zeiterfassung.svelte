<script lang="ts">
  // Zeiterfassung an der Karte (Modul Zeiterfassung): dein Timer, die Ticketzeit (Summe aller Einträge, die du siehst:
  // ohne das Recht "Zeiten anderer sehen" nur deine, und so heißt sie dann; setzen bucht die Differenz heute bei dir), die
  // Schätzung, Zeit nachtragen (Enter in Tag oder Dauer bucht) und die Einträge je Tag und Person (M-86 bis M-88). In
  // einer Zeile ändert ein Klick auf den Tag das Datum, die Dauer ist direkt änderbar, X löscht; das gilt für eigene
  // Einträge, für fremde nur mit dem Recht "Zeiten anderer bearbeiten". Gebucht und geändert wird nur über die
  // Anwendungsfälle, jede Änderung mit Rückgängig.
  import { Hilfepunkt } from "appkern-oberflaeche";
  import { tick } from "svelte";
  import { darf, laufendAuf, timerErlaubt, timerVon, zeitDerKarte } from "../daten/abfragen";
  import { bearbeiten } from "../daten/anwendung/karten.svelte";
  import { anhalten, fortsetzen, starten, stoppen } from "../daten/anwendung/timer.svelte";
  import { buchen, dauerAendern, datumAendern, loeschen, ticketzeitSetzen } from "../daten/anwendung/zeiten.svelte";
  import { uhr } from "../daten/uhr.svelte";
  import { ICH } from "../daten/ich";
  import { datum, dauer } from "../daten/format";
  import { konto, stand } from "../daten/stand.svelte";
  import { HERKUNFT } from "../anzeige";
  import type { Board, Karte, Zeiteintrag } from "../modell";
  import Person from "../board/Person.svelte";
  import DatumFeld from "../teile/DatumFeld.svelte";
  import DauerFeld from "../teile/DauerFeld.svelte";
  import { enter } from "../teile/taste";

  let { karte, board, gruppenSek = 0 }: { karte: Karte; board: Board; gruppenSek?: number } = $props();
  const andereSehen = $derived(darf(board, "zeit.andere.sehen"));
  const andereBearbeiten = $derived(darf(board, "zeit.andere.bearbeiten"));
  const eintraege = $derived(stand.zeiteintraege.filter((z) => z.karte === karte.id && (z.konto === ICH || andereSehen))
    .sort((a, b) => b.datum.localeCompare(a.datum) || (b.von ?? "").localeCompare(a.von ?? "")));
  const meiner = $derived(timerVon(ICH)?.karte === karte.id ? timerVon(ICH) : undefined);
  const fremde = $derived(laufendAuf(karte.id).filter((t) => t.konto !== ICH));
  const gesamt = $derived(zeitDerKarte(karte.id));
  const anteil = $derived(karte.schaetzungMin ? gesamt / 60 / karte.schaetzungMin : 0);
  let tag = $state(uhr.heute);
  let nachtrag = $state(0);
  /** Eintrag, dessen Tag gerade geändert wird */
  let tagAendern = $state<string | null>(null);

  function aenderbar(z: Zeiteintrag): boolean {
    return z.konto === ICH || andereBearbeiten;
  }

  /** nachtragen; die Dauer leert sich erst, wenn gebucht ist (getrennt oder abgelehnt bleibt sie stehen) */
  async function nachtragen(): Promise<void> {
    if (nachtrag && (await buchen(karte.id, tag, nachtrag))) nachtrag = 0;
  }

  /** Enter in Tag oder Dauer bucht (die Felder übernehmen ihren Wert schon beim Enter) */
  function taste(e: KeyboardEvent): void {
    if (enter(e) && (e.target as HTMLElement).tagName === "INPUT") void nachtragen();
  }

  async function tagOeffnen(id: string, zelle: HTMLElement): Promise<void> {
    const zeile = zelle.closest(".pw-tageszeile");
    tagAendern = id;
    await tick();
    zeile?.querySelector<HTMLInputElement>(".pw-tageszeile-tag input")?.select();
  }
</script>

<section class="pw-abschnitt">
  <div class="etikett">Zeiterfassung<Hilfepunkt thema="zeiterfassung" abschnitt="timer" /></div>
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
        <DauerFeld sek={Math.round(gesamt)} mitSekunden klasse="gross" titel="Ticketzeit: {andereSehen ? 'Summe aller Einträge' : 'Deine Zeit auf dieser Karte'}; ändern bucht die Differenz heute bei dir"
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
      <!-- svelte-ignore a11y_no_static_element_interactions -->
      <div class="pw-nachtragen" onkeydown={taste}>
        <DatumFeld {tag} ontag={(t) => (tag = t)} breite="150px" titel="Tag des Eintrags; Enter bucht" />
        <span class="pw-nachtragen-dauer"><DauerFeld sek={nachtrag} klasse="feld" platzhalter="0:30 oder 1,5" titel="Dauer wie 0:30, 1,5 oder 90min; Enter bucht" onwert={(s) => (nachtrag = s)} /></span>
        <button class="knopf" disabled={!nachtrag} onclick={nachtragen}><i class="fa-solid fa-plus"></i>Tag buchen</button>
      </div>
    {/if}
    <div class="pw-tageszeilen">
      {#each eintraege as z (z.id)}
        {@const zeiten = `${z.von ? ` ${z.von}` : ""}${z.bis ? ` bis ${z.bis}` : ""}`}
        <div class="pw-tageszeile">
          {#if tagAendern === z.id}
            <span class="pw-tageszeile-tag" onfocusout={() => (tagAendern = null)}>
              <DatumFeld tag={z.datum} ontag={(t) => datumAendern(z.id, t)} titel="Tag des Eintrags; Enter übernimmt, Escape verwirft" />
            </span>
          {:else if aenderbar(z)}
            <button class="pw-tageszeile-tag" title="Tag ändern" onclick={(e) => tagOeffnen(z.id, e.currentTarget)}>{datum(z.datum, true)}<span class="schwach">{zeiten}</span></button>
          {:else}
            <span class="pw-tageszeile-tag">{datum(z.datum, true)}<span class="schwach">{zeiten}</span></span>
          {/if}
          <span class="wer"><Person id={z.konto} /><span class="schwach">{HERKUNFT[z.herkunft]}{z.sitzungen ? `, ${z.sitzungen.length} Sitzungen` : ""}</span></span>
          {#if aenderbar(z)}
            <span class="dauer"><DauerFeld sek={z.sekunden} leerErlaubt={false} titel="Dauer ändern wie 1:30, 1,5 oder 90min"
                                           onwert={(s) => { if (s > 0) dauerAendern(z.id, s); }} /></span>
          {:else}
            <span class="dauer">{dauer(z.sekunden)}</span>
          {/if}
          {#if aenderbar(z)}
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
