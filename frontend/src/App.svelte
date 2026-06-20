<script lang="ts">
  import { onMount } from 'svelte'
  import type { Component } from 'svelte'
  import type { Board, Projektmappe } from './lib/types'
  import { ladeMappen, ladeBoards, ladeErweiterungen, erstelleBoard, benenneBoard, loescheBoard, erstelleMappe, benenneMappe, loescheMappe } from './lib/api'
  import { ansichten, komponenteFuer } from './lib/module/registry'
  import { theme, wechsleTheme } from './lib/theme/theme.svelte'
  import { VERSION } from './lib/version'
  import { aktualisiereLaufend } from './lib/timer.svelte'
  import { nav } from './lib/navigation.svelte'
  import Toast from './lib/Toast.svelte'
  import LaufBar from './lib/LaufBar.svelte'
  import DiensteStatus from './lib/DiensteStatus.svelte'
  import Hilfe from './lib/Hilfe.svelte'
  import Onboarding from './lib/Onboarding.svelte'

  interface Ansicht {
    id: string
    titel: string
    icon: string
    komponente: Component<{ boardId: string }>
  }

  // UI-Zustand im Browser merken (Sidebar, aktive Ansicht, letztes Board).
  const _ui: { rail?: boolean; ansicht?: string; board?: string | null } = (() => {
    try {
      return JSON.parse(localStorage.getItem('pw_ui') || '{}')
    } catch {
      return {}
    }
  })()
  function _merkeUi(): void {
    try {
      localStorage.setItem('pw_ui', JSON.stringify({ rail: railEin, ansicht: aktiveAnsicht, board: aktivesBoard?.id ?? null }))
    } catch {
      /* localStorage nicht verfügbar */
    }
  }

  // Startpfad frühzeitig sichern (bevor Effekte die URL anfassen können).
  const _startPfad = typeof window !== 'undefined' ? window.location.pathname : '/'
  let routingBereit = $state(false)

  // Hilfe + Einrichtungs-Assistent.
  let hilfeOffen = $state(false)
  let onboardingOffen = $state((() => {
    try {
      return localStorage.getItem('pw_onboarding_done') !== '1'
    } catch {
      return false
    }
  })())
  function onboardingFertig(): void {
    onboardingOffen = false
    try {
      localStorage.setItem('pw_onboarding_done', '1')
    } catch {
      /* ignorieren */
    }
  }
  function geheZuAnsicht(id: string): void {
    if (ansichtsListe.some((a) => a.id === id)) aktiveAnsicht = id
  }

  let mappen = $state<Projektmappe[]>([])
  let aktiveMappe = $state<Projektmappe | null>(null)
  let boards = $state<Board[]>([])
  let aktivesBoard = $state<Board | null>(null)
  let fehler = $state<string | null>(null)

  let ansichtsListe = $state<Ansicht[]>([])
  let aktiveAnsicht = $state('')
  const aktuelleKomponente = $derived(ansichtsListe.find((a) => a.id === aktiveAnsicht)?.komponente)

  // Globale Ansichten brauchen keine Board-Navigation; boardgebundene schon.
  const GLOBALE_ANSICHTEN = new Set(['heute', 'suche', 'transkripte', 'planung', 'jahreskalender', 'berichte', 'einstellungen'])
  const boardgebunden = $derived(!GLOBALE_ANSICHTEN.has(aktiveAnsicht))
  const aktuelleAnsichtMeta = $derived(ansichtsListe.find((a) => a.id === aktiveAnsicht))

  // Navigationswunsch (z.B. aus der Suche): zum Board wechseln; Board öffnet die Karte.
  $effect(() => {
    const ziel = nav.ziel
    if (!ziel) return
    const b = boards.find((x) => x.id === ziel.boardId)
    if (b) {
      if (ansichtsListe.some((a) => a.id === 'board')) aktiveAnsicht = 'board'
      aktivesBoard = b
    }
  })

  let bearbeiteBoardId = $state<string | null>(null)
  let loescheBoardId = $state<string | null>(null)
  let boardEntwurf = $state('')
  let neuesBoard = $state(false)
  let neuerBoardTitel = $state('')
  let bearbeiteMappeId = $state<string | null>(null)
  let loescheMappeId = $state<string | null>(null)
  let mappeEntwurf = $state('')
  let neueMappe = $state(false)
  let neuerMappeTitel = $state('')
  let railEin = $state(_ui.rail !== false)

  // Änderungen am UI-Zustand merken.
  $effect(() => {
    void railEin
    void aktiveAnsicht
    void aktivesBoard
    _merkeUi()
  })

  // Routing ohne Hashes: echte Pfade /ansicht bzw. /ansicht/boardId.
  function pfadAusZustand(): string {
    if (!aktiveAnsicht) return '/'
    return boardgebunden && aktivesBoard ? `/${aktiveAnsicht}/${aktivesBoard.id}` : `/${aktiveAnsicht}`
  }
  function wendePfadAn(pfad: string): void {
    const [ans, bId] = pfad.split('/').filter(Boolean)
    if (ans && ansichtsListe.some((a) => a.id === ans)) aktiveAnsicht = ans
    if (bId) {
      const b = boards.find((x) => x.id === bId)
      if (b) aktivesBoard = b
    }
  }
  $effect(() => {
    const p = pfadAusZustand()
    if (!routingBereit) return
    if (typeof window !== 'undefined' && window.location.pathname !== p) {
      window.history.pushState(null, '', p)
    }
  })

  async function ladeBoardListe() {
    if (aktiveMappe) boards = await ladeBoards(aktiveMappe.id)
  }
  async function waehleMappe(m: Projektmappe) {
    aktiveMappe = m
    bearbeiteBoardId = null
    loescheBoardId = null
    neuesBoard = false
    await ladeBoardListe()
    aktivesBoard = boards.find((b) => b.id === _ui.board) ?? boards[0] ?? null
  }
  async function neueMappeErstellen() {
    const t = neuerMappeTitel.trim()
    if (!t) return
    const neu = await erstelleMappe(t)
    mappen = await ladeMappen()
    neuerMappeTitel = ''
    neueMappe = false
    const ziel = mappen.find((m) => m.id === neu.id) ?? neu
    await waehleMappe(ziel)
  }
  async function mappeSpeichern(id: string) {
    const t = mappeEntwurf.trim()
    if (t) {
      await benenneMappe(id, t)
      mappen = await ladeMappen()
      if (aktiveMappe?.id === id) aktiveMappe = mappen.find((m) => m.id === id) ?? aktiveMappe
    }
    bearbeiteMappeId = null
  }
  async function mappeLoeschenBestaetigt(id: string) {
    await loescheMappe(id)
    loescheMappeId = null
    mappen = await ladeMappen()
    if (aktiveMappe?.id === id) {
      const ziel = mappen[0] ?? null
      if (ziel) await waehleMappe(ziel)
      else { aktiveMappe = null; boards = []; aktivesBoard = null }
    }
  }
  async function neuesBoardErstellen() {
    const t = neuerBoardTitel.trim()
    if (!t || !aktiveMappe) return
    const neu = await erstelleBoard(aktiveMappe.id, t)
    await ladeBoardListe()
    aktivesBoard = boards.find((b) => b.id === neu.id) ?? aktivesBoard
    neuerBoardTitel = ''
    neuesBoard = false
  }
  async function boardSpeichern(id: string) {
    const t = boardEntwurf.trim()
    if (t) {
      await benenneBoard(id, t)
      await ladeBoardListe()
      if (aktivesBoard?.id === id) aktivesBoard = boards.find((b) => b.id === id) ?? aktivesBoard
    }
    bearbeiteBoardId = null
  }
  async function boardLoeschenBestaetigt(id: string) {
    await loescheBoard(id)
    loescheBoardId = null
    await ladeBoardListe()
    if (aktivesBoard?.id === id) aktivesBoard = boards[0] ?? null
  }

  async function ladeAnsichten() {
    try {
      const erw = await ladeErweiterungen()
      ansichtsListe = erw.views
        .map((v) => {
          const k = komponenteFuer(v.wert.id)
          return k ? { ...v.wert, komponente: k } : null
        })
        .filter((a): a is Ansicht => a !== null)
    } catch {
      ansichtsListe = ansichten().map((a) => ({ id: a.id, titel: a.titel, icon: a.icon, komponente: a.komponente }))
    }
    const REIHENFOLGE = ['heute', 'board', 'zeiten', 'kalender', 'jahreskalender', 'serien', 'suche', 'transkripte', 'planung', 'berichte', 'einstellungen']
    ansichtsListe.sort((a, b) => ((REIHENFOLGE.indexOf(a.id) + 1) || 99) - ((REIHENFOLGE.indexOf(b.id) + 1) || 99))
    const gespeichert = _ui.ansicht
    aktiveAnsicht = gespeichert && ansichtsListe.some((a) => a.id === gespeichert)
      ? gespeichert
      : ansichtsListe[0]?.id ?? ''
  }

  onMount(async () => {
    await ladeAnsichten()
    aktualisiereLaufend()
    try {
      mappen = await ladeMappen()
      if (mappen[0]) await waehleMappe(mappen[0])
    } catch (e) {
      fehler = e instanceof Error ? e.message : 'unbekannter Fehler'
    }
    // Deep-Link aus dem (früh gesicherten) Startpfad anwenden, dann Routing scharf schalten.
    if (_startPfad && _startPfad !== '/') {
      wendePfadAn(_startPfad)
    }
    routingBereit = true
    window.addEventListener('popstate', () => wendePfadAn(window.location.pathname))
  })
</script>

<div class="wurzel">
<LaufBar />
<div class="app">
  <aside class="rail" class:zu={!railEin}>
    <div class="marke">
      <img class="logo" src="/favicon.svg" alt="" />
      <span class="name">Pinnwand <span class="ver">v{VERSION}</span></span>
      <button class="railtog" aria-label="Seitenleiste ein- oder ausklappen" onclick={() => (railEin = !railEin)}>
        <i class="fa-solid {railEin ? 'fa-angles-left' : 'fa-angles-right'}" aria-hidden="true"></i>
      </button>
    </div>

    <p class="rubrik">Ansichten</p>
    <nav>
      {#each ansichtsListe as a (a.id)}
        <button class="zeile menu" class:aktiv={aktiveAnsicht === a.id} onclick={() => (aktiveAnsicht = a.id)} title={a.titel}>
          <i class={a.icon} aria-hidden="true"></i><span>{a.titel}</span>
        </button>
      {/each}
    </nav>

    {#if boardgebunden}
    <p class="rubrik">Projektmappen</p>
    <nav>
      {#each mappen as m (m.id)}
        {#if bearbeiteMappeId === m.id}
          <!-- svelte-ignore a11y_autofocus -->
          <input class="feld" bind:value={mappeEntwurf} aria-label="Mappe umbenennen" autofocus
            onkeydown={(e) => { if (e.key === 'Enter') mappeSpeichern(m.id); if (e.key === 'Escape') (bearbeiteMappeId = null) }}
            onblur={() => mappeSpeichern(m.id)} />
        {:else if loescheMappeId === m.id}
          <div class="confirm">
            <span>Mappe samt allen Boards und Karten löschen?</span>
            <div class="reihe">
              <button class="mini gefahr" onclick={() => mappeLoeschenBestaetigt(m.id)}>Löschen</button>
              <button class="mini geist" onclick={() => (loescheMappeId = null)}>Abbrechen</button>
            </div>
          </div>
        {:else}
          <div class="zeile board" class:aktiv={aktiveMappe?.id === m.id}>
            <button class="bname" onclick={() => waehleMappe(m)} title={m.titel}>
              <i class="fa-solid fa-folder" aria-hidden="true"></i><span>{m.titel}</span>
            </button>
            <div class="aktionen">
              <button class="ic" aria-label="Mappe umbenennen" onclick={() => { bearbeiteMappeId = m.id; mappeEntwurf = m.titel }}><i class="fa-solid fa-pen" aria-hidden="true"></i></button>
              {#if mappen.length > 1}
                <button class="ic" aria-label="Mappe löschen" onclick={() => (loescheMappeId = m.id)}><i class="fa-solid fa-trash" aria-hidden="true"></i></button>
              {/if}
            </div>
          </div>
        {/if}
      {/each}

      {#if neueMappe}
        <!-- svelte-ignore a11y_autofocus -->
        <input class="feld" placeholder="Mappen-Name" bind:value={neuerMappeTitel} aria-label="Neue Mappe" autofocus
          onkeydown={(e) => { if (e.key === 'Enter') neueMappeErstellen(); if (e.key === 'Escape') { neueMappe = false; neuerMappeTitel = '' } }} />
      {:else}
        <button class="add" onclick={() => (neueMappe = true)}><i class="fa-solid fa-plus" aria-hidden="true"></i> Mappe</button>
      {/if}
    </nav>

    {#if aktiveMappe}
      <p class="rubrik">Boards</p>
      <nav>
        {#each boards as b (b.id)}
          {#if bearbeiteBoardId === b.id}
            <!-- svelte-ignore a11y_autofocus -->
            <input class="feld" bind:value={boardEntwurf} aria-label="Board umbenennen" autofocus
              onkeydown={(e) => { if (e.key === 'Enter') boardSpeichern(b.id); if (e.key === 'Escape') (bearbeiteBoardId = null) }}
              onblur={() => boardSpeichern(b.id)} />
          {:else if loescheBoardId === b.id}
            <div class="confirm">
              <span>Board und alle Karten löschen?</span>
              <div class="reihe">
                <button class="mini gefahr" onclick={() => boardLoeschenBestaetigt(b.id)}>Löschen</button>
                <button class="mini geist" onclick={() => (loescheBoardId = null)}>Abbrechen</button>
              </div>
            </div>
          {:else}
            <div class="zeile board" class:aktiv={aktivesBoard?.id === b.id}>
              <button class="bname" onclick={() => (aktivesBoard = b)}>
                <i class="fa-solid fa-table-columns" aria-hidden="true"></i><span>{b.titel}</span>
              </button>
              <div class="aktionen">
                <button class="ic" aria-label="Umbenennen" onclick={() => { bearbeiteBoardId = b.id; boardEntwurf = b.titel }}><i class="fa-solid fa-pen" aria-hidden="true"></i></button>
                <button class="ic" aria-label="Löschen" onclick={() => (loescheBoardId = b.id)}><i class="fa-solid fa-trash" aria-hidden="true"></i></button>
              </div>
            </div>
          {/if}
        {/each}

        {#if neuesBoard}
          <!-- svelte-ignore a11y_autofocus -->
          <input class="feld" placeholder="Board-Name" bind:value={neuerBoardTitel} aria-label="Neues Board" autofocus
            onkeydown={(e) => { if (e.key === 'Enter') neuesBoardErstellen(); if (e.key === 'Escape') { neuesBoard = false; neuerBoardTitel = '' } }} />
        {:else}
          <button class="add" onclick={() => (neuesBoard = true)}><i class="fa-solid fa-plus" aria-hidden="true"></i> Board</button>
        {/if}
      </nav>
    {/if}
    {/if}

    <div class="fussbereich">
      <DiensteStatus />
      <div class="fzeile">
        <button class="thema" onclick={wechsleTheme} aria-label="Theme wechseln">
          <i class={theme.modus === 'dunkel' ? 'fa-solid fa-sun' : 'fa-solid fa-moon'} aria-hidden="true"></i>
          <span>{theme.modus === 'dunkel' ? 'Hell' : 'Dunkel'}</span>
        </button>
        <button class="hilfebtn" onclick={() => (hilfeOffen = true)} aria-label="Hilfe" title="Hilfe">
          <i class="fa-solid fa-circle-question" aria-hidden="true"></i>
        </button>
      </div>
    </div>
  </aside>

  <div class="haupt">
    <header class="topbar">
      <div class="ort">
        <span class="btitel">{boardgebunden ? (aktivesBoard?.titel ?? 'Pinnwand') : (aktuelleAnsichtMeta?.titel ?? 'Pinnwand')}</span>
        {#if boardgebunden && aktiveMappe}<span class="krumen">{aktiveMappe.titel}{#if aktivesBoard?.kuerzel} &middot; {aktivesBoard.kuerzel}{/if}</span>{/if}
      </div>
    </header>

    <main class="buehne">
      {#if fehler}
        <p class="hinweis">Backend nicht erreichbar ({fehler}). Läuft das Backend auf Port 8420?</p>
      {:else if aktuelleKomponente && (!boardgebunden || aktivesBoard)}
        {@const Ansicht = aktuelleKomponente}
        <Ansicht boardId={aktivesBoard?.id ?? ''} />
      {:else}
        <p class="hinweis">Lädt ...</p>
      {/if}
    </main>
  </div>
</div>
</div>

<Toast />
{#if hilfeOffen}<Hilfe onSchliessen={() => (hilfeOffen = false)} />{/if}
{#if onboardingOffen}<Onboarding onFertig={onboardingFertig} onGeheZu={geheZuAnsicht} />{/if}

<style>
  .wurzel {
    display: flex;
    flex-direction: column;
    height: 100%;
  }
  .app {
    display: flex;
    flex: 1;
    min-height: 0;
    background: var(--surface-page);
  }
  .rail {
    flex: 0 0 232px;
    background: var(--surface-col);
    border-right: 1px solid var(--border);
    padding: 14px 11px;
    display: flex;
    flex-direction: column;
    gap: 2px;
    overflow-y: auto;
  }
  .marke {
    font-family: var(--font-display);
    font-size: 16px;
    font-weight: 600;
    color: var(--text-1);
    display: flex;
    align-items: center;
    gap: 9px;
    padding: 4px 8px 14px;
  }
  .marke .logo {
    width: 22px;
    height: 22px;
    border-radius: 6px;
    display: block;
    flex: none;
  }
  .marke .name {
    display: flex;
    align-items: baseline;
    gap: 8px;
  }
  .railtog {
    margin-left: auto;
    border: none;
    background: transparent;
    color: var(--text-3);
    width: 26px;
    height: 26px;
    border-radius: var(--r-s);
    font-size: 12px;
    flex: none;
  }
  .railtog:hover {
    color: var(--hl-primary-text);
    background: var(--surface-3);
  }
  .rail.zu {
    flex-basis: 58px;
  }
  .rail.zu .rubrik,
  .rail.zu .marke .name,
  .rail.zu .add,
  .rail.zu .menu span,
  .rail.zu .bname span,
  .rail.zu .aktionen,
  .rail.zu .thema span {
    display: none;
  }
  .rail.zu .marke {
    justify-content: center;
  }
  .rail.zu :global(.dienste) {
    display: none;
  }
  .rail.zu .menu,
  .rail.zu .bname,
  .rail.zu .thema {
    justify-content: center;
  }
  .rubrik {
    font-family: var(--font-display);
    font-size: 10.5px;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: var(--text-3);
    margin: 13px 8px 5px;
  }
  nav {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }
  .zeile {
    display: flex;
    align-items: center;
    border-radius: var(--r-m);
  }
  .menu,
  .bname {
    display: flex;
    align-items: center;
    gap: 10px;
    border: none;
    background: transparent;
    color: var(--text-2);
    font-size: 13px;
    text-align: left;
    padding: 8px 9px;
    width: 100%;
    min-width: 0;
  }
  .menu {
    border-radius: var(--r-m);
  }
  .bname span,
  .menu span {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .menu:hover {
    background: var(--surface-3);
    color: var(--text-1);
  }
  .menu.aktiv {
    background: var(--hl-primary-weich);
    color: var(--hl-primary-text);
  }
  .board {
    flex: 1;
  }
  .board.aktiv {
    background: var(--hl-primary-weich);
  }
  .board.aktiv .bname {
    color: var(--hl-primary-text);
  }
  .bname {
    flex: 1;
  }
  .aktionen {
    display: flex;
    gap: 1px;
    padding-right: 4px;
    opacity: 0;
    transition: opacity 0.12s;
  }
  .board:hover .aktionen,
  .board:focus-within .aktionen {
    opacity: 1;
  }
  .ic {
    border: none;
    background: transparent;
    color: var(--text-3);
    width: 24px;
    height: 24px;
    border-radius: var(--r-s);
    font-size: 11px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .ic:hover {
    background: var(--surface-1);
    color: var(--hl-primary-text);
  }
  .add {
    display: flex;
    align-items: center;
    gap: 9px;
    border: 1px dashed var(--border-2);
    background: transparent;
    color: var(--text-3);
    font-size: 13px;
    padding: 7px 9px;
    border-radius: var(--r-m);
    margin-top: 3px;
  }
  .add:hover {
    color: var(--hl-primary-text);
    border-color: var(--hl-primary);
  }
  .feld {
    width: 100%;
    border: 1px solid var(--border-2);
    background: var(--surface-1);
    color: var(--text-1);
    border-radius: var(--r-m);
    padding: 8px 9px;
    font-size: 13px;
  }
  .confirm {
    display: flex;
    flex-direction: column;
    gap: 7px;
    padding: 8px 9px;
    font-size: 12px;
    color: var(--text-2);
  }
  .reihe {
    display: flex;
    gap: 7px;
  }
  .mini {
    border: 1px solid var(--border);
    border-radius: var(--r-s);
    padding: 5px 10px;
    font-size: 12px;
  }
  .mini.geist {
    background: transparent;
    color: var(--text-2);
  }
  .mini.gefahr {
    background: var(--gefahr);
    color: #fff;
    border-color: transparent;
    font-weight: 500;
  }
  .fussbereich {
    margin-top: auto;
    display: flex;
    flex-direction: column;
  }
  .fzeile {
    display: flex;
    gap: 6px;
  }
  .fzeile .thema {
    flex: 1;
  }
  .hilfebtn {
    flex: none;
    width: 38px;
    border: 1px solid var(--border);
    background: var(--surface-2);
    color: var(--text-2);
    border-radius: var(--r-m);
    font-size: 14px;
  }
  .hilfebtn:hover {
    color: var(--hl-primary-text);
    border-color: var(--hl-primary);
  }
  .rail.zu .fzeile {
    flex-direction: column;
  }
  .thema {
    display: flex;
    align-items: center;
    gap: 10px;
    border: 1px solid var(--border);
    background: var(--surface-2);
    color: var(--text-2);
    font-size: 13px;
    padding: 9px 11px;
    border-radius: var(--r-m);
  }
  .thema:hover {
    color: var(--text-1);
    border-color: var(--border-2);
  }
  .haupt {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
  }
  .topbar {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 10px 16px;
    background: var(--surface-col);
    border-bottom: 1px solid var(--border);
  }
  .ort {
    display: flex;
    flex-direction: column;
    min-width: 0;
  }
  .btitel {
    font-family: var(--font-display);
    font-size: 15px;
    font-weight: 600;
    color: var(--text-1);
  }
  .krumen {
    font-size: 11px;
    color: var(--text-3);
  }
  .buehne {
    flex: 1;
    min-height: 0;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }
  .ver {
    font-family: var(--font-mono);
    font-size: 10px;
    color: var(--text-3);
    font-weight: 400;
  }
  .hinweis {
    color: var(--text-2);
    padding: 24px;
  }
</style>
