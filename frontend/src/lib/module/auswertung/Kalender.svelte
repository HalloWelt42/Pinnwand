<script lang="ts">
  import { ladeZeiteintraege } from '../../api'
  import { ymd, formatStd } from '../../zeit'

  let { boardId }: { boardId: string } = $props()

  let jahr = $state(new Date().getFullYear())
  let monat = $state(new Date().getMonth())
  let tagMap = $state<Map<string, number>>(new Map())
  let maxSek = $state(0)

  const WD = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So']
  const MONATE = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember']
  const HEUTE = ymd(new Date())

  async function laden() {
    void boardId
    const liste = await ladeZeiteintraege(`${jahr}-01-01`, `${jahr}-12-31`)
    const m = new Map<string, number>()
    let mx = 0
    for (const e of liste) {
      const v = (m.get(e.datum) ?? 0) + e.sekunden
      m.set(e.datum, v)
      if (v > mx) mx = v
    }
    tagMap = m
    maxSek = mx
  }
  $effect(() => {
    void jahr
    laden()
  })

  function farbe(sek: number): string {
    if (!sek) return 'var(--surface-2)'
    const r = maxSek > 0 ? sek / maxSek : 1
    const pct = r >= 0.75 ? 100 : r >= 0.5 ? 68 : r >= 0.25 ? 44 : 24
    return `color-mix(in srgb, var(--hl-primary) ${pct}%, transparent)`
  }
  function tipp(key: string, sek: number): string {
    return `${key}: ${sek ? formatStd(sek) + ' h' : 'keine Zeit'}`
  }
  // Kraeftig gefuellte Zellen (Intensitaet >= 68%) brauchen Text in der Auf-Primaer-Farbe fuer Kontrast.
  function kraeftig(sek: number): boolean {
    if (!sek || maxSek <= 0) return false
    return sek / maxSek >= 0.5
  }

  const jahrSumme = $derived([...tagMap.values()].reduce((s, v) => s + v, 0))

  // Jahres-Heatmap: Wochen-Spalten (Mo..So)
  const wochen = $derived.by(() => {
    const start = new Date(jahr, 0, 1)
    const ende = new Date(jahr, 11, 31)
    const ersterWd = (start.getDay() + 6) % 7
    const cursor = new Date(jahr, 0, 1 - ersterWd)
    const out: { key: string; sek: number; imJahr: boolean; monat: number }[][] = []
    while (cursor <= ende || out.length === 0 || ((cursor.getDay() + 6) % 7) !== 0) {
      const woche: { key: string; sek: number; imJahr: boolean; monat: number }[] = []
      for (let i = 0; i < 7; i++) {
        const key = ymd(cursor)
        woche.push({ key, sek: tagMap.get(key) ?? 0, imJahr: cursor.getFullYear() === jahr, monat: cursor.getMonth() })
        cursor.setDate(cursor.getDate() + 1)
      }
      out.push(woche)
      if (out.length > 60) break
    }
    return out
  })
  const monatsLabels = $derived.by(() => {
    const labels: { wi: number; text: string }[] = []
    let last = -1
    wochen.forEach((w, wi) => {
      const erster = w.find((d) => d.imJahr)
      if (erster && erster.monat !== last) {
        labels.push({ wi, text: MONATE[erster.monat].slice(0, 3) })
        last = erster.monat
      }
    })
    return labels
  })

  // Monatsgitter (6x7)
  const zellen = $derived.by(() => {
    const first = new Date(jahr, monat, 1)
    const ersterWd = (first.getDay() + 6) % 7
    const letzter = new Date(jahr, monat + 1, 0).getDate()
    const out: ({ tag: number; key: string; sek: number } | null)[] = []
    for (let i = 0; i < ersterWd; i++) out.push(null)
    for (let d = 1; d <= letzter; d++) {
      const key = ymd(new Date(jahr, monat, d))
      out.push({ tag: d, key, sek: tagMap.get(key) ?? 0 })
    }
    while (out.length < 42) out.push(null)
    return out
  })
  const monatSumme = $derived(zellen.reduce((s, z) => s + (z?.sek ?? 0), 0))

  function monatVor() {
    if (monat === 11) { monat = 0; jahr++ } else monat++
  }
  function monatZurueck() {
    if (monat === 0) { monat = 11; jahr-- } else monat--
  }
</script>

<div class="kal">
  <div class="spalten">
    <section class="karte heat">
      <div class="kh">
        <span class="titel">Aktivität {jahr}</span>
        <span class="ges">{formatStd(jahrSumme)} h gesamt</span>
        <span class="jnav">
          <button class="ib" aria-label="Jahr zurück" onclick={() => jahr--}><i class="fa-solid fa-chevron-left" aria-hidden="true"></i></button>
          <button class="ib" aria-label="Jahr vor" onclick={() => jahr++}><i class="fa-solid fa-chevron-right" aria-hidden="true"></i></button>
        </span>
      </div>
      <div class="hgrid">
        <div class="wdlabels">
          {#each WD as w (w)}<div class="wdl">{w}</div>{/each}
        </div>
        <div class="weeksWrap">
          <div class="mrow">
            {#each wochen as _, wi (wi)}
              {@const m = monatsLabels.find((l) => l.wi === wi)}
              <div class="ml">{m ? m.text : ''}</div>
            {/each}
          </div>
          <div class="weeks">
            {#each wochen as woche, wi (wi)}
              <div class="wcol">
                {#each woche as t (t.key)}
                  {#if t.imJahr}
                    <div class="zelle" class:heute={t.key === HEUTE} style="background:{farbe(t.sek)}" title={tipp(t.key, t.sek)}></div>
                  {:else}
                    <div class="zelle leer"></div>
                  {/if}
                {/each}
              </div>
            {/each}
          </div>
        </div>
      </div>
      <div class="legende">
        <span>weniger</span>
        <div class="zelle" style="background:var(--surface-2)"></div>
        <div class="zelle" style="background:color-mix(in srgb, var(--hl-primary) 24%, transparent)"></div>
        <div class="zelle" style="background:color-mix(in srgb, var(--hl-primary) 44%, transparent)"></div>
        <div class="zelle" style="background:color-mix(in srgb, var(--hl-primary) 68%, transparent)"></div>
        <div class="zelle" style="background:var(--hl-primary)"></div>
        <span>mehr</span>
      </div>
    </section>

    <section class="karte month">
      <div class="kh">
        <button class="ib" aria-label="Monat zurück" onclick={monatZurueck}><i class="fa-solid fa-chevron-left" aria-hidden="true"></i></button>
        <span class="titel">{MONATE[monat]} {jahr}</span>
        <button class="ib" aria-label="Monat vor" onclick={monatVor}><i class="fa-solid fa-chevron-right" aria-hidden="true"></i></button>
        <span class="ges">{formatStd(monatSumme)} h</span>
      </div>
      <div class="mweekdays">{#each WD as w (w)}<div class="mwd">{w}</div>{/each}</div>
      <div class="mgrid">
        {#each zellen as z, i (i)}
          {#if z}
            <div class="mtag" class:heute={z.key === HEUTE} class:kraeftig={kraeftig(z.sek)} style="background:{farbe(z.sek)}" title={tipp(z.key, z.sek)}>
              <span class="mnum">{z.tag}</span>
              {#if z.sek}<span class="mstd">{formatStd(z.sek)}</span>{/if}
            </div>
          {:else}
            <div class="mtag mleer"></div>
          {/if}
        {/each}
      </div>
    </section>
  </div>
</div>

<style>
  .kal {
    height: 100%;
    overflow-y: auto;
    padding: 16px;
  }
  .spalten {
    display: flex;
    flex-wrap: wrap;
    gap: 16px;
    align-items: flex-start;
  }
  .karte {
    background: var(--surface-col);
    border: 1px solid var(--border);
    border-radius: var(--r-xl);
    padding: 14px;
  }
  .kh {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 12px;
  }
  .titel {
    font-family: var(--font-display);
    font-size: 14px;
    font-weight: 600;
    color: var(--text-1);
  }
  .ges {
    font-size: 11px;
    color: var(--text-3);
  }
  .jnav {
    margin-left: auto;
    display: flex;
    gap: 4px;
  }
  .ib {
    width: 26px;
    height: 26px;
    border-radius: var(--r-s);
    border: 1px solid var(--border);
    background: var(--surface-2);
    color: var(--text-2);
    font-size: 11px;
  }
  .ib:hover {
    color: var(--hl-primary-text);
    border-color: var(--hl-primary);
  }
  .hgrid {
    display: flex;
    gap: 6px;
  }
  .wdlabels {
    display: flex;
    flex-direction: column;
    gap: 3px;
    padding-top: 16px;
  }
  .wdl {
    width: 20px;
    height: 11px;
    font-size: 9px;
    color: var(--text-3);
    line-height: 11px;
    text-align: right;
  }
  .weeksWrap {
    display: flex;
    flex-direction: column;
  }
  .mrow {
    display: flex;
    gap: 3px;
    height: 13px;
    margin-bottom: 3px;
  }
  .ml {
    width: 11px;
    font-size: 9px;
    color: var(--text-3);
    white-space: nowrap;
  }
  .weeks {
    display: flex;
    gap: 3px;
  }
  .wcol {
    display: flex;
    flex-direction: column;
    gap: 3px;
  }
  .zelle {
    width: 11px;
    height: 11px;
    border-radius: 2px;
    border: 1px solid transparent;
  }
  .zelle.leer {
    background: transparent;
  }
  .zelle.heute {
    border-color: var(--ok);
  }
  .legende {
    display: flex;
    align-items: center;
    gap: 3px;
    margin-top: 10px;
    padding-left: 26px;
    font-size: 9px;
    color: var(--text-3);
  }
  .legende span {
    padding: 0 4px;
  }
  .mweekdays {
    display: grid;
    grid-template-columns: repeat(7, 38px);
    gap: 5px;
    margin-bottom: 5px;
  }
  .mwd {
    font-size: 9px;
    color: var(--text-3);
    text-align: center;
  }
  .mgrid {
    display: grid;
    grid-template-columns: repeat(7, 38px);
    gap: 5px;
  }
  .mtag {
    position: relative;
    width: 38px;
    height: 38px;
    border-radius: var(--r-s);
    border: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1px;
  }
  .mtag.mleer {
    background: transparent !important;
    border-color: transparent;
  }
  .mtag.heute {
    border-color: var(--ok);
  }
  .mnum {
    font-size: 11px;
    color: var(--text-1);
  }
  .mstd {
    font-size: 8.5px;
    font-family: var(--font-mono);
    color: var(--text-2);
  }
  .mtag.kraeftig .mnum,
  .mtag.kraeftig .mstd {
    color: var(--hl-on-primary);
  }
</style>
