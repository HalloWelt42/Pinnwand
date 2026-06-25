<script lang="ts">
  // Dauerhaft sichtbare Stunden-Uebersicht: geleistete Zeit (Ist) gegen Soll
  // fuer Heute, aktuelle Woche, Monat und Jahr. Ist gruen fett, Soll blau duenn.
  // Einklappbar; der Zustand wird im Browser gemerkt.
  import { ladeStundenUebersicht, ladePersonen, type StundenUebersicht, type Person } from './api'
  import { personSicht, setzePersonSicht } from './personSicht.svelte'
  import { formatStd } from './zeit'
  import { timer, formatDauerVoll } from './timer.svelte'
  import { leseJson, schreibeJson } from './uiSpeicher'

  let daten = $state<StundenUebersicht | null>(null)
  let personen = $state<Person[]>([])
  let offen = $state(ladeOffen())

  const aktivKuerzel = $derived(
    personSicht.id ? (personen.find((p) => p.id === personSicht.id)?.kuerzel ?? null) : null,
  )

  $effect(() => {
    ladePersonen().then((p) => (personen = p.filter((x) => x.aktiv))).catch(() => {})
  })

  function ladeOffen(): boolean {
    return leseJson<{ offen?: boolean }>('pw_stundenleiste', {}).offen ?? true
  }
  $effect(() => {
    schreibeJson('pw_stundenleiste', { offen })
  })

  async function laden(): Promise<void> {
    try {
      daten = await ladeStundenUebersicht(personSicht.id || undefined)
    } catch {
      /* Planung evtl. nicht erreichbar - alten Stand behalten */
    }
  }

  // Erstmals laden + nach jeder Timer-Aktion (Start/Pause/Stopp) + bei Personenwechsel.
  let letzterStand = -1
  let letzteId: string | null = null
  $effect(() => {
    if (timer.stand !== letzterStand || personSicht.id !== letzteId) {
      letzterStand = timer.stand
      letzteId = personSicht.id
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

  // Tab-Titel zeigt heutiges Ist/Soll; ein heute laufender Timer tickt live mit.
  function heuteIso(): string {
    const d = new Date()
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
  }
  $effect(() => {
    const h = daten?.heute
    if (!h) {
      document.title = 'Pinnwand'
      return
    }
    let ist = h.ist_sek
    const a = timer.aktiv
    const laeuft = !!a?.laeuft_seit
    // Laufendes Segment nur dazurechnen, wenn es zur aktuellen Sicht passt
    // (Alle, oder die laufende Karte gehoert der gewaehlten Person).
    const zaehltFuerSicht = !personSicht.id || a?.zustaendig === aktivKuerzel
    if (a?.laeuft_seit && a.laeuft_seit.slice(0, 10) === heuteIso() && zaehltFuerSicht) {
      // Noch nicht gebuchtes, laufendes Segment von heute dazurechnen.
      ist += Math.max(0, Math.floor((timer.jetzt - new Date(a.laeuft_seit).getTime()) / 1000))
    }
    const istTxt = laeuft ? formatDauerVoll(ist) : formatStd(ist)
    document.title = `${istTxt} / ${formatStd(h.soll_sek)} - Pinnwand`
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
    {#if personen.length}
      <select class="psel" value={personSicht.id} onchange={(e) => setzePersonSicht(e.currentTarget.value)}
        title="Sicht auf eine Person (Alle = Team-Gesamt)">
        <option value="">Alle</option>
        {#each personen as p (p.id)}<option value={p.id}>{p.kuerzel ?? p.name}</option>{/each}
      </select>
    {/if}
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
  .psel {
    margin-left: auto;
    border: 1px solid var(--border-2);
    background: var(--surface-2);
    color: var(--text-2);
    border-radius: var(--r-s);
    padding: 3px 6px;
    font-size: 11.5px;
  }
</style>
