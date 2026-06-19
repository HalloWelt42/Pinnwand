<script lang="ts">
  import { ladeHeute, type HeuteUebersicht, type HeuteEintrag } from '../../api'
  import { oeffneKarte } from '../../navigation.svelte'
  import { tts, vorlesen, stoppeVorlesen } from '../../tts.svelte'

  let { boardId }: { boardId: string } = $props()
  $effect(() => void boardId)

  let d = $state<HeuteUebersicht | null>(null)

  $effect(() => {
    ladeHeute().then((x) => (d = x)).catch(() => {})
  })

  const gruppen = $derived(
    d
      ? [
          { titel: 'Ueberfaellig', icon: 'fa-triangle-exclamation', klasse: 'rot', items: d.ueberfaellig },
          { titel: 'Heute faellig', icon: 'fa-calendar-day', klasse: '', items: d.heute },
          { titel: 'Diese Woche', icon: 'fa-calendar-week', klasse: '', items: d.diese_woche },
          { titel: 'Laeuft gerade', icon: 'fa-play', klasse: 'gruen', items: d.laufend },
          { titel: 'Liegengeblieben', icon: 'fa-hourglass-half', klasse: 'amber', items: d.liegengeblieben },
        ]
      : [],
  )

  function oeffne(e: HeuteEintrag): void {
    oeffneKarte(e.board_id, e.id)
  }

  function briefing(): string {
    if (!d) return ''
    const teile = [`Was steht an am ${d.datum}.`]
    if (d.ueberfaellig.length) teile.push(`${d.ueberfaellig.length} ueberfaellig: ${d.ueberfaellig.map((x) => x.titel).join(', ')}.`)
    if (d.heute.length) teile.push(`Heute faellig: ${d.heute.map((x) => x.titel).join(', ')}.`)
    if (d.diese_woche.length) teile.push(`Diese Woche: ${d.diese_woche.map((x) => x.titel).join(', ')}.`)
    if (d.laufend.length) teile.push(`Es laeuft: ${d.laufend.map((x) => x.titel).join(', ')}.`)
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
                  {#if e.faellig}<span class="fa">{e.faellig.slice(5)}</span>{/if}
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
</style>
