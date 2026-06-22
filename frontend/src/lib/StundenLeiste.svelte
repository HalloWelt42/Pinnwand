<script lang="ts">
  // Dauerhaft sichtbare Stunden-Uebersicht: geleistete Zeit (Ist) gegen Soll
  // fuer Heute, aktuelle Woche, Monat und Jahr. Ist gruen fett, Soll blau duenn.
  // Einklappbar; der Zustand wird im Browser gemerkt.
  import { ladeStundenUebersicht, type StundenUebersicht } from './api'
  import { formatStd } from './zeit'
  import { timer } from './timer.svelte'

  let daten = $state<StundenUebersicht | null>(null)
  let offen = $state(ladeOffen())

  function ladeOffen(): boolean {
    try {
      return JSON.parse(localStorage.getItem('pw_stundenleiste') || '{}').offen ?? true
    } catch {
      return true
    }
  }
  $effect(() => {
    try {
      localStorage.setItem('pw_stundenleiste', JSON.stringify({ offen }))
    } catch {
      /* localStorage nicht verfuegbar */
    }
  })

  async function laden(): Promise<void> {
    try {
      daten = await ladeStundenUebersicht()
    } catch {
      /* Planung evtl. nicht erreichbar - alten Stand behalten */
    }
  }

  // Erstmals laden + nach jeder Timer-Aktion (Start/Pause/Stopp) aktualisieren.
  let letzterStand = -1
  $effect(() => {
    if (timer.stand !== letzterStand) {
      letzterStand = timer.stand
      laden()
    }
  })

  // Regelmaessig und bei Rueckkehr ins Fenster auffrischen (auch manuelle Nachtraege).
  $effect(() => {
    const iv = setInterval(laden, 60000)
    const beiFokus = () => laden()
    window.addEventListener('focus', beiFokus)
    return () => {
      clearInterval(iv)
      window.removeEventListener('focus', beiFokus)
    }
  })

  const PERIODEN: { key: keyof StundenUebersicht; label: string }[] = [
    { key: 'heute', label: 'Heute' },
    { key: 'woche', label: 'Woche' },
    { key: 'monat', label: 'Monat' },
    { key: 'jahr', label: 'Jahr' },
  ]
</script>

<div class="sl">
  <button class="kopf" onclick={() => (offen = !offen)} aria-expanded={offen}
    title={offen ? 'Stunden einklappen' : 'Stunden ausklappen'}>
    <i class="fa-solid fa-clock" aria-hidden="true"></i>
    <span class="titel">Stunden</span>
    <i class="fa-solid {offen ? 'fa-chevron-up' : 'fa-chevron-down'} chev" aria-hidden="true"></i>
  </button>
  {#if offen}
    <div class="werte">
      {#each PERIODEN as p (p.key)}
        {@const s = daten?.[p.key]}
        <span class="metrik" title="{p.label}: geleistet / Soll">
          <span class="ml">{p.label}</span>
          <span class="ist">{s ? formatStd(s.ist_sek) : '-'}</span>
          <span class="trenner">/</span>
          <span class="soll">{s ? formatStd(s.soll_sek) : '-'}</span>
        </span>
      {/each}
    </div>
  {/if}
</div>

<style>
  .sl {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 5px 14px;
    background: var(--surface-1);
    border-bottom: 1px solid var(--border);
    font-size: 12px;
    flex-wrap: wrap;
  }
  .kopf {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    background: transparent;
    border: none;
    color: var(--text-2);
    cursor: pointer;
    padding: 2px 4px;
  }
  .kopf .titel {
    font-family: var(--font-display);
    font-size: 11.5px;
    letter-spacing: 0.02em;
  }
  .chev {
    font-size: 10px;
    color: var(--text-3);
  }
  .werte {
    display: inline-flex;
    align-items: center;
    gap: 18px;
    flex-wrap: wrap;
  }
  .metrik {
    display: inline-flex;
    align-items: baseline;
    gap: 5px;
  }
  .ml {
    color: var(--text-3);
    font-size: 11px;
  }
  .ist {
    color: var(--ok);
    font-weight: 700;
    font-variant-numeric: tabular-nums;
  }
  .trenner {
    color: var(--text-3);
  }
  .soll {
    color: var(--hl-primary-text);
    font-weight: 400;
    font-variant-numeric: tabular-nums;
  }
</style>
