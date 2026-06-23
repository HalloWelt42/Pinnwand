<script lang="ts">
  import {
    transkripteStatus,
    transkripteSuche,
    transkriptDetail,
    markenJeTranskript,
    erstelleMarke,
    ladeMappen,
    ladeBoards,
    ladeBoard,
    ladePool,
    poolAufnehmen,
    poolEntfernen,
    type TranskriptTreffer,
    type TranskriptDetail,
    type TranskriptSegment,
    type TranskriptMarke,
  } from '../../api'
  import type { Karte } from '../../types'
  import { tts, vorlesen, stoppeVorlesen } from '../../tts.svelte'
  import { transkriptNav, oeffneKarte } from '../../navigation.svelte'

  let { boardId }: { boardId: string } = $props()
  $effect(() => void boardId)

  let frage = $state('')
  let treffer = $state<TranskriptTreffer[]>([])
  let aktiv = $state<TranskriptDetail | null>(null)

  // Arbeitspool (Vorfilter): nur ausgewaehlte Transkripte sind im Alltag sichtbar;
  // "Alle" zeigt den ganzen Bestand zum Aus-/Abwaehlen. Modus im Browser gemerkt.
  let modus = $state<'pool' | 'alle'>('pool')
  try {
    const m = localStorage.getItem('pw_transkripte_modus')
    if (m === 'alle' || m === 'pool') modus = m
  } catch { /* localStorage nicht verfuegbar */ }
  $effect(() => { try { localStorage.setItem('pw_transkripte_modus', modus) } catch { /* ignorieren */ } })
  let poolIds = $state<Set<string>>(new Set())
  let sortierung = $state<'name' | 'sprecher'>('name')
  let gruppenOffen = $state<Set<string>>(new Set())

  async function ladePoolIds(): Promise<void> {
    try { poolIds = new Set((await ladePool()).pool.map((p) => p.transkript_id)) } catch { poolIds = new Set() }
  }
  $effect(() => { ladePoolIds() })

  function imPool(id: string): boolean {
    return poolIds.has(id)
  }
  async function poolToggle(t: TranskriptTreffer): Promise<void> {
    if (poolIds.has(t.id)) {
      await poolEntfernen(t.id)
      const s = new Set(poolIds); s.delete(t.id); poolIds = s
    } else {
      await poolAufnehmen(t.id, t.name)
      poolIds = new Set(poolIds).add(t.id)
    }
  }
  function toggleGruppe(name: string): void {
    const s = new Set(gruppenOffen)
    s.has(name) ? s.delete(name) : s.add(name)
    gruppenOffen = s
  }

  // Sichtbare Treffer je nach Modus, gruppiert nach Name (Duplikate = mehrere Fassungen).
  const sichtbar = $derived(modus === 'pool' ? treffer.filter((t) => poolIds.has(t.id)) : treffer)
  const gruppen = $derived.by(() => {
    const map = new Map<string, TranskriptTreffer[]>()
    for (const t of sichtbar) {
      const key = t.name || t.id
      if (!map.has(key)) map.set(key, [])
      map.get(key)!.push(t)
    }
    const arr = [...map.entries()].map(([name, fassungen]) => {
      const sorted = [...fassungen].sort((a, b) => (b.speaker_names?.length ?? 0) - (a.speaker_names?.length ?? 0))
      return { name, fassungen: sorted, primaer: sorted[0], count: sorted.length }
    })
    if (sortierung === 'name') arr.sort((a, b) => a.name.localeCompare(b.name))
    else arr.sort((a, b) => (b.primaer.speaker_names?.length ?? 0) - (a.primaer.speaker_names?.length ?? 0))
    return arr
  })
  let status = $state<{ erreichbar: boolean; konfiguriert: boolean } | null>(null)
  let laeuft = $state(false)
  let timer: ReturnType<typeof setTimeout> | null = null
  let audioEl = $state<HTMLAudioElement | null>(null)

  // Marken (Karten-Verweise) des aktiven Transkripts + Deep-Link-Sprungziel.
  let marken = $state<TranskriptMarke[]>([])
  let zielPos = $state<number | null>(null)
  let aktivSeg = $state<number | null>(null)
  // Ticket-Auswahl beim Anheften eines Segments.
  let anheftenSeg = $state<TranskriptSegment | null>(null)
  let boardListe = $state<{ id: string; titel: string }[]>([])
  let pickBoardId = $state('')
  let pickKarten = $state<Karte[]>([])
  let anheftMeldung = $state('')

  const markiertePositionen = $derived(
    new Set(marken.filter((m) => m.position_sek != null).map((m) => Math.round((m.position_sek as number) * 10))),
  )
  function istMarkiert(start: number): boolean {
    return markiertePositionen.has(Math.round(start * 10))
  }

  function mmss(s: number): string {
    const t = Math.max(0, Math.floor(s))
    return `${Math.floor(t / 60)}:${String(t % 60).padStart(2, '0')}`
  }
  function springe(start: number, i: number | null = null): void {
    aktivSeg = i
    if (!audioEl) return
    try { audioEl.currentTime = start } catch { /* noch keine Metadaten */ }
    void audioEl.play()
  }
  async function ladeMarkenDes(id: string): Promise<void> {
    try { marken = (await markenJeTranskript(id)).marken } catch { marken = [] }
  }
  async function oeffneById(id: string): Promise<void> {
    stoppeVorlesen()
    anheftenSeg = null
    aktivSeg = null
    try {
      aktiv = await transkriptDetail(id)
    } catch {
      aktiv = null
    }
    await ladeMarkenDes(id)
  }
  // Wunsch aus einer verknuepften Karte: dieses Transkript oeffnen, ggf. an Position springen.
  $effect(() => {
    const id = transkriptNav.id
    if (id) {
      const pos = transkriptNav.positionSek
      transkriptNav.id = null
      transkriptNav.positionSek = null
      oeffneById(id).then(() => { zielPos = pos })
    }
  })
  // Nach dem Laden zur gewuenschten Position springen + Segment hervorheben.
  $effect(() => {
    const pos = zielPos
    if (pos == null || !aktiv) return
    setTimeout(() => {
      const segs = aktiv?.segmente ?? []
      let bi = 0
      let bd = Infinity
      segs.forEach((s, i) => { const d = Math.abs((s.start ?? 0) - pos); if (d < bd) { bd = d; bi = i } })
      if (segs.length) {
        aktivSeg = bi
        document.getElementById('seg-' + bi)?.scrollIntoView({ block: 'center' })
      }
      if (audioEl) { try { audioEl.currentTime = pos } catch { /* ignorieren */ } }
      zielPos = null
    }, 250)
  })

  $effect(() => {
    transkripteStatus().then((s) => (status = s)).catch(() => (status = { erreichbar: false, konfiguriert: false }))
  })

  // Erstbefüllung (leere Suche zeigt die neuesten) und entprellte Suche.
  $effect(() => {
    const q = frage
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => suchen(q), 220)
  })

  async function suchen(q: string): Promise<void> {
    if (status && !status.erreichbar) return
    laeuft = true
    try {
      treffer = (await transkripteSuche(q, 40)).treffer
    } catch {
      treffer = []
    } finally {
      laeuft = false
    }
  }

  async function oeffne(t: TranskriptTreffer): Promise<void> {
    await oeffneById(t.id)
  }

  // -- Segment an ein Ticket anheften (Position + Text + Sprecher uebernehmen) --
  async function anheftenStart(seg: TranskriptSegment): Promise<void> {
    anheftMeldung = ''
    anheftenSeg = anheftenSeg === seg ? null : seg
    pickKarten = []
    if (!anheftenSeg) return
    if (!boardListe.length) {
      try {
        const mappen = await ladeMappen()
        const alle: { id: string; titel: string }[] = []
        for (const mp of mappen) {
          for (const b of await ladeBoards(mp.id)) alle.push({ id: b.id, titel: b.titel })
        }
        boardListe = alle
        if (!pickBoardId && alle[0]) pickBoardId = alle[0].id
      } catch {
        boardListe = []
      }
    }
    if (pickBoardId) boardWaehlen(pickBoardId)
  }
  async function boardWaehlen(id: string): Promise<void> {
    pickBoardId = id
    try { pickKarten = (await ladeBoard(id)).karten } catch { pickKarten = [] }
  }
  async function anheften(k: Karte): Promise<void> {
    if (!aktiv || !anheftenSeg) return
    await erstelleMarke({
      karte_id: k.id,
      transkript_id: aktiv.id,
      transkript_name: aktiv.name,
      position_sek: anheftenSeg.start,
      segment_text: anheftenSeg.text,
      sprecher: anheftenSeg.speaker ?? null,
    })
    anheftMeldung = `An ${k.schluessel ?? k.titel} angeheftet.`
    anheftenSeg = null
    await ladeMarkenDes(aktiv.id)
  }
  function zurKarte(m: TranskriptMarke): void {
    if (m.karte_board) oeffneKarte(m.karte_board, m.karte_id, m.karte_schluessel ?? undefined)
  }

  function vorlesenUmschalten(): void {
    if (tts.laeuft) stoppeVorlesen()
    else if (aktiv) vorlesen(aktiv.full_text)
  }

  function hervor(text: string, q: string): string {
    // Einfache Hervorhebung des Suchbegriffs (HTML-sicher).
    const esc = (s: string) => s.replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' })[c] as string)
    if (!q.trim()) return esc(text)
    const re = new RegExp(`(${q.trim().replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi')
    return esc(text).replace(re, '<mark>$1</mark>')
  }
</script>

<div class="trans">
  {#if status && !status.konfiguriert}
    <p class="hinweis">Kein Transkriptions-Dienst konfiguriert.</p>
  {:else if status && !status.erreichbar}
    <p class="hinweis">Transkriptions-Dienst nicht erreichbar. Läuft er?</p>
  {:else}
    <div class="spalten">
      <aside class="liste">
        <div class="kopfzeile">
          <div class="umschalt" role="tablist" aria-label="Transkript-Sicht">
            <button class:an={modus === 'pool'} onclick={() => (modus = 'pool')} title="Nur ausgewaehlte (Arbeitspool)">Arbeitspool</button>
            <button class:an={modus === 'alle'} onclick={() => (modus = 'alle')} title="Alle Transkripte zum Aus-/Abwaehlen">Alle</button>
          </div>
          <select class="sortwahl" bind:value={sortierung} aria-label="Sortierung">
            <option value="name">A-Z</option>
            <option value="sprecher">Sprecher</option>
          </select>
        </div>
        <div class="feldreihe">
          <i class="fa-solid fa-magnifying-glass" aria-hidden="true"></i>
          <input class="frage" placeholder="durchsuchen ..." bind:value={frage} aria-label="Transkripte suchen" />
        </div>
        {#if laeuft}<p class="lade">sucht ...</p>{/if}
        <ul>
          {#each gruppen as g (g.name)}
            <li class="gruppe">
              <div class="grow" class:on={g.fassungen.some((f) => f.id === aktiv?.id)}>
                <button class="nmbtn" onclick={() => oeffne(g.primaer)} title={g.name}>
                  <span class="nm">{g.name}</span>
                  <span class="meta">{g.primaer.speaker_names.length} Sprecher{#if g.count > 1} &middot; {g.count} Fassungen{/if}</span>
                </button>
                {#if g.count > 1}
                  <button class="ic" aria-label="Fassungen anzeigen" onclick={() => toggleGruppe(g.name)}><i class="fa-solid {gruppenOffen.has(g.name) ? 'fa-chevron-up' : 'fa-chevron-down'}" aria-hidden="true"></i></button>
                {/if}
                <button class="star" class:an={imPool(g.primaer.id)} aria-label="In Arbeitspool aufnehmen oder entfernen" onclick={() => poolToggle(g.primaer)}><i class="fa-{imPool(g.primaer.id) ? 'solid' : 'regular'} fa-star" aria-hidden="true"></i></button>
              </div>
              {#if g.count > 1 && gruppenOffen.has(g.name)}
                <div class="fassungen">
                  {#each g.fassungen as f (f.id)}
                    <div class="grow klein" class:on={aktiv?.id === f.id}>
                      <button class="nmbtn" onclick={() => oeffne(f)}>
                        <span class="meta">{f.speaker_names.length} Sprecher{#if f.id === g.primaer.id} (Haupt){/if}</span>
                      </button>
                      <button class="star" class:an={imPool(f.id)} aria-label="In Arbeitspool aufnehmen oder entfernen" onclick={() => poolToggle(f)}><i class="fa-{imPool(f.id) ? 'solid' : 'regular'} fa-star" aria-hidden="true"></i></button>
                    </div>
                  {/each}
                </div>
              {/if}
            </li>
          {/each}
          {#if !gruppen.length && !laeuft}
            <li class="leer">{modus === 'pool' ? 'Arbeitspool ist leer - wechsle zu "Alle" und nimm relevante Transkripte per Stern auf.' : 'Keine Transkripte.'}</li>
          {/if}
        </ul>
      </aside>

      <section class="detail">
        {#if aktiv}
          <header class="dkopf">
            <h2>{aktiv.name}</h2>
            <div class="meta">
              {#if aktiv.language}<span>{aktiv.language}</span>{/if}
              {#if aktiv.speaker_names.length}<span>{aktiv.speaker_names.join(', ')}</span>{/if}
              {#if aktiv.segment_count}<span>{aktiv.segment_count} Segmente</span>{/if}
            </div>
            <div class="aktionen">
              <button class="btn" onclick={vorlesenUmschalten}>
                <i class="fa-solid {tts.laeuft ? 'fa-stop' : 'fa-volume-high'}" aria-hidden="true"></i>
                {tts.laeuft ? 'Stopp' : 'Vorlesen'}
              </button>
            </div>
            {#if aktiv.audio_url}
              <audio class="player" controls src={aktiv.audio_url} bind:this={audioEl}></audio>
            {/if}
            {#if marken.length}
              <div class="verknuepft">
                <span class="vlbl">Verknüpfte Tickets:</span>
                {#each marken as m (m.id)}
                  <button class="vchip" title="Zur Karte springen" onclick={() => zurKarte(m)}>
                    {m.karte_schluessel || m.karte_titel || 'Karte'}{#if m.position_sek != null} &middot; {mmss(m.position_sek)}{/if}
                  </button>
                {/each}
              </div>
            {/if}
            {#if anheftMeldung}<p class="anheftok">{anheftMeldung}</p>{/if}
          </header>
          {#if aktiv.segmente && aktiv.segmente.length}
            <div class="segmente">
              {#each aktiv.segmente as s, i (i)}
                <div class="segzeile" id={'seg-' + i} class:aktiv={aktivSeg === i} class:markiert={istMarkiert(s.start)}>
                  <button class="seg" onclick={() => springe(s.start, i)} title="Zum Segment springen">
                    <span class="szeit">{mmss(s.start)}</span>
                    {#if s.speaker}<span class="sspk">{s.speaker}</span>{/if}
                    <span class="stext">{@html hervor(s.text, frage)}</span>
                  </button>
                  <button class="anheft-btn" class:an={istMarkiert(s.start)} title="An Ticket anheften" aria-label="An Ticket anheften" onclick={() => anheftenStart(s)}>
                    <i class="fa-solid fa-thumbtack" aria-hidden="true"></i>
                  </button>
                </div>
                {#if anheftenSeg === s}
                  <div class="picker">
                    <div class="preihe">
                      <select aria-label="Board" bind:value={pickBoardId} onchange={(e) => boardWaehlen(e.currentTarget.value)}>
                        {#each boardListe as b (b.id)}<option value={b.id}>{b.titel}</option>{/each}
                      </select>
                      <button class="mini geist" onclick={() => (anheftenSeg = null)}>Schliessen</button>
                    </div>
                    <div class="pkarten">
                      {#each pickKarten as k (k.id)}
                        <button class="pk" onclick={() => anheften(k)}>{#if k.schluessel}<span class="pkkey">{k.schluessel}</span>{/if} {k.titel}</button>
                      {/each}
                      {#if !pickKarten.length}<span class="leer">Keine Karten in diesem Board.</span>{/if}
                    </div>
                  </div>
                {/if}
              {/each}
            </div>
          {:else}
            <div class="text">{@html hervor(aktiv.full_text, frage)}</div>
          {/if}
        {:else}
          <p class="leer-d">Links ein Transkript wählen.</p>
        {/if}
      </section>
    </div>
  {/if}
</div>

<style>
  .trans {
    height: 100%;
    overflow: hidden;
    padding: 16px;
  }
  .hinweis {
    color: var(--text-3);
    font-size: 13px;
  }
  .spalten {
    display: grid;
    grid-template-columns: 320px 1fr;
    gap: 16px;
    height: 100%;
    min-height: 0;
  }
  .liste {
    display: flex;
    flex-direction: column;
    min-height: 0;
  }
  .feldreihe {
    display: flex;
    align-items: center;
    gap: 8px;
    background: var(--surface-1);
    border: 1px solid var(--border-2);
    border-radius: var(--r-m);
    padding: 2px 10px;
    color: var(--text-3);
  }
  .feldreihe:focus-within {
    border-color: var(--hl-primary);
  }
  .frage {
    flex: 1;
    border: none;
    background: transparent;
    color: var(--text-1);
    font-size: 13px;
    padding: 9px 0;
    outline: none;
  }
  .lade {
    font-size: 11px;
    color: var(--text-3);
    margin: 6px 2px;
  }
  .liste ul {
    list-style: none;
    margin: 8px 0 0;
    padding: 0;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
  .kopfzeile {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
  }
  .umschalt {
    display: flex;
    flex: 1;
    border: 1px solid var(--border-2);
    border-radius: var(--r-m);
    overflow: hidden;
  }
  .umschalt button {
    flex: 1;
    border: none;
    background: transparent;
    color: var(--text-2);
    font-size: 12px;
    padding: 6px 8px;
  }
  .umschalt button.an {
    background: var(--hl-primary);
    color: var(--hl-on-primary);
    font-weight: 500;
  }
  .sortwahl {
    border: 1px solid var(--border-2);
    background: var(--surface-2);
    color: var(--text-2);
    border-radius: var(--r-m);
    font-size: 12px;
    padding: 6px 6px;
  }
  .gruppe {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }
  .grow {
    display: flex;
    align-items: center;
    gap: 4px;
    background: var(--surface-col);
    border: 1px solid var(--border);
    border-radius: var(--r-m);
    padding: 4px 6px 4px 9px;
  }
  .grow:hover {
    background: var(--surface-3);
  }
  .grow.on {
    border-color: var(--hl-primary);
    background: var(--hl-primary-weich);
  }
  .grow.klein {
    margin-left: 16px;
    padding-top: 3px;
    padding-bottom: 3px;
  }
  .nmbtn {
    flex: 1;
    min-width: 0;
    text-align: left;
    border: none;
    background: transparent;
    color: var(--text-1);
    display: flex;
    flex-direction: column;
    gap: 1px;
    cursor: pointer;
    padding: 4px 0;
  }
  .nm {
    font-size: 12.5px;
    font-weight: 500;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .meta {
    font-size: 10.5px;
    color: var(--text-3);
  }
  .grow .ic {
    flex: none;
    width: 24px;
    height: 24px;
    border: none;
    background: transparent;
    color: var(--text-3);
    border-radius: var(--r-s);
    font-size: 11px;
  }
  .grow .ic:hover {
    color: var(--text-1);
    background: var(--surface-2);
  }
  .star {
    flex: none;
    width: 26px;
    height: 26px;
    border: none;
    background: transparent;
    color: var(--text-3);
    border-radius: var(--r-s);
    font-size: 12px;
  }
  .star:hover {
    background: var(--surface-2);
  }
  .star.an {
    color: var(--prio-mittel);
  }
  .fassungen {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }
  .leer,
  .leer-d {
    color: var(--text-3);
    font-size: 12.5px;
    padding: 8px 2px;
  }
  .detail {
    min-width: 0;
    display: flex;
    flex-direction: column;
    border: 1px solid var(--border);
    border-radius: var(--r-l);
    background: var(--surface-col);
    overflow: hidden;
  }
  .dkopf {
    padding: 14px 16px;
    border-bottom: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  .dkopf h2 {
    margin: 0;
    font-family: var(--font-display);
    font-size: 15px;
    color: var(--text-1);
  }
  .meta {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    font-size: 11px;
    color: var(--text-3);
  }
  .btn {
    align-self: flex-start;
    border: 1px solid var(--hl-primary);
    background: var(--hl-primary);
    color: var(--hl-on-primary);
    border-radius: var(--r-m);
    padding: 7px 12px;
    font-size: 12.5px;
    font-weight: 500;
  }
  .player {
    width: 100%;
    height: 34px;
  }
  .text {
    padding: 14px 16px;
    overflow-y: auto;
    font-size: 13.5px;
    line-height: 1.7;
    color: var(--text-1);
    white-space: pre-wrap;
  }
  .text :global(mark),
  .stext :global(mark) {
    background: var(--hl-primary-weich);
    color: var(--hl-primary-text);
    border-radius: 2px;
  }
  .segmente {
    padding: 10px 12px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 3px;
  }
  .seg {
    display: grid;
    grid-template-columns: 48px auto 1fr;
    gap: 9px;
    align-items: baseline;
    text-align: left;
    background: transparent;
    border: 1px solid transparent;
    border-radius: var(--r-m);
    padding: 6px 9px;
    color: var(--text-1);
    font-size: 13px;
    line-height: 1.55;
    cursor: pointer;
  }
  .seg:hover {
    background: var(--surface-2);
    border-color: var(--border);
  }
  .szeit {
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--hl-primary-text);
    font-variant-numeric: tabular-nums;
  }
  .sspk {
    font-size: 11px;
    color: var(--text-3);
    font-weight: 600;
    white-space: nowrap;
  }
  .stext {
    min-width: 0;
  }
  .segzeile {
    display: flex;
    align-items: stretch;
    gap: 4px;
    border: 1px solid transparent;
    border-radius: var(--r-m);
  }
  .segzeile.aktiv {
    border-color: var(--hl-primary);
    background: var(--hl-primary-weich);
  }
  .segzeile.markiert {
    background: var(--surface-2);
  }
  .segzeile .seg {
    flex: 1;
    min-width: 0;
  }
  .anheft-btn {
    flex: none;
    width: 30px;
    border: none;
    background: transparent;
    color: var(--text-3);
    border-radius: var(--r-s);
    font-size: 12px;
    opacity: 0;
    transition: opacity 0.12s;
  }
  .segzeile:hover .anheft-btn {
    opacity: 0.8;
  }
  .anheft-btn:hover {
    background: var(--surface-3);
    color: var(--hl-primary-text);
    opacity: 1;
  }
  .anheft-btn.an {
    color: var(--hl-primary-text);
    opacity: 1;
  }
  .picker {
    margin: 2px 0 6px 48px;
    border: 1px solid var(--border-2);
    background: var(--surface-1);
    border-radius: var(--r-m);
    padding: 8px;
    display: flex;
    flex-direction: column;
    gap: 7px;
  }
  .preihe {
    display: flex;
    gap: 8px;
    align-items: center;
  }
  .preihe select {
    flex: 1;
    border: 1px solid var(--border-2);
    background: var(--surface-2);
    color: var(--text-1);
    border-radius: var(--r-s);
    padding: 6px 8px;
    font-size: 12.5px;
  }
  .pkarten {
    display: flex;
    flex-direction: column;
    gap: 3px;
    max-height: 220px;
    overflow-y: auto;
  }
  .pk {
    text-align: left;
    border: 1px solid var(--border);
    background: var(--surface-col);
    color: var(--text-1);
    border-radius: var(--r-s);
    padding: 6px 9px;
    font-size: 12.5px;
    display: flex;
    align-items: center;
    gap: 7px;
  }
  .pk:hover {
    border-color: var(--hl-primary);
  }
  .pkkey {
    font-family: var(--font-mono);
    font-size: 10.5px;
    color: var(--hl-primary-text);
    background: var(--hl-primary-weich);
    padding: 1px 6px;
    border-radius: var(--r-s);
  }
  .mini {
    border: 1px solid var(--hl-primary);
    background: var(--hl-primary);
    color: var(--hl-on-primary);
    border-radius: var(--r-s);
    padding: 5px 9px;
    font-size: 11.5px;
    white-space: nowrap;
  }
  .mini.geist {
    background: transparent;
    color: var(--text-2);
    border-color: var(--border-2);
  }
  .verknuepft {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 6px;
  }
  .vlbl {
    font-size: 11px;
    color: var(--text-3);
  }
  .vchip {
    border: 1px solid var(--border-2);
    background: var(--surface-2);
    color: var(--hl-primary-text);
    border-radius: var(--r-s);
    padding: 3px 8px;
    font-size: 11px;
    font-family: var(--font-mono);
  }
  .vchip:hover {
    border-color: var(--hl-primary);
  }
  .anheftok {
    font-size: 11.5px;
    color: var(--ok);
    margin: 0;
  }
</style>
