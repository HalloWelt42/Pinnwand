<script lang="ts">
  import { ladeFlow, type FlowGraph } from '../../api'
  import { oeffneKarte } from '../../navigation.svelte'

  let { boardId }: { boardId: string } = $props()

  // Layout-Masse der automatischen Anordnung.
  const W = 196
  const H = 76
  const GX = 76
  const GY = 24
  const PAD = 24
  const COLS = 4 // nur im abhaengigkeitsfreien Raster

  let graph = $state<FlowGraph | null>(null)
  let laedt = $state(true)
  let fehler = $state(false)

  async function laden(): Promise<void> {
    laedt = true
    fehler = false
    try {
      graph = await ladeFlow(boardId)
    } catch {
      graph = null
      fehler = true
    } finally {
      laedt = false
    }
  }
  $effect(() => {
    void boardId
    laden()
  })

  const hatKanten = $derived((graph?.edges.length ?? 0) > 0)

  interface Platzierung { id: string; x: number; y: number }

  // Knoten automatisch anordnen: nach Abhaengigkeitsschicht (links nach rechts),
  // ohne Abhaengigkeiten als kompaktes Raster.
  const platzierung = $derived.by<Platzierung[]>(() => {
    if (!graph) return []
    const res: Platzierung[] = []
    if (!hatKanten) {
      graph.nodes.forEach((n, i) => {
        res.push({ id: n.id, x: PAD + (i % COLS) * (W + GX), y: PAD + Math.floor(i / COLS) * (H + GY) })
      })
    } else {
      const proSchicht: Record<number, number> = {}
      for (const n of graph.nodes) {
        const idx = proSchicht[n.layer] ?? 0
        proSchicht[n.layer] = idx + 1
        res.push({ id: n.id, x: PAD + n.layer * (W + GX), y: PAD + idx * (H + GY) })
      }
    }
    return res
  })

  const posVon = $derived(new Map(platzierung.map((p) => [p.id, p])))
  // Zusatzpuffer rechts/unten, damit die Bogen der Rueckwaertskanten nicht abgeschnitten werden.
  const leinwandB = $derived(platzierung.length ? Math.max(...platzierung.map((p) => p.x)) + W + PAD + 48 : 400)
  const leinwandH = $derived(platzierung.length ? Math.max(...platzierung.map((p) => p.y)) + H + PAD + 48 : 240)

  interface Kante { id: string; d: string; kritisch: boolean; zyklus: boolean }
  const kanten = $derived.by<Kante[]>(() => {
    if (!graph) return []
    const out: Kante[] = []
    for (const e of graph.edges) {
      const a = posVon.get(e.von)
      const b = posVon.get(e.nach)
      if (!a || !b) continue
      const sx = a.x + W
      const sy = a.y + H / 2
      const tx = b.x
      const ty = b.y + H / 2
      const dx = Math.max(34, (tx - sx) / 2)
      out.push({
        id: e.von + '->' + e.nach,
        d: `M${sx},${sy} C${sx + dx},${sy} ${tx - dx},${ty} ${tx},${ty}`,
        kritisch: e.auf_kritischem_pfad,
        zyklus: e.zyklus,
      })
    }
    return out
  })

  function hhmm(min: number): string {
    const h = Math.floor(min / 60)
    const m = min % 60
    return h ? `${h}:${String(m).padStart(2, '0')} h` : `${m} min`
  }

  const kp = $derived(graph?.kritischer_pfad ?? { karten: [], dauer_min: 0 })
  const zyklen = $derived(graph?.zyklus_kanten.length ?? 0)
</script>

<div class="flowwrap">
<div class="flowtop">
  {#if kp.karten.length > 1}
    <span class="summe"><i class="fa-solid fa-bolt" aria-hidden="true"></i> Kritischer Pfad: {kp.karten.length} Aufgaben{kp.dauer_min > 0 ? ' · ' + hhmm(kp.dauer_min) : ''}</span>
  {:else}
    <span class="summe leer">Kein kritischer Pfad (keine Abhaengigkeiten)</span>
  {/if}
  <div class="legende">
    <span><span class="pkt krit"></span> kritisch</span>
    <span><span class="pkt blk"></span> blockiert</span>
    <span><span class="pkt bereit"></span> startklar</span>
    <span><span class="pkt erl"></span> erledigt</span>
  </div>
</div>

{#if zyklen > 0}
  <div class="zwarn">
    <i class="fa-solid fa-triangle-exclamation" aria-hidden="true"></i>
    Zyklische Abhaengigkeit erkannt ({zyklen} {zyklen === 1 ? 'Kante' : 'Kanten'}). Betroffene Verbindungen sind rot gestrichelt - bitte aufloesen.
  </div>
{/if}

<div class="flow">
  {#if laedt}
    <p class="hinweis">Diagramm wird geladen ...</p>
  {:else if fehler}
    <p class="hinweis">Diagramm konnte nicht geladen werden.</p>
  {:else if !graph || !graph.nodes.length}
    <p class="hinweis">Keine Karten auf diesem Board.</p>
  {:else}
    {#if !hatKanten}
      <p class="hinweis tipp">Noch keine Abhaengigkeiten. Lege im Karten-Detail unter "Abhaengigkeiten" fest, welche Karte eine andere blockiert - dann ordnet dieses Diagramm sie automatisch nach Reihenfolge an und zeigt den kritischen Pfad.</p>
    {/if}
    <div class="canvas" style="width:{leinwandB}px; height:{leinwandH}px;">
      <svg class="kanten" width={leinwandB} height={leinwandH} aria-hidden="true">
        <defs>
          <marker id="pf-norm" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(--text-3)" /></marker>
          <marker id="pf-krit" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(--hl-primary)" /></marker>
          <marker id="pf-zyk" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(--gefahr)" /></marker>
        </defs>
        {#each kanten as e (e.id)}
          <path d={e.d} fill="none"
            stroke={e.zyklus ? 'var(--gefahr)' : e.kritisch ? 'var(--hl-primary)' : 'var(--border-2)'}
            stroke-width={e.kritisch ? 2.4 : 1.6}
            stroke-dasharray={e.zyklus ? '5 4' : undefined}
            marker-end={e.zyklus ? 'url(#pf-zyk)' : e.kritisch ? 'url(#pf-krit)' : 'url(#pf-norm)'} />
        {/each}
      </svg>
      {#each graph.nodes as n (n.id)}
        {@const p = posVon.get(n.id)}
        {#if p}
          <div class="knoten s-{n.status}" class:kritisch={n.auf_kritischem_pfad} class:zyklus={n.in_zyklus}
            style="left:{p.x}px; top:{p.y}px; width:{W}px; height:{H}px;"
            role="button" tabindex="0"
            onclick={() => oeffneKarte(boardId, n.id)}
            onkeydown={(ev) => { if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); oeffneKarte(boardId, n.id) } }}>
            <div class="kkopf">
              {#if n.schluessel}<span class="key">{n.schluessel}</span>{/if}
              <span class="iconrow">
                {#if n.auf_kritischem_pfad}<i class="fa-solid fa-bolt ic-krit" title="kritischer Pfad" aria-hidden="true"></i>{/if}
                {#if n.status === 'blockiert'}<i class="fa-solid fa-lock ic-blk" title="blockiert" aria-hidden="true"></i>{/if}
                {#if n.status === 'startklar'}<i class="fa-solid fa-circle-play ic-bereit" title="startklar" aria-hidden="true"></i>{/if}
                {#if n.status === 'erledigt'}<i class="fa-solid fa-check ic-erl" title="erledigt" aria-hidden="true"></i>{/if}
              </span>
            </div>
            <div class="ktitel">{n.titel}</div>
            {#if n.schaetzung_min > 0}<div class="kmeta">{hhmm(n.schaetzung_min)}</div>{/if}
          </div>
        {/if}
      {/each}
    </div>
  {/if}
</div>
</div>

<style>
  .flowwrap { height: 100%; display: flex; flex-direction: column; }
  .flowtop { flex: none; display: flex; align-items: center; gap: 16px; padding: 10px 14px; border-bottom: 1px solid var(--border); flex-wrap: wrap; }
  .summe { font-size: 12.5px; color: var(--text-1); display: inline-flex; align-items: center; gap: 7px; }
  .summe i { color: var(--hl-primary-text); }
  .summe.leer { color: var(--text-3); }
  .legende { margin-left: auto; display: inline-flex; gap: 12px; font-size: 11.5px; color: var(--text-3); }
  .legende span { display: inline-flex; align-items: center; gap: 5px; }
  .pkt { width: 10px; height: 10px; border-radius: 3px; display: inline-block; }
  .pkt.krit { background: var(--hl-primary); }
  .pkt.blk { background: var(--gefahr); }
  .pkt.bereit { background: var(--ok, #2e7d32); }
  .pkt.erl { background: var(--text-3); }
  .zwarn { flex: none; display: flex; align-items: center; gap: 8px; margin: 10px 14px 0; padding: 8px 12px; font-size: 12px; color: var(--gefahr); background: color-mix(in srgb, var(--gefahr) 12%, transparent); border: 1px solid color-mix(in srgb, var(--gefahr) 35%, transparent); border-radius: var(--r-m); }
  .flow { flex: 1; min-height: 0; overflow: auto; }
  .hinweis { color: var(--text-3); font-size: 12.5px; padding: 16px; }
  .hinweis.tipp { max-width: 70ch; line-height: 1.55; }
  .canvas { position: relative; }
  .kanten { position: absolute; inset: 0; pointer-events: none; }
  .knoten { position: absolute; background: var(--surface-col); border: 1px solid var(--border-2); border-radius: var(--r-m); padding: 8px 10px; box-shadow: var(--schatten-karte); cursor: pointer; overflow: hidden; display: flex; flex-direction: column; gap: 3px; }
  .knoten:hover { border-color: var(--hl-primary); }
  .knoten:focus-visible { outline: 2px solid var(--hl-primary); outline-offset: 1px; }
  .knoten.kritisch { border-color: var(--hl-primary); box-shadow: 0 0 0 1px var(--hl-primary) inset, var(--schatten-karte); }
  .knoten.s-blockiert { border-color: var(--gefahr); }
  .knoten.s-erledigt { opacity: 0.62; }
  .knoten.zyklus { border-color: var(--gefahr); border-style: dashed; }
  .kkopf { display: flex; align-items: center; justify-content: space-between; gap: 6px; }
  .key { font-family: var(--font-mono); font-size: 10px; color: var(--text-3); }
  .iconrow { display: inline-flex; gap: 6px; align-items: center; }
  .iconrow i { font-size: 10.5px; }
  .ic-krit { color: var(--hl-primary-text); }
  .ic-blk { color: var(--gefahr); }
  .ic-bereit { color: var(--ok, #2e7d32); }
  .ic-erl { color: var(--text-3); }
  .ktitel { font-size: 12.5px; color: var(--text-1); line-height: 1.3; max-height: 2.6em; overflow: hidden; }
  .kmeta { font-size: 10.5px; color: var(--text-3); font-family: var(--font-mono); }
</style>
