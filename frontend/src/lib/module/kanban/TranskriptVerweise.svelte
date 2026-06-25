<script lang="ts">
  // Eigenstaendiger Abschnitt: mehrere Transkript-Marken je Karte (Position +
  // editierbare Zusammenfassung, KI-Vorschlag, Sprung ins Transkript).
  import { transkripteSuche, ladeMarken, erstelleMarke, aktualisiereMarke, loescheMarke, zusammenfassungVorschlag, type TranskriptMarke, type TranskriptTreffer } from '../../api'
  import { oeffneTranskript } from '../../navigation.svelte'
  import { mmss } from '../../timer.svelte'

  let { karteId }: { karteId: string } = $props()

  let marken = $state<TranskriptMarke[]>([])
  let mSuche = $state('')
  let mTreffer = $state<TranskriptTreffer[]>([])
  let mTimer: ReturnType<typeof setTimeout> | null = null
  const zusTimer: Record<string, ReturnType<typeof setTimeout>> = {}
  let kiLaeuft = $state<string | null>(null)
  let kiVorschau = $state<Record<string, string>>({})
  let kiFehler = $state<Record<string, string>>({})

  let zuletzt = $state<string | null>(null)
  $effect(() => {
    if (karteId !== zuletzt) {
      zuletzt = karteId
      mSuche = ''
      mTreffer = []
      kiVorschau = {}
      laden()
    }
  })
  async function laden(): Promise<void> {
    try { marken = (await ladeMarken(karteId)).marken } catch { marken = [] }
  }
  function suchen(): void {
    if (mTimer) clearTimeout(mTimer)
    const q = mSuche
    mTimer = setTimeout(async () => {
      try { mTreffer = (await transkripteSuche(q, 12)).treffer } catch { mTreffer = [] }
    }, 220)
  }
  async function hinzufuegen(t: TranskriptTreffer): Promise<void> {
    const m = await erstelleMarke({ karte_id: karteId, transkript_id: t.id, transkript_name: t.name })
    marken = [...marken, m]
    mSuche = ''
    mTreffer = []
  }
  function oeffnen(m: TranskriptMarke): void {
    oeffneTranskript(m.transkript_id, m.position_sek ?? null)
  }
  async function loeschen(m: TranskriptMarke): Promise<void> {
    await loescheMarke(m.id)
    marken = marken.filter((x) => x.id !== m.id)
  }
  function zusAendern(m: TranskriptMarke, wert: string): void {
    m.zusammenfassung = wert
    if (zusTimer[m.id]) clearTimeout(zusTimer[m.id])
    zusTimer[m.id] = setTimeout(() => { aktualisiereMarke(m.id, { zusammenfassung: wert }).catch(() => {}) }, 600)
  }
  async function kiVorschlag(m: TranskriptMarke): Promise<void> {
    kiFehler = { ...kiFehler, [m.id]: '' }
    kiLaeuft = m.id
    try {
      const { zusammenfassung } = await zusammenfassungVorschlag(m.transkript_id, m.position_sek ?? null)
      kiVorschau = { ...kiVorschau, [m.id]: zusammenfassung }
    } catch (e) {
      kiFehler = { ...kiFehler, [m.id]: e instanceof Error ? e.message : 'KI nicht verfügbar' }
    } finally {
      kiLaeuft = null
    }
  }
  function kiVerwerfen(m: TranskriptMarke): void {
    const { [m.id]: _weg, ...rest } = kiVorschau
    kiVorschau = rest
  }
  function kiUebernehmen(m: TranskriptMarke): void {
    const t = kiVorschau[m.id]
    if (t == null) return
    m.zusammenfassung = t
    aktualisiereMarke(m.id, { zusammenfassung: t }).catch(() => {})
    kiVerwerfen(m)
  }
</script>

<p class="sec">Transkript-Verweise</p>
{#each marken as m (m.id)}
  <div class="marke">
    <div class="mkopf">
      <i class="fa-solid fa-headphones" aria-hidden="true"></i>
      <span class="mname">{m.titel || m.transkript_name || 'Transkript'}</span>
      {#if m.position_sek != null}<span class="mzeit">{mmss(m.position_sek)}</span>{/if}
      {#if m.sprecher}<span class="mspk">{m.sprecher}</span>{/if}
      <button class="mini geist" onclick={() => oeffnen(m)}><i class="fa-solid fa-arrow-up-right-from-square" aria-hidden="true"></i> Öffnen</button>
      <button class="ic" aria-label="Verweis entfernen" onclick={() => loeschen(m)}><i class="fa-solid fa-xmark" aria-hidden="true"></i></button>
    </div>
    {#if m.segment_text}<div class="mseg">{m.segment_text}</div>{/if}
    <textarea class="mzus" rows="2" placeholder="Zusammenfassung dieses Abschnitts ..." value={m.zusammenfassung ?? ''} oninput={(e) => zusAendern(m, e.currentTarget.value)}></textarea>
    <div class="mreihe">
      <button class="mini geist" disabled={kiLaeuft === m.id} onclick={() => kiVorschlag(m)}>
        <i class="fa-solid fa-wand-magic-sparkles" aria-hidden="true"></i> {kiLaeuft === m.id ? 'erzeugt ...' : 'KI-Vorschlag'}
      </button>
      {#if kiFehler[m.id]}<span class="mfehler">{kiFehler[m.id]}</span>{/if}
    </div>
    {#if kiVorschau[m.id] != null}
      <div class="kivorschau">
        <div class="kitext">{kiVorschau[m.id]}</div>
        <div class="mreihe">
          <button class="mini" onclick={() => kiUebernehmen(m)}>Übernehmen</button>
          <button class="mini geist" onclick={() => kiVerwerfen(m)}>Verwerfen</button>
        </div>
      </div>
    {/if}
  </div>
{/each}
<input class="feld" placeholder="Transkript suchen und als Verweis anhängen ..." bind:value={mSuche} oninput={suchen} />
{#if mTreffer.length}
  <div class="ttreffer">
    {#each mTreffer as t (t.id)}
      <button class="ttr" onclick={() => hinzufuegen(t)}><i class="fa-regular fa-file-audio" aria-hidden="true"></i> <span>{t.name}</span></button>
    {/each}
  </div>
{/if}

<style>
  .sec { font-family: var(--font-display); font-size: 10.5px; letter-spacing: 0.04em; text-transform: uppercase; color: var(--text-3); margin: 18px 0 8px; }
  .marke { border: 1px solid var(--border); background: var(--surface-2); border-radius: var(--r-m); padding: 9px 10px; margin-bottom: 7px; display: flex; flex-direction: column; gap: 7px; }
  .mkopf { display: flex; align-items: center; gap: 8px; color: var(--text-1); font-size: 12.5px; }
  .mname { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-weight: 500; }
  .mzeit { font-family: var(--font-mono); font-size: 10.5px; color: var(--hl-primary-text); background: var(--hl-primary-weich); padding: 1px 6px; border-radius: var(--r-s); }
  .mspk { font-size: 10.5px; color: var(--text-3); white-space: nowrap; }
  .mseg { font-size: 11.5px; color: var(--text-2); line-height: 1.45; background: var(--surface-1); border-radius: var(--r-s); padding: 5px 8px; }
  .mzus { width: 100%; box-sizing: border-box; border: 1px solid var(--border); background: var(--surface-1); color: var(--text-1); border-radius: var(--r-s); padding: 6px 8px; font-size: 12px; line-height: 1.45; resize: vertical; }
  .mreihe { display: flex; align-items: center; gap: 8px; }
  .mfehler { font-size: 10.5px; color: var(--due-rot-fg); }
  .kivorschau { border: 1px dashed var(--hl-primary); background: var(--hl-primary-weich); border-radius: var(--r-s); padding: 7px 9px; display: flex; flex-direction: column; gap: 6px; }
  .kitext { font-size: 12px; line-height: 1.5; color: var(--text-1); }
  .mini { border: 1px solid var(--hl-primary); background: var(--hl-primary); color: var(--hl-on-primary); border-radius: var(--r-s); padding: 4px 9px; font-size: 11.5px; white-space: nowrap; cursor: pointer; }
  .mini.geist { background: transparent; color: var(--text-2); border-color: var(--border-2); }
  .ic { border: none; background: transparent; color: var(--text-3); cursor: pointer; padding: 2px 4px; }
  .ic:hover { color: var(--text-1); }
  .feld { width: 100%; box-sizing: border-box; border: 1px solid var(--border); background: var(--surface-2); color: var(--text-1); border-radius: var(--r-m); padding: 7px 9px; font-size: 12.5px; margin-top: 6px; }
  .ttreffer { display: flex; flex-direction: column; gap: 3px; margin-top: 5px; }
  .ttr { display: flex; align-items: center; gap: 8px; text-align: left; border: 1px solid var(--border); background: var(--surface-2); color: var(--text-1); border-radius: var(--r-m); padding: 7px 10px; font-size: 12.5px; cursor: pointer; }
  .ttr span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .ttr:hover { border-color: var(--hl-primary); }
</style>
