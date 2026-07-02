<script lang="ts">
  import { onMount } from 'svelte'
  import type { Component } from 'svelte'
  import type { Board, Projektmappe, Person } from './lib/types'
  import { ladeMappen, ladeBoards, ladeErweiterungen, erstelleBoard, benenneBoard, loescheBoard, erstelleMappe, benenneMappe, loescheMappe, serienVorbuchenAlle, ladeLabels, ladePersonen, ladeAuthStatus, abmelden } from './lib/api'
  import { setzeLabelDefinitionen } from './lib/labels'
  import { personSicht, setzePersonSicht } from './lib/personSicht.svelte'
  import { aktiveRolle as leiteRolleAb, eigenesKuerzel } from './lib/identitaet'
  import { auth } from './lib/auth.svelte'
  import Login from './lib/Login.svelte'
  import { ansichten, komponenteFuer } from './lib/module/registry'
  import { theme, wechsleTheme } from './lib/theme/theme.svelte'
  import { VERSION } from './lib/version'
  import { leseText, schreibeText, leseJson, schreibeJson } from './lib/uiSpeicher'
  import { ymd } from './lib/zeit'
  import { aktualisiereLaufend, timer } from './lib/timer.svelte'
  import { ladeKanbanKonfig } from './lib/kanbanKonfig.svelte'
  import { nav, transkriptNav, kartenZeiger, oeffneKarte } from './lib/navigation.svelte'
  import Toast from './lib/Toast.svelte'
  import KopfSuche from './lib/KopfSuche.svelte'
  import LaufBar from './lib/LaufBar.svelte'
  import StundenLeiste from './lib/StundenLeiste.svelte'
  import DiensteStatus from './lib/DiensteStatus.svelte'
  import Hilfe from './lib/Hilfe.svelte'
  import Onboarding from './lib/Onboarding.svelte'
  import DokumentVerwaltung from './lib/DokumentVerwaltung.svelte'
  import VorleseLeiste from './lib/VorleseLeiste.svelte'
  import BestaetigungsOverlay from './lib/module/termine/BestaetigungsOverlay.svelte'
  import SerienErinnerung from './lib/SerienErinnerung.svelte'
  import LoginTor from './lib/LoginTor.svelte'
  import PersonWahl from './lib/PersonWahl.svelte'
  import MappenMitglieder from './lib/MappenMitglieder.svelte'

  interface Ansicht {
    id: string
    titel: string
    icon: string
    komponente: Component<{ boardId: string }>
    reihenfolge: number
    global: boolean
    adminOnly: boolean
  }

  // UI-Zustand im Browser merken (Sidebar, aktive Ansicht, letztes Board).
  const _ui = leseJson<{ rail?: boolean; railBreite?: number; ansicht?: string; board?: string | null }>('pw_ui', {})
  function _merkeUi(): void {
    schreibeJson('pw_ui', { rail: railEin, railBreite, ansicht: aktiveAnsicht, board: aktivesBoard?.id ?? null })
  }

  // Startpfad frühzeitig sichern (bevor Effekte die URL anfassen können).
  const _startPfad = typeof window !== 'undefined' ? window.location.pathname : '/'
  let routingBereit = $state(false)

  // Hilfe + Einrichtungs-Assistent.
  let hilfeOffen = $state(false)
  let mappeDokOffen = $state(false)
  let onboardingOffen = $state(leseText('pw_onboarding_done') !== '1')
  function onboardingFertig(): void {
    onboardingOffen = false
    schreibeText('pw_onboarding_done', '1')
  }
  function geheZuAnsicht(id: string): void {
    if (ansichtsListe.some((a) => a.id === id)) aktiveAnsicht = id
  }

  let mappen = $state<Projektmappe[]>([])
  let aktiveMappe = $state<Projektmappe | null>(null)
  let mitgliederMappe = $state<Projektmappe | null>(null)  // offene Mitglieder-Verwaltung
  let boards = $state<Board[]>([])
  let aktivesBoard = $state<Board | null>(null)
  let boardsGeladen = $state(false)
  let fehler = $state<string | null>(null)

  let ansichtsListe = $state<Ansicht[]>([])
  let aktiveAnsicht = $state('')

  // Rollen-Gating (Phase 1, ohne Passwort = reines UI-Scoping): Mitarbeiter sehen die
  // verwaltenden Bereiche nicht. Rolle leitet sich aus der aktiven Person ab; ohne
  // gewaehlte Person gilt 'admin' (Bestand/frische Installation bleibt voll sichtbar).
  let personen = $state<Person[]>([])
  // Gating und Reihenfolge kommen aus den Modul-Manifesten (adminOnly/global/
  // reihenfolge) - keine Hartlisten mehr, die neue Module vergessen koennten.
  // Bei aktivem Login ist die Rolle serverseitig bestimmt (autoritativ), sonst aus
  // der gewaehlten Person abgeleitet (Phase-1-Verhalten).
  const aktiveRolle = $derived(leiteRolleAb(auth, personen, personSicht.id))
  // Timer je Person: der Timer-Store braucht das Kuerzel der aktiven Identitaet
  // fuer den laufend-Abgleich mit dem Server.
  $effect(() => {
    timer.kuerzel = eigenesKuerzel(auth, personen, personSicht.id)
  })
  const istAdmin = $derived(aktiveRolle === 'admin')
  const sichtbareAnsichten = $derived(
    aktiveRolle === 'mitarbeiter' ? ansichtsListe.filter((a) => !a.adminOnly) : ansichtsListe,
  )
  // Komponente nur aus den sichtbaren Ansichten - so rendert ein Mitarbeiter nie den
  // Inhalt eines gesperrten Bereichs (auch nicht kurz vor dem Fallback).
  const aktuelleKomponente = $derived(sichtbareAnsichten.find((a) => a.id === aktiveAnsicht)?.komponente)
  // Faellt die aktive Ansicht fuer einen Mitarbeiter weg (z.B. gespeicherte Admin-Ansicht
  // oder Personenwechsel), still auf die erste sichtbare Ansicht zurueckfallen.
  $effect(() => {
    if (aktiveAnsicht && sichtbareAnsichten.length && !sichtbareAnsichten.some((a) => a.id === aktiveAnsicht)) {
      aktiveAnsicht = sichtbareAnsichten[0].id
    }
  })

  // Globale Ansichten brauchen keine Board-Navigation; boardgebundene schon.
  const boardgebunden = $derived(!(ansichtsListe.find((a) => a.id === aktiveAnsicht)?.global ?? false))
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

  // Wunsch, ein verknuepftes Transkript zu oeffnen: zur Transkripte-Ansicht wechseln
  // (die Ansicht liest den Wunsch selbst aus und oeffnet das Transkript).
  $effect(() => {
    if (transkriptNav.id && ansichtsListe.some((a) => a.id === 'transkripte')) {
      aktiveAnsicht = 'transkripte'
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
  // Sidebar-Breite frei einstellbar (Ziehgriff) und dauerhaft gemerkt.
  const RAIL_MIN = 200
  const RAIL_MAX = 480
  let railBreite = $state(Math.max(RAIL_MIN, Math.min(RAIL_MAX, _ui.railBreite ?? 264)))
  let zieht = $state(false)
  function resizeStart(e: MouseEvent): void {
    e.preventDefault()
    zieht = true
    const move = (ev: MouseEvent) => {
      railBreite = Math.max(RAIL_MIN, Math.min(RAIL_MAX, Math.round(ev.clientX)))
    }
    const stop = () => {
      zieht = false
      window.removeEventListener('mousemove', move)
      window.removeEventListener('mouseup', stop)
      _merkeUi()
    }
    window.addEventListener('mousemove', move)
    window.addEventListener('mouseup', stop)
  }

  // Änderungen am UI-Zustand merken.
  $effect(() => {
    void railEin
    void railBreite
    void aktiveAnsicht
    void aktivesBoard
    _merkeUi()
  })

  // Routing ohne Hashes: echte Pfade /ansicht bzw. /ansicht/boardId.
  function pfadAusZustand(): string {
    if (!aktiveAnsicht) return '/'
    if (!boardgebunden || !aktivesBoard) return `/${aktiveAnsicht}`
    const k = kartenZeiger.offen
    const kartenTeil = k && k.boardId === aktivesBoard.id ? `/${encodeURIComponent(k.schluessel)}` : ''
    return `/${aktiveAnsicht}/${aktivesBoard.id}${kartenTeil}`
  }
  function wendePfadAn(pfad: string): void {
    const [ans, bId, kSchluessel] = pfad.split('/').filter(Boolean)
    if (ans && ansichtsListe.some((a) => a.id === ans)) aktiveAnsicht = ans
    if (bId) {
      const b = boards.find((x) => x.id === bId)
      if (b) aktivesBoard = b
      // Deep-Link auf eine Karte: das Board oeffnet sie anhand des Schluessels.
      if (kSchluessel) oeffneKarte(bId, undefined, decodeURIComponent(kSchluessel))
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
    if (aktiveMappe) {
      boardsGeladen = false
      boards = await ladeBoards(aktiveMappe.id)
      boardsGeladen = true
    }
  }
  async function erstesBoardAnlegen() {
    if (!aktiveMappe) return
    const neu = await erstelleBoard(aktiveMappe.id, 'Aufgaben')
    await ladeBoardListe()
    aktivesBoard = boards.find((b) => b.id === neu.id) ?? aktivesBoard
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
    // Dialog auch bei Server-Ablehnung schliessen (Meldung kommt zentral als Toast).
    try {
      await loescheMappe(id)
    } finally {
      loescheMappeId = null
    }
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
    try {
      await loescheBoard(id)
    } finally {
      loescheBoardId = null
    }
    await ladeBoardListe()
    if (aktivesBoard?.id === id) aktivesBoard = boards[0] ?? null
  }

  async function ladeAnsichten() {
    try {
      const erw = await ladeErweiterungen()
      ansichtsListe = erw.views
        .map((v) => {
          const k = komponenteFuer(v.wert.id)
          if (!k) return null
          // Sortierung/Gating kommen aus dem Modul-Manifest; Fallbacks fuer
          // Altbestand ohne die neuen Felder.
          return {
            id: v.wert.id,
            titel: v.wert.titel,
            icon: v.wert.icon,
            komponente: k,
            reihenfolge: v.wert.reihenfolge ?? 99,
            global: v.wert.global ?? false,
            adminOnly: v.wert.adminOnly ?? false,
          }
        })
        .filter((a): a is Ansicht => a !== null)
    } catch {
      // Offline-Notweg ohne Manifest-Metadaten: neutrale Defaults.
      ansichtsListe = ansichten().map((a) => ({
        id: a.id, titel: a.titel, icon: a.icon, komponente: a.komponente,
        reihenfolge: 99, global: false, adminOnly: false,
      }))
    }
    ansichtsListe.sort((a, b) => a.reihenfolge - b.reihenfolge)
    const gespeichert = _ui.ansicht
    aktiveAnsicht = gespeichert && ansichtsListe.some((a) => a.id === gespeichert)
      ? gespeichert
      : ansichtsListe[0]?.id ?? ''
  }

  // Wiederkehrende Aufgaben einmal pro Tag vorbuchen, damit genau die heute
  // faelligen Karten entstehen (bei vorlauf 0 ohne Neustart, kein Voraus-Stapel).
  async function serienTagesabgleich(): Promise<void> {
    const heute = ymd(new Date())  // lokales Datum (UTC verschiebt nach Mitternacht)
    if (leseText('pw_serien_check') === heute) return
    try {
      await serienVorbuchenAlle()
      schreibeText('pw_serien_check', heute)
    } catch {
      /* Vorbuchung ist unkritisch */
    }
  }

  // Zugewiesene Label-Farben einmal beim Start in die Farbquelle (labels.ts) spiegeln,
  // damit Karten-Chips überall die in der Verwaltung gewählte Farbe zeigen.
  async function ladeLabelFarben(): Promise<void> {
    try {
      setzeLabelDefinitionen(await ladeLabels())
    } catch {
      /* Label-Farben sind optional; Fallback bleibt die automatische Farbe */
    }
  }

  async function abmeldenUndNeu(): Promise<void> {
    await abmelden()
    location.reload()
  }

  onMount(async () => {
    // Zuerst den Anmeldestatus klaeren. Ist Anmeldung erforderlich und niemand
    // angemeldet, zeigt sich die Login-Sperre und der Rest der App laedt nicht.
    await ladeAuthStatus()
    if (auth.erforderlich && !auth.angemeldet) return
    // Bei aktivem Login ist die eigene Person die aktive Sicht.
    if (auth.erforderlich && auth.personId) setzePersonSicht(auth.personId)
    await ladeAnsichten()
    ladeLabelFarben()
    ladePersonen().then((p) => (personen = p)).catch(() => {}) // fuer das Rollen-Gating
    aktualisiereLaufend()
    void ladeKanbanKonfig()
    serienTagesabgleich()
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
<StundenLeiste />
<div class="app">
  <aside class="rail" class:zu={!railEin} style={railEin ? `flex-basis:${railBreite}px` : ''}>
    <div class="marke">
      <img class="logo" src="/favicon.svg" alt="" />
      <span class="name">Pinnwand <span class="ver">v{VERSION}</span></span>
      <button class="railtog" aria-label="Seitenleiste ein- oder ausklappen" onclick={() => (railEin = !railEin)}>
        <i class="fa-solid {railEin ? 'fa-angles-left' : 'fa-angles-right'}" aria-hidden="true"></i>
      </button>
    </div>

    <p class="rubrik">Ansichten</p>
    <nav>
      {#each sichtbareAnsichten as a (a.id)}
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
          <div class="zeile board mappe" class:aktiv={aktiveMappe?.id === m.id}>
            <button class="bname" onclick={() => waehleMappe(m)} title={m.titel}>
              <i class="fa-solid {aktiveMappe?.id === m.id ? 'fa-folder-open' : 'fa-folder'}" aria-hidden="true"></i><span>{m.titel}</span>
            </button>
            <div class="aktionen">
              <!-- Mitglieder-Pflege auch fuer Mitglieder der Mappe (Server prueft). -->
              <button class="ic" aria-label="Projekt-Mitglieder" title="Wer sieht dieses Projekt" onclick={() => (mitgliederMappe = m)}><i class="fa-solid fa-users" aria-hidden="true"></i></button>
              <button class="ic" aria-label="Mappe umbenennen" onclick={() => { bearbeiteMappeId = m.id; mappeEntwurf = m.titel }}><i class="fa-solid fa-pen" aria-hidden="true"></i></button>
              {#if mappen.length > 1}
                <button class="ic" aria-label="Mappe löschen" onclick={() => (loescheMappeId = m.id)}><i class="fa-solid fa-trash" aria-hidden="true"></i></button>
              {/if}
            </div>
          </div>

          {#if aktiveMappe?.id === m.id}
            <!-- Unterbaum: Boards + Dokumente dieser Mappe, eingerueckt fuer klare Hierarchie -->
            <div class="unterbaum">
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
                    <button class="bname" onclick={() => (aktivesBoard = b)} title={b.titel}>
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
              <button class="add dokbtn" onclick={() => (mappeDokOffen = true)} title="Dokumente dieser Mappe"><i class="fa-solid fa-folder-open" aria-hidden="true"></i> Dokumente</button>
            </div>
          {/if}
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
    {/if}

    <div class="fussbereich">
      {#if auth.angemeldet}
        <button class="abmelden" onclick={abmeldenUndNeu} title="Abmelden">
          <i class="fa-solid fa-right-from-bracket" aria-hidden="true"></i>
          <span>{auth.kuerzel ?? auth.name} abmelden</span>
        </button>
      {/if}
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
  {#if railEin}
    <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
    <div class="resizer" class:zieht role="separator" aria-label="Seitenleiste breiter oder schmaler ziehen" onmousedown={resizeStart}></div>
  {/if}

  <div class="haupt">
    <header class="topbar">
      <div class="ort">
        <span class="btitel">{boardgebunden ? (aktivesBoard?.titel ?? 'Pinnwand') : (aktuelleAnsichtMeta?.titel ?? 'Pinnwand')}</span>
        {#if boardgebunden && aktiveMappe}<span class="krumen">{aktiveMappe.titel}{#if aktivesBoard?.kuerzel} &middot; {aktivesBoard.kuerzel}{/if}</span>{/if}
      </div>
      <div class="kopfsuche"><KopfSuche onSuche={() => geheZuAnsicht('suche')} /></div>
    </header>

    <main class="buehne">
      {#if fehler}
        <p class="hinweis">Backend nicht erreichbar ({fehler}). Läuft das Backend auf Port 8420?</p>
      {:else if aktuelleKomponente && (!boardgebunden || aktivesBoard)}
        {@const Ansicht = aktuelleKomponente}
        <Ansicht boardId={aktivesBoard?.id ?? ''} />
      {:else if boardgebunden && aktiveMappe && boardsGeladen && boards.length === 0}
        <div class="leer">
          <i class="fa-solid fa-table-columns" aria-hidden="true"></i>
          <h2>Noch kein Board in "{aktiveMappe.titel}"</h2>
          <p>Lege ein Board an, um Aufgaben in Spalten zu planen.</p>
          <button class="cta" onclick={erstesBoardAnlegen}>
            <i class="fa-solid fa-plus" aria-hidden="true"></i> Board anlegen
          </button>
        </div>
      {:else}
        <p class="hinweis">Lädt ...</p>
      {/if}
    </main>
  </div>
</div>
</div>

<Toast />
<VorleseLeiste />
<BestaetigungsOverlay />
<SerienErinnerung />
<LoginTor />
<Login />
{#if !auth.erforderlich}<PersonWahl />{/if}

{#if mitgliederMappe}
  <MappenMitglieder mappeId={mitgliederMappe.id} titel={mitgliederMappe.titel} {personen} onSchliessen={() => (mitgliederMappe = null)} />
{/if}
{#if hilfeOffen}<Hilfe onSchliessen={() => (hilfeOffen = false)} />{/if}
{#if onboardingOffen}<Onboarding onFertig={onboardingFertig} onGeheZu={geheZuAnsicht} />{/if}
{#if mappeDokOffen && aktiveMappe}
  <div class="dokback" role="presentation" onclick={() => (mappeDokOffen = false)}></div>
  <aside class="dokdrawer" aria-label="Mappen-Dokumente">
    <header class="dokkopf">
      <i class="fa-solid fa-folder-open" aria-hidden="true"></i>
      <span class="dtit">Dokumente &middot; {aktiveMappe.titel}</span>
      <button class="dokx" aria-label="Schließen" onclick={() => (mappeDokOffen = false)}><i class="fa-solid fa-xmark" aria-hidden="true"></i></button>
    </header>
    <div class="dokbody">
      <DokumentVerwaltung kontext="mappe" kontextId={aktiveMappe.id} />
    </div>
  </aside>
{/if}

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
    flex: 0 0 264px;
    background: var(--surface-col);
    padding: 14px 11px;
    display: flex;
    flex-direction: column;
    gap: 2px;
    overflow-y: auto;
  }
  .resizer {
    flex: 0 0 5px;
    border-right: 1px solid var(--border);
    cursor: col-resize;
    background: transparent;
    transition: background 0.12s, border-color 0.12s;
  }
  .resizer:hover,
  .resizer.zieht {
    background: var(--hl-primary-weich);
    border-right-color: var(--hl-primary);
  }
  /* Boards + Dokumente eingerueckt unter der aktiven Mappe (klare Hierarchie). */
  .unterbaum {
    display: flex;
    flex-direction: column;
    gap: 2px;
    margin: 2px 0 8px 16px;
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
    border-right: 1px solid var(--border);
  }
  .rail.zu .rubrik,
  .rail.zu .marke .name,
  .rail.zu .add,
  .rail.zu .menu span,
  .rail.zu .bname span,
  .rail.zu .aktionen,
  .rail.zu .unterbaum,
  .rail.zu .thema span {
    display: none;
  }
  .rail.zu .marke {
    flex-direction: column;
    justify-content: center;
    gap: 8px;
    padding: 4px 0 12px;
  }
  .rail.zu .railtog {
    margin-left: 0;
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
  .abmelden {
    display: flex;
    align-items: center;
    gap: 8px;
    width: 100%;
    border: 1px solid var(--border);
    background: var(--surface-2);
    color: var(--text-2);
    border-radius: var(--r-m);
    padding: 7px 10px;
    font-size: 12px;
    margin-bottom: 8px;
    overflow: hidden;
    white-space: nowrap;
  }
  .abmelden:hover { background: var(--surface-3); color: var(--text-1); }
  .rail.zu .abmelden span { display: none; }
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
  .kopfsuche {
    margin-left: auto;
    flex: 0 1 460px;
    display: flex;
    justify-content: flex-end;
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
  .leer {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 10px;
    text-align: center;
    padding: 32px;
    color: var(--text-2);
  }
  .leer > i {
    font-size: 34px;
    color: var(--text-3);
    margin-bottom: 4px;
  }
  .leer h2 {
    font-family: var(--font-display);
    font-size: 17px;
    font-weight: 600;
    color: var(--text-1);
    margin: 0;
  }
  .leer p {
    margin: 0;
    font-size: 13px;
    color: var(--text-3);
  }
  .cta {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    margin-top: 8px;
    border: none;
    border-radius: var(--r-m);
    background: var(--hl-primary);
    color: var(--hl-on-primary);
    font-size: 13px;
    font-weight: 600;
    padding: 9px 16px;
    cursor: pointer;
  }
  .cta:hover {
    filter: brightness(1.08);
  }
  .dokbtn {
    width: 100%;
    margin-top: 3px;
    justify-content: flex-start;
  }
  .dokback {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.45);
    z-index: 40;
  }
  .dokdrawer {
    position: fixed;
    top: 0;
    right: 0;
    bottom: 0;
    width: 560px;
    max-width: 94vw;
    z-index: 41;
    background: var(--surface-col);
    border-left: 1px solid var(--border-2);
    box-shadow: var(--schatten-pop);
    display: flex;
    flex-direction: column;
  }
  .dokkopf {
    display: flex;
    align-items: center;
    gap: 9px;
    padding: 12px 14px;
    border-bottom: 1px solid var(--border);
    color: var(--text-2);
  }
  .dokkopf .dtit {
    font-family: var(--font-display);
    font-weight: 600;
    color: var(--text-1);
    font-size: 14px;
  }
  .dokx {
    margin-left: auto;
    width: 28px;
    height: 28px;
    border-radius: var(--r-s);
    border: 1px solid var(--border);
    background: var(--surface-2);
    color: var(--text-2);
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .dokx:hover {
    color: var(--text-1);
  }
  .dokbody {
    padding: 14px;
    overflow-y: auto;
  }
</style>
