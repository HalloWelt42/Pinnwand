<script lang="ts">
  import { ladeHeute, schnellErfassen, type HeuteUebersicht, type HeuteEintrag, type ErfassenErgebnis } from '../../api'
  import { oeffneKarte } from '../../navigation.svelte'
  import { tts, vorlesen, stoppeVorlesen } from '../../tts.svelte'
  import { isoKurz, isoGesprochen, formatStd } from '../../zeit'

  let { boardId }: { boardId: string } = $props()
  $effect(() => void boardId)

  let d = $state<HeuteUebersicht | null>(null)

  // Schnell-Erfassung (natuersprachliche Zeitbuchung mit Vorschau)
  let qText = $state('')
  let qVorschau = $state<ErfassenErgebnis | null>(null)
  let qFehler = $state('')
  let qMeldung = $state('')
  async function qPruefen(): Promise<void> {
    qFehler = ''
    qMeldung = ''
    if (!qText.trim()) return
    try {
      qVorschau = await schnellErfassen(qText, true)
    } catch (e) {
      qVorschau = null
      qFehler = e instanceof Error ? e.message : 'nicht verstanden'
    }
  }
  async function qBuchen(): Promise<void> {
    try {
      await schnellErfassen(qText, false)
      qMeldung = 'Zeit gebucht.'
      qText = ''
      qVorschau = null
      ladeHeute().then((x) => (d = x)).catch(() => {})
    } catch (e) {
      qFehler = e instanceof Error ? e.message : 'Buchen fehlgeschlagen'
    }
  }
  function qAbbrechen(): void {
    qVorschau = null
    qFehler = ''
  }

  $effect(() => {
    ladeHeute().then((x) => (d = x)).catch(() => {})
  })

  const gruppen = $derived(
    d
      ? [
          { titel: 'Überfällig', icon: 'fa-triangle-exclamation', klasse: 'rot', items: d.ueberfaellig },
          { titel: 'Heute fällig', icon: 'fa-calendar-day', klasse: '', items: d.heute },
          { titel: 'Diese Woche', icon: 'fa-calendar-week', klasse: '', items: d.diese_woche },
          { titel: 'Läuft gerade', icon: 'fa-play', klasse: 'gruen', items: d.laufend },
          { titel: 'Liegengeblieben', icon: 'fa-hourglass-half', klasse: 'amber', items: d.liegengeblieben },
        ]
      : [],
  )

  function oeffne(e: HeuteEintrag): void {
    oeffneKarte(e.board_id, e.id)
  }

  function briefing(): string {
    if (!d) return ''
    const teile = [`Was steht an am ${isoGesprochen(d.datum)}.`]
    if (d.ueberfaellig.length) teile.push(`${d.ueberfaellig.length} überfällig: ${d.ueberfaellig.map((x) => x.titel).join(', ')}.`)
    if (d.heute.length) teile.push(`Heute fällig: ${d.heute.map((x) => x.titel).join(', ')}.`)
    if (d.diese_woche.length) teile.push(`Diese Woche: ${d.diese_woche.map((x) => x.titel).join(', ')}.`)
    if (d.laufend.length) teile.push(`Es läuft: ${d.laufend.map((x) => x.titel).join(', ')}.`)
    if (teile.length === 1) teile.push('Nichts Dringendes.')
    return teile.join(' ')
  }
  function vorlesenUmschalten(): void {
    if (tts.laeuft) stoppeVorlesen()
    else vorlesen(briefing())
  }
</script>

<div class="heute">
  <div class="kopf">
    <h2>Was steht an</h2>
    <button class="btn" onclick={vorlesenUmschalten}>
      <i class="fa-solid {tts.laeuft ? 'fa-stop' : 'fa-volume-high'}" aria-hidden="true"></i>
      {tts.laeuft ? 'Stopp' : 'Vorlesen'}
    </button>
  </div>

  <div class="quick">
    <i class="fa-solid fa-bolt" aria-hidden="true"></i>
    <input class="qin" placeholder="Schnell erfassen: z.B. R3-130 1:30 Doku geschrieben gestern" bind:value={qText}
      oninput={() => { qVorschau = null; qFehler = '' }}
      onkeydown={(e) => { if (e.key === 'Enter') qPruefen() }} />
    <button class="btn" onclick={qPruefen}>Vorschau</button>
  </div>
  {#if qFehler}<p class="qfehler">{qFehler}</p>{/if}
  {#if qMeldung}<p class="qok">{qMeldung}</p>{/if}
  {#if qVorschau && qVorschau.karte}
    <div class="qvor">
      <span class="ql">Buchung:</span>
      <b>{qVorschau.karte.schluessel ?? ''}</b> {qVorschau.karte.titel}
      <span class="qd">{formatStd(qVorschau.sekunden ?? 0)} h{#if qVorschau.datum} &middot; {isoKurz(qVorschau.datum)}{/if}{#if qVorschau.kommentar} &middot; "{qVorschau.kommentar}"{/if}</span>
      <span class="qbtns">
        <button class="btn primaer" onclick={qBuchen}>Buchen</button>
        <button class="btn geist" onclick={qAbbrechen}>Abbrechen</button>
      </span>
    </div>
  {/if}
  <div class="gitter">
    {#each gruppen as g (g.titel)}
      <section class="karte {g.klasse}">
        <div class="kh"><i class="fa-solid {g.icon}" aria-hidden="true"></i><span class="t">{g.titel}</span><span class="z">{g.items.length}</span></div>
        {#if g.items.length}
          <ul>
            {#each g.items as e (e.id)}
              <li>
                <button class="eintrag" onclick={() => oeffne(e)}>
                  {#if e.schluessel}<span class="key">{e.schluessel}</span>{/if}
                  <span class="ti">{e.titel}</span>
                  {#if e.faellig}<span class="fa">{isoKurz(e.faellig)}</span>{/if}
                </button>
              </li>
            {/each}
          </ul>
        {:else}
          <p class="leer">-</p>
        {/if}
      </section>
    {/each}
  </div>
</div>

<style>
  .heute { height: 100%; overflow-y: auto; padding: 18px; }
  .kopf { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
  .kopf h2 { margin: 0; font-family: var(--font-display); font-size: 17px; color: var(--text-1); }
  .btn { border: 1px solid var(--border); background: var(--surface-2); color: var(--text-2); border-radius: var(--r-m); padding: 7px 12px; font-size: 12.5px; }
  .btn:hover { color: var(--hl-primary-text); border-color: var(--hl-primary); }
  .gitter { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 12px; align-items: start; }
  .karte { border: 1px solid var(--border); background: var(--surface-col); border-radius: var(--r-l); padding: 12px; }
  .kh { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; font-family: var(--font-display); font-size: 13px; color: var(--text-1); }
  .kh .t { flex: 1; }
  .kh .z { font-size: 11px; color: var(--text-3); background: var(--surface-2); border-radius: 999px; padding: 1px 8px; }
  .karte.rot .kh { color: var(--due-rot-fg); }
  .karte.amber .kh { color: var(--due-amber-fg); }
  .karte.gruen .kh { color: var(--ok); }
  ul { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 3px; }
  .eintrag { width: 100%; display: flex; align-items: center; gap: 8px; text-align: left; background: var(--surface-2); border: 1px solid transparent; border-radius: var(--r-s); padding: 6px 9px; color: var(--text-1); font-size: 12px; }
  .eintrag:hover { border-color: var(--border-2); background: var(--surface-3); }
  .key { font-family: var(--font-mono); font-size: 10px; color: var(--text-3); flex: none; }
  .ti { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .fa { font-size: 10.5px; color: var(--text-3); flex: none; }
  .leer { color: var(--text-3); font-size: 12px; margin: 2px 0; }
  .btn.primaer { background: var(--hl-primary); color: var(--hl-on-primary); border-color: transparent; font-weight: 500; }
  .btn.geist { background: transparent; color: var(--text-2); }
  .quick { display: flex; align-items: center; gap: 9px; margin-bottom: 8px; color: var(--text-3); }
  .quick .qin {
    flex: 1; min-width: 0; border: 1px solid var(--border); background: var(--surface-2); color: var(--text-1);
    border-radius: var(--r-m); padding: 8px 11px; font-size: 12.5px;
  }
  .quick .qin:focus { border-color: var(--hl-primary); outline: none; }
  .qfehler { color: var(--gefahr); font-size: 12px; margin: 0 0 8px; }
  .qok { color: var(--ok); font-size: 12px; margin: 0 0 8px; }
  .qvor {
    display: flex; flex-wrap: wrap; align-items: center; gap: 8px;
    background: var(--hl-primary-weich); border: 1px solid var(--hl-primary);
    border-radius: var(--r-m); padding: 9px 12px; font-size: 12.5px; color: var(--text-1); margin-bottom: 12px;
  }
  .qvor .ql { color: var(--hl-primary-text); font-weight: 600; }
  .qvor .qd { color: var(--text-2); }
  .qvor .qbtns { margin-left: auto; display: flex; gap: 7px; }
</style>
