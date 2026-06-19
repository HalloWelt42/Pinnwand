<script lang="ts">
  import { ladeBoard, aktualisiereKarte } from '../../api'
  import type { BoardDetail, Karte, Spalte } from '../../types'

  let { boardId }: { boardId: string } = $props()

  const BOX_B = 180
  const BOX_H = 70
  const SP_X = 230
  const SP_Y = 96

  let board = $state<BoardDetail | null>(null)
  let pos = $state<Record<string, { x: number; y: number }>>({})
  let verknuepfen = $state(false)
  let quelle = $state<string | null>(null)
  let hinweis = $state('')

  async function laden(): Promise<void> {
    const b = await ladeBoard(boardId)
    board = b
    const spaltenIdx: Record<string, number> = {}
    b.spalten.forEach((s, i) => (spaltenIdx[s.id] = i))
    const zaehler: Record<string, number> = {}
    const p: Record<string, { x: number; y: number }> = {}
    for (const k of b.karten) {
      if (k.flow_x != null && k.flow_y != null) {
        p[k.id] = { x: k.flow_x, y: k.flow_y }
      } else {
        const sp = spaltenIdx[k.spalte] ?? 0
        const r = (zaehler[k.spalte] = (zaehler[k.spalte] ?? 0) + 1) - 1
        p[k.id] = { x: 20 + sp * SP_X, y: 20 + r * SP_Y }
      }
    }
    pos = p
  }
  $effect(() => {
    void boardId
    laden()
  })

  const karten = $derived(board?.karten ?? [])
  const doneSpalten = $derived(new Set((board?.spalten ?? []).filter((s) => s.erledigt).map((s) => s.id)))

  function blockiert(k: Karte): boolean {
    // rot, wenn ein blockierender Vorgaenger noch nicht erledigt ist
    return (k.blockiert_von ?? []).some((id) => {
      const v = karten.find((x) => x.id === id)
      return v ? !doneSpalten.has(v.spalte) : false
    })
  }

  // -- Ziehen --
  let zieht: string | null = null
  let startMaus = { x: 0, y: 0 }
  let startPos = { x: 0, y: 0 }
  function down(e: PointerEvent, k: Karte): void {
    if (verknuepfen) {
      verknuepfe(k)
      return
    }
    zieht = k.id
    startMaus = { x: e.clientX, y: e.clientY }
    startPos = { ...pos[k.id] }
    window.addEventListener('pointermove', move)
    window.addEventListener('pointerup', up, { once: true })
  }
  function move(e: PointerEvent): void {
    if (!zieht) return
    pos[zieht] = { x: Math.max(0, startPos.x + (e.clientX - startMaus.x)), y: Math.max(0, startPos.y + (e.clientY - startMaus.y)) }
  }
  async function up(): Promise<void> {
    window.removeEventListener('pointermove', move)
    const id = zieht
    zieht = null
    if (id && pos[id]) await aktualisiereKarte(id, { flow_x: Math.round(pos[id].x), flow_y: Math.round(pos[id].y) })
  }

  // -- Verknuepfen --
  async function verknuepfe(ziel: Karte): Promise<void> {
    if (!quelle) {
      quelle = ziel.id
      hinweis = 'Jetzt die abhaengige Karte waehlen (wird vom ersten blockiert).'
      return
    }
    if (quelle === ziel.id) {
      quelle = null
      hinweis = ''
      return
    }
    const liste = new Set(ziel.blockiert_von ?? [])
    liste.add(quelle)
    await aktualisiereKarte(ziel.id, { blockiert_von: [...liste] })
    quelle = null
    hinweis = ''
    await laden()
  }
  async function entferne(k: Karte, vonId: string): Promise<void> {
    await aktualisiereKarte(k.id, { blockiert_von: (k.blockiert_von ?? []).filter((x) => x !== vonId) })
    await laden()
  }

  function mitte(id: string): { x: number; y: number } {
    const p = pos[id] ?? { x: 0, y: 0 }
    return { x: p.x + BOX_B / 2, y: p.y + BOX_H / 2 }
  }
  const kanten = $derived(
    karten.flatMap((k) =>
      (k.blockiert_von ?? [])
        .filter((vid) => pos[vid] && pos[k.id])
        .map((vid) => ({ id: vid + '->' + k.id, von: mitte(vid), zu: mitte(k.id) })),
    ),
  )
</script>

<div class="flowtop">
  <button class="btn" class:an={verknuepfen} onclick={() => { verknuepfen = !verknuepfen; quelle = null; hinweis = verknuepfen ? 'Verknuepfen: erst die blockierende, dann die abhaengige Karte klicken.' : '' }}>
    <i class="fa-solid fa-diagram-project" aria-hidden="true"></i> {verknuepfen ? 'Verknuepfen aktiv' : 'Verknuepfen'}
  </button>
  {#if hinweis}<span class="hw">{hinweis}</span>{/if}
  <span class="legende"><span class="pkt rot"></span> blockiert</span>
</div>

<div class="flow">
  <div class="canvas">
    <svg class="kanten" aria-hidden="true">
      <defs>
        <marker id="pfeil" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
          <path d="M0,0 L10,5 L0,10 z" fill="var(--text-3)" />
        </marker>
      </defs>
      {#each kanten as e (e.id)}
        <line x1={e.von.x} y1={e.von.y} x2={e.zu.x} y2={e.zu.y} stroke="var(--text-3)" stroke-width="1.6" marker-end="url(#pfeil)" />
      {/each}
    </svg>
    {#each karten as k (k.id)}
      <div
        class="box"
        class:blockiert={blockiert(k)}
        class:quelle={quelle === k.id}
        style="left:{pos[k.id]?.x ?? 0}px; top:{pos[k.id]?.y ?? 0}px; width:{BOX_B}px;"
        onpointerdown={(e) => down(e, k)}
        role="button"
        tabindex="0"
      >
        <div class="bk">
          {#if k.schluessel}<span class="key">{k.schluessel}</span>{/if}
          {#if blockiert(k)}<i class="fa-solid fa-lock rot" aria-hidden="true"></i>{/if}
        </div>
        <div class="bt">{k.titel}</div>
        {#if (k.blockiert_von ?? []).length}
          <div class="deps">
            {#each k.blockiert_von ?? [] as vid (vid)}
              {@const v = karten.find((x) => x.id === vid)}
              <span class="dep">{v?.schluessel ?? '?'}<button aria-label="Verknuepfung entfernen" onpointerdown={(ev) => ev.stopPropagation()} onclick={() => entferne(k, vid)}><i class="fa-solid fa-xmark" aria-hidden="true"></i></button></span>
            {/each}
          </div>
        {/if}
      </div>
    {/each}
  </div>
</div>

<style>
  .flowtop { display: flex; align-items: center; gap: 12px; padding: 10px 14px; border-bottom: 1px solid var(--border); }
  .btn { border: 1px solid var(--border); background: var(--surface-2); color: var(--text-2); border-radius: var(--r-m); padding: 7px 12px; font-size: 12.5px; }
  .btn.an { background: var(--hl-primary); color: var(--hl-on-primary); border-color: transparent; }
  .hw { font-size: 12px; color: var(--text-3); }
  .legende { margin-left: auto; font-size: 11.5px; color: var(--text-3); display: inline-flex; align-items: center; gap: 6px; }
  .pkt { width: 10px; height: 10px; border-radius: 3px; display: inline-block; }
  .pkt.rot { background: var(--gefahr); }
  .flow { height: calc(100% - 44px); overflow: auto; }
  .canvas { position: relative; width: 2200px; height: 1500px; }
  .kanten { position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: none; }
  .box { position: absolute; background: var(--surface-col); border: 1px solid var(--border-2); border-radius: var(--r-m); padding: 8px 10px; cursor: grab; box-shadow: var(--schatten-karte); user-select: none; }
  .box:active { cursor: grabbing; }
  .box.blockiert { border-color: var(--gefahr); }
  .box.quelle { border-color: var(--hl-primary); box-shadow: 0 0 0 2px var(--hl-primary-weich); }
  .bk { display: flex; align-items: center; gap: 6px; }
  .key { font-family: var(--font-mono); font-size: 10px; color: var(--text-3); }
  .rot { color: var(--gefahr); font-size: 10px; }
  .bt { font-size: 12.5px; color: var(--text-1); margin-top: 2px; line-height: 1.3; max-height: 2.6em; overflow: hidden; }
  .deps { display: flex; flex-wrap: wrap; gap: 3px; margin-top: 5px; }
  .dep { display: inline-flex; align-items: center; gap: 3px; font-size: 9.5px; font-family: var(--font-mono); background: var(--surface-2); color: var(--text-3); border-radius: 999px; padding: 1px 6px; }
  .dep button { border: none; background: transparent; color: var(--text-3); font-size: 8px; padding: 0; }
  .dep button:hover { color: var(--gefahr); }
</style>
