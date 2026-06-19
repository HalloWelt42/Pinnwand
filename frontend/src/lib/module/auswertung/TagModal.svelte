<script lang="ts">
  import { setzeUrlaub, leereTag, type AbwesenheitTyp } from '../../api'

  interface PersonMini { id: string; name: string; kuerzel: string | null }
  let {
    personen,
    typen,
    start,
    onSchliessen,
    onGespeichert,
  }: {
    personen: PersonMini[]
    typen: AbwesenheitTyp[]
    start: { person_id: string; von: string; bis: string }
    onSchliessen: () => void
    onGespeichert: () => void
  } = $props()

  // svelte-ignore state_referenced_locally
  let personId = $state(start.person_id || (personen[0]?.id ?? ''))
  // svelte-ignore state_referenced_locally
  let typ = $state(typen[0]?.code ?? 'urlaub')
  let anteil = $state(1)
  // svelte-ignore state_referenced_locally
  let von = $state(start.von)
  // svelte-ignore state_referenced_locally
  let bis = $state(start.bis)
  let notiz = $state('')
  let arbeitet = $state(false)
  let fehler = $state('')

  const tageImBereich = $derived.by(() => {
    const out: string[] = []
    const a = new Date(von + 'T00:00:00')
    const b = new Date(bis + 'T00:00:00')
    for (let d = a; d <= b; d.setDate(d.getDate() + 1)) out.push(d.toISOString().slice(0, 10))
    return out
  })

  async function eintragen(): Promise<void> {
    if (!personId || !von) { fehler = 'Person und Datum noetig.'; return }
    arbeitet = true
    fehler = ''
    try {
      await setzeUrlaub({ person_id: personId, von, bis: bis || von, anteil, typ, notiz: notiz || undefined })
      onGespeichert()
    } catch {
      fehler = 'Konnte nicht gespeichert werden.'
    } finally {
      arbeitet = false
    }
  }
  async function leeren(): Promise<void> {
    if (!personId) return
    arbeitet = true
    fehler = ''
    try {
      for (const d of tageImBereich) await leereTag(personId, d)
      onGespeichert()
    } catch {
      fehler = 'Konnte nicht geleert werden.'
    } finally {
      arbeitet = false
    }
  }
</script>

<svelte:window onkeydown={(e) => { if (e.key === 'Escape') onSchliessen() }} />
<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
<div class="overlay" role="presentation" onclick={onSchliessen}>
  <!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
  <div class="modal" role="dialog" aria-label="Eintrag" tabindex="-1" onclick={(e) => e.stopPropagation()}>
    <h3>Eintrag {von}{bis && bis !== von ? ' bis ' + bis : ''}</h3>
    <label>Person
      <select bind:value={personId}>
        {#each personen as p (p.id)}<option value={p.id}>{p.name}</option>{/each}
      </select>
    </label>
    <label>Art
      <select bind:value={typ}>
        {#each typen as t (t.code)}<option value={t.code}>{t.name}</option>{/each}
      </select>
    </label>
    <div class="reihe">
      <label>von <input type="date" bind:value={von} /></label>
      <label>bis <input type="date" bind:value={bis} /></label>
      <label>Umfang
        <select bind:value={anteil}><option value={1}>ganzer Tag</option><option value={0.5}>halber Tag</option></select>
      </label>
    </div>
    <label>Notiz
      <input placeholder="optional" bind:value={notiz} />
    </label>
    {#if fehler}<p class="fehler">{fehler}</p>{/if}
    <div class="fuss">
      <button class="btn gefahr" onclick={leeren} disabled={arbeitet}>Tag(e) leeren</button>
      <span class="luecke"></span>
      <button class="btn" onclick={onSchliessen}>Abbrechen</button>
      <button class="btn primaer" onclick={eintragen} disabled={arbeitet}>Eintragen</button>
    </div>
  </div>
</div>

<style>
  .overlay { position: fixed; inset: 0; z-index: 80; background: rgba(0, 0, 0, 0.45); display: flex; align-items: center; justify-content: center; }
  .modal { width: 440px; max-width: 94vw; background: var(--surface-col); border: 1px solid var(--border-2); border-radius: var(--r-xl); padding: 18px; box-shadow: var(--schatten-pop); display: flex; flex-direction: column; gap: 10px; }
  h3 { margin: 0 0 4px; font-family: var(--font-display); font-size: 15px; color: var(--text-1); }
  label { display: flex; flex-direction: column; gap: 4px; font-size: 11.5px; color: var(--text-3); }
  select, input { border: 1px solid var(--border-2); background: var(--surface-2); color: var(--text-1); border-radius: var(--r-m); padding: 7px 9px; font-size: 12.5px; }
  .reihe { display: flex; gap: 8px; }
  .reihe label { flex: 1; }
  .fehler { color: var(--gefahr); font-size: 12px; margin: 0; }
  .fuss { display: flex; align-items: center; gap: 8px; margin-top: 4px; }
  .luecke { flex: 1; }
  .btn { border: 1px solid var(--border); background: var(--surface-2); color: var(--text-2); border-radius: var(--r-m); padding: 8px 13px; font-size: 12.5px; }
  .btn.primaer { background: var(--hl-primary); color: var(--hl-on-primary); border-color: transparent; font-weight: 500; }
  .btn.gefahr { color: var(--gefahr); border-color: var(--gefahr); background: transparent; }
</style>
