<script lang="ts">
  // Zeiterfassung einer Karte: Start/Pause/Stopp, Schaetzung, Fortschritt, geteilte
  // Gruppen-Zeit (nur Anzeige), Tag nachbuchen und die Tages-Aufschluesselung.
  // Ticketzeit = Summe je Karte; jeder Eintrag haengt an einem Tag (= Arbeitszeit).
  import type { Karte, Zeiteintrag } from '../../types'
  import { erstelleZeiteintrag, ladeKartenZeiten, aktualisiereZeiteintrag, loescheZeiteintrag } from '../../api'
  import type { KarteAenderung } from '../../api'
  import { ymd } from '../../zeit'
  import { timer, timerStarten, timerPausieren, timerStoppen, erfassteSekunden, formatDauerVoll, formatPlan, parseZeit } from '../../timer.svelte'

  let { karte, onAendern }: { karte: Karte; onAendern: (daten: KarteAenderung) => void } = $props()

  const laeuft = $derived(!!karte.laeuft_seit)
  // Pausiert = diese Karte ist die aktive Sitzung, laeuft aber gerade nicht.
  const pausiert = $derived(!laeuft && timer.aktiv?.id === karte.id)
  const sek = $derived(laeuft ? erfassteSekunden(karte, timer.jetzt) : (karte.erfasst_sek ?? 0))
  const planMin = $derived(karte.schaetzung_min ?? null)
  const prozent = $derived(planMin && planMin > 0 ? (sek / 60 / planMin) * 100 : null)
  // Geteilte Zeitgruppe: kombinierte Zeit nur zur Anzeige (zaehlt einmal).
  const geteilt = $derived(!!karte.gruppe_id && karte.gruppe_zeit_geteilt !== false)
  const gruppeAnzahl = $derived((karte.gruppe_mitglieder?.length ?? 0) + 1)

  // Alle Zeiteintraege dieser Karte (alle Tage); Korrekturen laufen ueber datierte
  // Eintraege, damit die Arbeitszeit dem richtigen Tag gutgeschrieben wird.
  let kartenZeiten = $state<Zeiteintrag[]>([])
  let nbDatum = $state(ymd(new Date()))
  let nbDauer = $state('')

  let zuletzt: string | null = null
  $effect(() => {
    if (karte.id !== zuletzt) {
      zuletzt = karte.id
      ladeKartenZeitenFuer()
    }
  })
  async function ladeKartenZeitenFuer(): Promise<void> {
    try {
      kartenZeiten = (await ladeKartenZeiten(karte.id)).sort((a, b) => b.datum.localeCompare(a.datum))
    } catch {
      kartenZeiten = []
    }
  }
  async function zeileDatum(e: Zeiteintrag, datum: string): Promise<void> {
    if (!datum || datum === e.datum) return
    await aktualisiereZeiteintrag(e.id, { datum })
    timer.stand++
    await ladeKartenZeitenFuer()
  }
  async function zeileDauer(e: Zeiteintrag, wert: string): Promise<void> {
    const s = parseZeit(wert)
    if (s == null || s === e.sekunden) return
    await aktualisiereZeiteintrag(e.id, { sekunden: Math.max(0, s) })
    timer.stand++
    await ladeKartenZeitenFuer()
  }
  async function zeileLoeschen(e: Zeiteintrag): Promise<void> {
    await loescheZeiteintrag(e.id)
    timer.stand++
    await ladeKartenZeitenFuer()
  }
  async function bucheTag(): Promise<void> {
    const s = parseZeit(nbDauer)
    if (s == null || s <= 0) return
    await erstelleZeiteintrag({ karte_id: karte.id, datum: nbDatum, sekunden: s })
    nbDauer = ''
    timer.stand++ // Board laedt neu -> Ticketzeit der Karte aktualisiert sich
    await ladeKartenZeitenFuer()
  }
</script>

<p class="sec">Zeiterfassung</p>
<div class="timer">
  {#if laeuft}
    <button class="tbtn an" onclick={() => timerPausieren(karte.id)}><i class="fa-solid fa-pause" aria-hidden="true"></i> Pause</button>
    <button class="tbtn stopp" onclick={() => timerStoppen(karte.id)}><i class="fa-solid fa-stop" aria-hidden="true"></i> Stopp</button>
  {:else if pausiert}
    <button class="tbtn play" onclick={() => timerStarten(karte.id)}><i class="fa-solid fa-play" aria-hidden="true"></i> Fortsetzen</button>
    <button class="tbtn stopp" onclick={() => timerStoppen(karte.id)}><i class="fa-solid fa-stop" aria-hidden="true"></i> Stopp</button>
  {:else}
    <button class="tbtn play" onclick={() => timerStarten(karte.id)}><i class="fa-solid fa-play" aria-hidden="true"></i> Start</button>
  {/if}
  <span class="erfasst" title="Ticketzeit gesamt (Summe aller Tage)">{formatDauerVoll(sek)}</span>
  <label class="plan">Schätzung
    <input type="number" min="0" step="0.25" value={planMin ? planMin / 60 : ''}
      onchange={(e) => { const v = parseFloat(e.currentTarget.value); onAendern({ schaetzung_min: Number.isFinite(v) && v > 0 ? Math.round(v * 60) : null }) }} />
    Std
  </label>
</div>
{#if geteilt}
  <p class="grpzeit"><i class="fa-solid fa-link" aria-hidden="true"></i> Geteilt über {gruppeAnzahl} Aufgaben: {formatDauerVoll(karte.gruppe_sek ?? 0)} - zählt einmal</p>
{/if}
<p class="zcap">Ticketzeit gesamt (Summe aller Tage). Die Tage darunter bilden die Arbeitszeit des jeweiligen Tages.</p>
{#if prozent != null}
  <div class="fortschritt" class:ueber={prozent > 100}><span style="width:{Math.min(prozent, 100)}%"></span></div>
  <div class="pinfo" class:ueber={prozent > 100}>{Math.round(prozent)}% von {formatPlan(planMin ?? 0)}{#if prozent > 100} - überschritten{/if}</div>
{/if}
<div class="tagbuchung">
  <input type="date" bind:value={nbDatum} aria-label="Datum für Nachtrag" />
  <input class="tbdauer" placeholder="z.B. 0:30 oder 1,5" bind:value={nbDauer} aria-label="Dauer"
    onkeydown={(e) => { if (e.key === 'Enter') bucheTag() }} />
  <button class="mini" onclick={bucheTag}>Tag buchen</button>
</div>
<p class="taginfo">Zeit für einen beliebigen Tag nachtragen (zusätzlich zu Start/Stopp).</p>
{#if kartenZeiten.length}
  <div class="tageliste">
    {#each kartenZeiten as e (e.id)}
      <div class="tagrow">
        <input type="date" value={e.datum} onchange={(ev) => zeileDatum(e, ev.currentTarget.value)} aria-label="Tag des Eintrags" />
        <input class="trdauer" value={formatDauerVoll(e.sekunden)} onchange={(ev) => zeileDauer(e, ev.currentTarget.value)} aria-label="Dauer" title="Dauer (z.B. 1:30:00 oder 1,5)" />
        {#if !e.manuell}<span class="trauto" title="Aus Start/Stopp"><i class="fa-solid fa-stopwatch" aria-hidden="true"></i></span>{/if}
        <button class="ic" aria-label="Eintrag löschen" onclick={() => zeileLoeschen(e)}><i class="fa-solid fa-xmark" aria-hidden="true"></i></button>
      </div>
    {/each}
  </div>
{/if}

<style>
  .sec { font-family: var(--font-display); font-size: 10.5px; letter-spacing: 0.04em; text-transform: uppercase; color: var(--text-3); margin: 18px 0 8px; }
  .timer { display: flex; align-items: center; gap: 12px; }
  .tbtn { display: inline-flex; align-items: center; gap: 8px; border: 1px solid var(--hl-primary); background: var(--hl-primary); color: var(--hl-on-primary); border-radius: var(--r-m); padding: 8px 16px; font-size: 13px; font-weight: 600; cursor: pointer; }
  .tbtn.an { background: var(--surface-2); color: var(--hl-primary-text); }
  .tbtn.stopp { background: var(--surface-1); color: var(--text-2); border-color: var(--border-2); }
  .tbtn.stopp:hover { border-color: var(--gefahr); color: var(--due-rot-fg); }
  .erfasst { font-family: var(--font-mono); font-size: 18px; font-variant-numeric: tabular-nums; color: var(--text-1); }
  .plan { margin-left: auto; font-size: 12px; color: var(--text-3); display: inline-flex; align-items: center; gap: 6px; }
  .plan input { width: 60px; border: 1px solid var(--border); background: var(--surface-2); color: var(--text-1); border-radius: var(--r-s); padding: 5px 7px; font-size: 12.5px; }
  .grpzeit { margin: 2px 0 0; font-size: 11.5px; color: var(--hl-primary-text); display: flex; align-items: center; gap: 6px; }
  .zcap { font-size: 10.5px; color: var(--text-3); margin: 6px 0 0; }
  .fortschritt { height: 7px; border-radius: 5px; background: var(--border); overflow: hidden; margin: 10px 0 5px; }
  .fortschritt span { display: block; height: 100%; background: var(--hl-primary); }
  .fortschritt.ueber span { background: var(--gefahr); }
  .pinfo { font-size: 12px; color: var(--text-3); }
  .pinfo.ueber { color: var(--due-rot-fg); font-weight: 600; }
  .tagbuchung { display: flex; align-items: center; gap: 8px; margin-top: 10px; }
  .tagbuchung input[type='date'] { border: 1px solid var(--border); background: var(--surface-2); color: var(--text-1); border-radius: var(--r-s); padding: 6px 8px; font-size: 12.5px; }
  .tbdauer { flex: 1; min-width: 0; border: 1px solid var(--border); background: var(--surface-2); color: var(--text-1); border-radius: var(--r-s); padding: 6px 8px; font-size: 12.5px; }
  .taginfo { font-size: 10.5px; color: var(--text-3); margin: 4px 0 0; }
  .tageliste { display: flex; flex-direction: column; gap: 5px; margin-top: 8px; }
  .tagrow { display: flex; align-items: center; gap: 8px; }
  .tagrow input[type='date'] { border: 1px solid var(--border); background: var(--surface-2); color: var(--text-1); border-radius: var(--r-s); padding: 5px 8px; font-size: 12.5px; }
  .trdauer { width: 96px; border: 1px solid var(--border); background: var(--surface-2); color: var(--text-1); border-radius: var(--r-s); padding: 5px 8px; font-size: 12.5px; font-variant-numeric: tabular-nums; }
  .trauto { color: var(--text-3); font-size: 11px; }
  .ic { border: none; background: transparent; color: var(--text-3); cursor: pointer; padding: 2px 4px; }
  .ic:hover { color: var(--text-1); }
  .mini { border: 1px solid var(--hl-primary); background: var(--hl-primary); color: var(--hl-on-primary); border-radius: var(--r-s); padding: 4px 9px; font-size: 11.5px; white-space: nowrap; cursor: pointer; }
</style>
