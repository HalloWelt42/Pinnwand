<script lang="ts">
  import { onMount } from 'svelte'
  import { materialisiereTermine, ladeTerminInstanzen, bestaetigeTermin, lehneTerminAb, bestaetigeAlleTermine, type TerminInstanz } from '../../api'
  import { ymd, isoLang } from '../../zeit'
  import { leseText, schreibeText } from '../../uiSpeicher'

  let offen = $state<TerminInstanz[]>([])
  let sichtbar = $state(false)
  let dauer = $state<Record<string, number>>({})

  const SCHLUESSEL = 'pw_termine_letzter_check'

  async function offeneLaden(): Promise<void> {
    const heute = ymd(new Date())
    offen = (await ladeTerminInstanzen({ status: 'schwebend', bis: heute })) ?? []
  }

  onMount(async () => {
    const heute = ymd(new Date())
    if (leseText(SCHLUESSEL) === heute) return // heute schon gefragt
    try {
      await materialisiereTermine()
      await offeneLaden()
    } catch { return }
    schreibeText(SCHLUESSEL, heute)
    if (offen.length) sichtbar = true
  })

  function dauerVon(i: TerminInstanz): number {
    return dauer[i.id] ?? i.geplant_min
  }
  async function bestaetigen(i: TerminInstanz): Promise<void> {
    await bestaetigeTermin(i.id, dauerVon(i))
    await offeneLaden()
    if (!offen.length) sichtbar = false
  }
  async function ablehnen(i: TerminInstanz): Promise<void> {
    await lehneTerminAb(i.id)
    await offeneLaden()
    if (!offen.length) sichtbar = false
  }
  async function alleWieGeplant(): Promise<void> {
    await bestaetigeAlleTermine(offen.map((i) => i.id))
    await offeneLaden()
    sichtbar = false
  }
  function spaeter(): void {
    sichtbar = false
  }
</script>

<svelte:window onkeydown={(e) => { if (sichtbar && e.key === 'Escape') spaeter() }} />
{#if sichtbar}
  <!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
  <div class="overlay" role="presentation" onclick={spaeter}></div>
  <!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
  <div class="modal" role="dialog" aria-label="Termine bestätigen" tabindex="-1" onclick={(e) => e.stopPropagation()}>
    <h2><i class="fa-solid fa-calendar-check" aria-hidden="true"></i> Termine bestätigen</h2>
    <p class="hint">Haben diese Termine stattgefunden? Dauer bei Bedarf anpassen. Nicht bestätigte Termine werden nicht gebucht.</p>
    <div class="liste">
      {#each offen as i (i.id)}
        <div class="zeile">
          <span class="dat">{isoLang(i.datum)}</span>
          <span class="tit">{i.uhrzeit ? i.uhrzeit + ' ' : ''}{i.titel}{#if i.kuerzel} <span class="k">{i.kuerzel}</span>{/if}</span>
          <input class="dauer" type="number" min="0" step="5" value={dauerVon(i)} onchange={(e) => (dauer[i.id] = parseInt(e.currentTarget.value) || 0)} />
          <span class="me">min</span>
          <button class="mini" onclick={() => bestaetigen(i)}>Fand statt</button>
          <button class="mini geist" onclick={() => ablehnen(i)}>Nein</button>
        </div>
      {/each}
    </div>
    <div class="fuss">
      <button class="text" onclick={spaeter}>Später</button>
      <button class="primaer" onclick={alleWieGeplant}>Alle wie geplant bestätigen</button>
    </div>
  </div>
{/if}

<style>
  .overlay { position: fixed; inset: 0; z-index: 80; background: rgba(0, 0, 0, 0.5); }
  .modal {
    position: fixed; z-index: 81; top: 50%; left: 50%; transform: translate(-50%, -50%);
    width: 560px; max-width: 94vw; max-height: 86vh; overflow-y: auto;
    background: var(--surface-col); border: 1px solid var(--border-2); border-radius: var(--r-xl);
    padding: 20px; box-shadow: var(--schatten-pop);
  }
  h2 { margin: 0 0 6px; font-family: var(--font-display); font-size: 17px; color: var(--text-1); display: flex; align-items: center; gap: 9px; }
  .hint { margin: 0 0 14px; font-size: 12.5px; color: var(--text-2); line-height: 1.5; }
  .liste { display: flex; flex-direction: column; gap: 4px; }
  .zeile { display: flex; align-items: center; gap: 8px; padding: 6px 0; border-bottom: 1px solid var(--border); font-size: 12.5px; }
  .zeile:last-child { border-bottom: none; }
  .dat { flex: 0 0 92px; color: var(--text-2); font-variant-numeric: tabular-nums; }
  .tit { flex: 1; min-width: 0; color: var(--text-1); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .tit .k { color: var(--text-3); font-size: 11px; }
  .dauer { width: 60px; border: 1px solid var(--border); background: var(--surface-2); color: var(--text-1); border-radius: var(--r-s); padding: 4px 6px; font-size: 12px; }
  .me { color: var(--text-3); font-size: 11px; }
  .mini { border: 1px solid var(--hl-primary); background: var(--hl-primary); color: var(--hl-on-primary); border-radius: var(--r-s); padding: 4px 9px; font-size: 11.5px; white-space: nowrap; }
  .mini.geist { background: transparent; color: var(--text-2); border-color: var(--border-2); }
  .fuss { display: flex; align-items: center; justify-content: space-between; margin-top: 16px; }
  .text { border: none; background: transparent; color: var(--text-3); font-size: 12.5px; padding: 8px 10px; }
  .primaer { border: 1px solid transparent; background: var(--hl-primary); color: var(--hl-on-primary); font-weight: 500; border-radius: var(--r-m); padding: 9px 16px; font-size: 12.5px; }
</style>
