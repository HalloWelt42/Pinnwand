<script lang="ts">
  import { onMount } from 'svelte'
  import type { Component } from 'svelte'
  import type { Board, Projektmappe, Person } from './lib/types'
  import { ladeMappen, ladeBoards, ladeErweiterungen, erstelleBoard, benenneBoard, loescheBoard, erstelleMappe, benenneMappe, loescheMappe, serienVorbuchenAlle, ladeLabels, ladePersonen, ladeAuthStatus } from './lib/api'
  import { setzeLabelDefinitionen } from './lib/labels'
  import { personSicht, setzePersonSicht } from './lib/personSicht.svelte'
  import { aktiveRolle as leiteRolleAb, eigenesKuerzel } from './lib/identitaet'
  import { auth } from './lib/auth.svelte'
  import Login from './lib/Login.svelte'
  import { ansichten, komponenteFuer } from './lib/module/registry'
  import { leseText, schreibeText, leseJson, schreibeJson } from './lib/uiSpeicher'
  import { ymd } from './lib/zeit'
  import { aktualisiereLaufend, timer } from './lib/timer.svelte'
  import { ladeKanbanKonfig } from './lib/kanbanKonfig.svelte'
  import { nav, transkriptNav } from './lib/navigation.svelte'
  import { startPfad, routing, pfadAusZustand, zerlegePfad, schreibePfad, beobachteStandort } from './lib/routing.svelte'
  import SeitenLeiste from './lib/SeitenLeiste.svelte'
  import Toast from './lib/Toast.svelte'
  import KopfSuche from './lib/KopfSuche.svelte'
  import LaufBar from './lib/LaufBar.svelte'
  import StundenLeiste from './lib/StundenLeiste.svelte'
  import Hilfe from './lib/Hilfe.svelte'
  import Glocke from './lib/Glocke.svelte'
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

  // Routing ohne Hashes (Details in lib/routing.svelte.ts): der Effekt spiegelt den
  // App-Zustand in den Pfad; wendePfadAn wendet einen Pfad (Start-Deep-Link,
  // Zurueck-Taste) auf den App-Zustand an.
  function wendePfadAn(pfad: string): void {
    const ziel = zerlegePfad(pfad)
    if (ziel.ansicht && ansichtsListe.some((a) => a.id === ziel.ansicht)) aktiveAnsicht = ziel.ansicht
    if (ziel.boardId) {
      const b = boards.find((x) => x.id === ziel.boardId)
      if (b) aktivesBoard = b
    }
  }
  $effect(() => {
    schreibePfad(pfadAusZustand(aktiveAnsicht, boardgebunden, aktivesBoard?.id ?? null))
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
  // Mappe aktivieren: Boards laden und das zuletzt genutzte (oder erste) Board waehlen.
  async function waehleMappe(m: Projektmappe): Promise<void> {
    aktiveMappe = m
    await ladeBoardListe()
    aktivesBoard = boards.find((b) => b.id === _ui.board) ?? boards[0] ?? null
  }
  // Legt die Mappe an und gibt sie zurueck; die Seitenleiste aktiviert sie danach.
  async function neueMappeErstellen(titel: string): Promise<Projektmappe> {
    const neu = await erstelleMappe(titel)
    mappen = await ladeMappen()
    return mappen.find((m) => m.id === neu.id) ?? neu
  }
  async function mappeUmbenennen(id: string, titel: string): Promise<void> {
    await benenneMappe(id, titel)
    mappen = await ladeMappen()
    if (aktiveMappe?.id === id) aktiveMappe = mappen.find((m) => m.id === id) ?? aktiveMappe
  }
  async function mappeLoeschenBestaetigt(id: string): Promise<void> {
    await loescheMappe(id)
    mappen = await ladeMappen()
    if (aktiveMappe?.id === id) {
      const ziel = mappen[0] ?? null
      if (ziel) await waehleMappe(ziel)
      else { aktiveMappe = null; boards = []; aktivesBoard = null }
    }
  }
  async function neuesBoardErstellen(titel: string): Promise<void> {
    if (!aktiveMappe) return
    const neu = await erstelleBoard(aktiveMappe.id, titel)
    await ladeBoardListe()
    aktivesBoard = boards.find((b) => b.id === neu.id) ?? aktivesBoard
  }
  async function boardUmbenennen(id: string, titel: string): Promise<void> {
    await benenneBoard(id, titel)
    await ladeBoardListe()
    if (aktivesBoard?.id === id) aktivesBoard = boards.find((b) => b.id === id) ?? aktivesBoard
  }
  async function boardLoeschenBestaetigt(id: string): Promise<void> {
    await loescheBoard(id)
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
    if (startPfad && startPfad !== '/') {
      wendePfadAn(startPfad)
    }
    routing.bereit = true
    beobachteStandort(wendePfadAn)
  })
</script>

<div class="wurzel">
<LaufBar />
<StundenLeiste />
<div class="app">
  <SeitenLeiste
    ansichten={sichtbareAnsichten}
    bind:aktiveAnsicht
    {boardgebunden}
    {mappen}
    {aktiveMappe}
    {boards}
    bind:aktivesBoard
    bind:railEin
    {railBreite}
    onWaehleMappe={waehleMappe}
    onMappeErstellen={neueMappeErstellen}
    onMappeUmbenennen={mappeUmbenennen}
    onMappeLoeschen={mappeLoeschenBestaetigt}
    onBoardErstellen={neuesBoardErstellen}
    onBoardUmbenennen={boardUmbenennen}
    onBoardLoeschen={boardLoeschenBestaetigt}
    onMitglieder={(m) => (mitgliederMappe = m)}
    onDokumente={() => (mappeDokOffen = true)}
    onHilfe={() => (hilfeOffen = true)}
  />
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
      <Glocke kuerzel={timer.kuerzel} />
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
