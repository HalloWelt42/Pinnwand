<script lang="ts">
  import { dndzone, dragHandleZone, SHADOW_PLACEHOLDER_ITEM_ID } from 'svelte-dnd-action'
  import { flip } from 'svelte/animate'
  import { untrack } from 'svelte'
  import type { BoardDetail, Karte, Prioritaet, Spalte } from '../../types'
  import {
    ladeBoard,
    ladeFertige,
    ladeKarte,
    verschiebeKarte,
    erstelleKarte,
    aktualisiereKarte,
    karteVerknuepfen,
    anhaengenKommentar,
    loescheKarte,
    erstelleSpalte,
    aktualisiereSpalte,
    verschiebeSpalte,
    loescheSpalte,
    setzeErledigtSpalte,
    setzeSpaltenReihenfolge,
    ladePersonen,
    type KarteAenderung,
    type Person,
  } from '../../api'
  import { zeigeToast } from '../../toaster.svelte'
  import { timer } from '../../timer.svelte'
  import { nav, setzeOffeneKarte } from '../../navigation.svelte'
  import { neuKarteAus } from '../../restore'
  import { personSicht } from '../../personSicht.svelte'
  import { zuletztKuerzel } from '../../zuletztKuerzel.svelte'
  import { leseJson, schreibeJson } from '../../uiSpeicher'
  import Column from './Column.svelte'
  import Toolbar from './Toolbar.svelte'
  import CardDrawer from './CardDrawer.svelte'
  import Archiv from './Archiv.svelte'

  let { boardId }: { boardId: string } = $props()

  interface Eintrag {
    id: string
    spalte: Spalte
    karten: Karte[]
  }

  let board = $state<BoardDetail | null>(null)
  let ansicht = $state<Eintrag[]>([])
  let ausgewaehlt = $state<Karte | null>(null)
  let eingeklappt = $state<Set<string>>(new Set())
  let personen = $state<Person[]>([])
  // Zeitraum-Filter je erledigter Spalte (Schluessel = Spalten-ID, Wert = Zeitraum).
  let fertigFilter = $state<Record<string, string>>({})

  // Gefensterte Fertig-Karten je Erledigt-Spalte: geladene Seite + Nachlade-Info.
  // board.karten enthaelt KEINE Erledigt-Karten mehr (das Backend liefert sie gefenstert).
  interface FertigDaten {
    karten: Karte[]
    gesamt: number
    hatMehr: boolean
    laden: boolean
  }
  let fertigDaten = $state<Record<string, FertigDaten>>({})
  let archivOffen = $state(false)

  let suche = $state('')
  let sortModus = $state<'manuell' | 'faellig' | 'prioritaet'>('manuell')
  let filterPrio = $state<Prioritaet | null>(null)
  let filterLabels = $state<string[]>([])

  let neueSpalte = $state(false)
  let spalteTitel = $state('')
  let zuletztGezogen = 0

  const AKZENTE = ['#4f9be8', '#ffb300', '#a5d6a7', '#b39ddb', '#f48fb1', '#80cbc4', '#ff8a65', '#9fa8da']
  const PRIO_RANG: Record<string, number> = { hoch: 0, mittel: 1, niedrig: 2 }

  const kartenDragAus = $derived(suche !== '' || filterLabels.length > 0 || filterPrio !== null || sortModus !== 'manuell')
  const alleLabels = $derived([...new Set((board?.karten ?? []).flatMap((k) => k.labels))].sort())
  const mitglieder = $derived([...new Set((board?.karten ?? []).map((k) => k.zustaendig).filter((z): z is string => !!z))])
  // Default-Zustaendiger fuer neue Karten: aktive Identitaet, sonst zuletzt genutztes Kuerzel.
  const aktivKuerzel = $derived(personSicht.id ? (personen.find((p) => p.id === personSicht.id)?.kuerzel ?? null) : null)
  const standardKuerzel = $derived(aktivKuerzel ?? (zuletztKuerzel.wert || null))

  // Aus der Suche/Deep-Link angesteuerte Karte öffnen, sobald dieses Board geladen ist
  // (über interne ID oder über den Karten-Schlüssel aus der URL).
  $effect(() => {
    const ziel = nav.ziel
    if (ziel && ziel.boardId === boardId && board) {
      const k = ziel.karteId
        ? findeKarte(ziel.karteId)
        : ziel.schluessel
          ? [board, ...Object.values(fertigDaten).map((d) => ({ karten: d.karten }))]
              .flatMap((q) => q.karten)
              .find((x) => x.schluessel === ziel.schluessel)
          : undefined
      if (k) {
        ausgewaehlt = k
        nav.ziel = { boardId }
      } else if (ziel.karteId) {
        // Deep-Link auf eine fertige Karte, die (noch) nicht gefenstert geladen ist:
        // die Karte einzeln nachladen und oeffnen.
        const zid = ziel.karteId
        ladeKarte(zid).then((karte) => {
          if (nav.ziel?.karteId === zid) { ausgewaehlt = karte; nav.ziel = { boardId } }
        }).catch(() => zeigeToast('Karte konnte nicht geladen werden.'))
      }
    }
  })

  // Offene Karte für tief verlinkbare URLs spiegeln; beim Verlassen wieder abräumen.
  $effect(() => {
    setzeOffeneKarte(ausgewaehlt ? boardId : null, ausgewaehlt?.schluessel ?? null)
    return () => setzeOffeneKarte(null)
  })

  function baueAnsicht() {
    if (!board) return
    ansicht = board.spalten.map((s) => ({
      id: s.id,
      spalte: s,
      // Erledigt-Spalten kommen gefenstert aus fertigDaten; offene Spalten aus board.karten.
      karten: s.erledigt
        ? (fertigDaten[s.id]?.karten ?? [])
        : board!.karten.filter((k) => k.spalte === s.id).sort((a, b) => a.reihenfolge - b.reihenfolge),
    }))
  }

  // Ladeparameter einer Erledigt-Spalte: bei aktiver Suche/Sortierung greift die
  // serverseitige Suche (Zeitfenster ausgesetzt), sonst der Zeitfilter der Spalte.
  function fertigParams(spalteId: string): { zeitraum?: string; q?: string; labels?: string[]; prioritaet?: string | null } {
    if (kartenDragAus) {
      return { q: suche || undefined, labels: filterLabels, prioritaet: filterPrio }
    }
    return { zeitraum: fertigFilter[spalteId] ?? 'heute' }
  }

  // Generationszaehler je Spalte: eine spaetere Anfrage (z.B. Zeitfilter-Wechsel oder
  // Board-Wechsel) ueberholt eine noch laufende; deren Ergebnis wird dann verworfen.
  const fertigGen: Record<string, number> = {}
  async function ladeFertigSpalte(spalteId: string, reset = true): Promise<void> {
    const vorher = fertigDaten[spalteId]
    // Nachladen (Anhaengen) nicht doppelt starten; ein Reset (Filterwechsel) hat aber
    // immer Vorrang und darf eine laufende Anfrage ueberholen.
    if (!reset && vorher?.laden) return
    const gen = (fertigGen[spalteId] = (fertigGen[spalteId] ?? 0) + 1)
    const meinBoard = boardId
    const offset = reset ? 0 : (vorher?.karten.length ?? 0)
    fertigDaten = { ...fertigDaten, [spalteId]: { karten: vorher?.karten ?? [], gesamt: vorher?.gesamt ?? 0, hatMehr: vorher?.hatMehr ?? false, laden: true } }
    try {
      const seite = await ladeFertige(spalteId, { ...fertigParams(spalteId), offset })
      if (fertigGen[spalteId] !== gen || boardId !== meinBoard) return  // ueberholt / Board gewechselt -> verwerfen
      const bestehend = reset ? [] : (vorher?.karten ?? [])
      // Dubletten vermeiden (falls sich zwischen zwei Seiten etwas verschoben hat).
      const bekannt = new Set(bestehend.map((k) => k.id))
      const neu = seite.karten.filter((k) => !bekannt.has(k.id))
      fertigDaten = { ...fertigDaten, [spalteId]: { karten: [...bestehend, ...neu], gesamt: seite.gesamt, hatMehr: seite.hat_mehr, laden: false } }
    } catch {
      if (fertigGen[spalteId] === gen && boardId === meinBoard) {
        fertigDaten = { ...fertigDaten, [spalteId]: { karten: vorher?.karten ?? [], gesamt: vorher?.gesamt ?? 0, hatMehr: vorher?.hatMehr ?? false, laden: false } }
      }
    }
    baueAnsicht()
  }

  async function ladeAlleFertig(): Promise<void> {
    const spalten = (board?.spalten ?? []).filter((s) => s.erledigt)
    await Promise.all(spalten.map((s) => ladeFertigSpalte(s.id, true)))
  }

  // Karte ueber offene UND gefensterte Fertig-Spalten finden.
  function findeKarte(id: string): Karte | undefined {
    const offen = board?.karten.find((k) => k.id === id)
    if (offen) return offen
    for (const d of Object.values(fertigDaten)) {
      const k = d.karten.find((x) => x.id === id)
      if (k) return k
    }
    return undefined
  }

  async function laden() {
    board = await ladeBoard(boardId)
    baueAnsicht()
    await ladeAlleFertig()
    // Offene Detailansicht auf den frischen Stand spiegeln (Timer-Start/Pause/Stopp, erfasste Zeit).
    if (ausgewaehlt) ausgewaehlt = findeKarte(ausgewaehlt.id) ?? ausgewaehlt
  }

  // Spalten-/Filterzustand je Board im Browser merken.
  function _ladeBoardUi(id: string): { suche?: string; sortModus?: typeof sortModus; filterPrio?: Prioritaet | null; filterLabels?: string[]; eingeklappt?: string[]; fertigFilter?: Record<string, string> } {
    return leseJson('pw_board_' + id, {})
  }
  function _merkeBoardUi(): void {
    schreibeJson('pw_board_' + boardId, {
      suche, sortModus, filterPrio, filterLabels, eingeklappt: Array.from(eingeklappt), fertigFilter,
    })
  }

  $effect(() => {
    void boardId
    const s = _ladeBoardUi(boardId)
    suche = s.suche ?? ''
    sortModus = s.sortModus ?? 'manuell'
    filterPrio = s.filterPrio ?? null
    filterLabels = s.filterLabels ?? []
    ausgewaehlt = null
    eingeklappt = new Set(s.eingeklappt ?? [])
    fertigFilter = s.fertigFilter ?? {}
    fertigDaten = {}  // Board-Wechsel: gefensterte Fertig-Daten des alten Boards verwerfen
    laden()
  })

  $effect(() => {
    void suche
    void sortModus
    void filterPrio
    void filterLabels
    void eingeklappt
    void fertigFilter
    _merkeBoardUi()
  })

  // Aendert sich Suche/Label/Prio/Sortierung, aendern sich die Server-Parameter der
  // Fertig-Spalten -> erste Seite serverseitig neu laden (entprellt gegen Tippen).
  let refetchTimer: ReturnType<typeof setTimeout> | null = null
  $effect(() => {
    void suche
    void filterLabels
    void filterPrio
    void sortModus
    if (!untrack(() => board)) return
    if (refetchTimer) clearTimeout(refetchTimer)
    refetchTimer = setTimeout(() => ladeAlleFertig(), 250)
  })

  // Timer-Änderungen (Start/Pause irgendwo) -> Board neu laden, damit der Lauf-Status stimmt.
  let letzterStand = 0
  $effect(() => {
    if (timer.stand !== letzterStand) {
      letzterStand = timer.stand
      laden()
    }
  })

  // Personen laden (fuer den Default-Zustaendigen neuer Karten); bei Board-Wechsel
  // auffrischen, damit neu angelegte Personen ohne App-Neustart auftauchen.
  $effect(() => {
    void boardId
    ladePersonen().then((p) => (personen = p)).catch(() => {})
  })

  function volltext(k: Karte): string {
    return [
      k.titel,
      k.schluessel,
      k.beschreibung,
      k.zustaendig,
      k.prioritaet,
      ...k.labels,
      ...k.checkliste.map((c) => c.text),
      ...k.kommentare.flatMap((c) => [c.text, c.autor]),
    ]
      .filter(Boolean)
      .join(' \n ')
      .toLowerCase()
  }

  function passt(k: Karte): boolean {
    if (filterPrio && k.prioritaet !== filterPrio) return false
    if (filterLabels.length && !filterLabels.some((l) => k.labels.includes(l))) return false
    const q = suche.trim().toLowerCase()
    if (q) {
      // Tiefensuche über alle Inhalte; jedes Wort muss vorkommen (Wort- und Satzsuche).
      const text = volltext(k)
      if (!q.split(/\s+/).every((w) => text.includes(w))) return false
    }
    return true
  }

  function anzeige(eintrag: Eintrag): Karte[] {
    // Erledigt-Spalten sind bereits serverseitig gefiltert/gefenstert (inkl. Suche).
    if (eintrag.spalte.erledigt) return eintrag.karten
    // Offene Spalten: Suche/Sortierung clientseitig ueber die voll geladenen Karten.
    if (kartenDragAus) {
      let liste = eintrag.karten.filter(passt)
      if (sortModus === 'faellig') {
        liste = [...liste].sort((a, b) => (a.faellig ?? '9999').localeCompare(b.faellig ?? '9999'))
      } else if (sortModus === 'prioritaet') {
        liste = [...liste].sort((a, b) => (PRIO_RANG[a.prioritaet ?? 'z'] ?? 9) - (PRIO_RANG[b.prioritaet ?? 'z'] ?? 9))
      }
      return liste
    }
    return eintrag.karten
  }

  function setzeFertigFilter(spalteId: string, zeitraum: string): void {
    fertigFilter = { ...fertigFilter, [spalteId]: zeitraum }
    ladeFertigSpalte(spalteId, true)  // neuer Zeitraum -> erste Seite serverseitig neu laden
  }

  function toggleEinklappen(id: string) {
    const s = new Set(eingeklappt)
    s.has(id) ? s.delete(id) : s.add(id)
    eingeklappt = s
  }

  // -- Karten-Drag --
  function cardsConsider(idx: number, items: Karte[]) {
    ansicht[idx].karten = items
    zuletztGezogen = Date.now()
  }
  function cardsFinalize(idx: number, items: Karte[], info: { id: string }) {
    ansicht[idx].karten = items
    const eintrag = ansicht[idx]
    const spalteId = eintrag.spalte.id
    const pos = items.findIndex((k) => k.id === info.id)
    if (pos >= 0) {
      const wechsel = items[pos].spalte !== spalteId
      items[pos].spalte = spalteId
      // WIP-Durchsetzung (weiche Warnung): schiebt ein Spaltenwechsel die Zielspalte
      // ueber ihr WIP-Limit, deutlich darauf hinweisen (Karte bleibt, kein harter Block).
      if (wechsel) {
        const sp = eintrag.spalte
        const n = items.filter((k) => k.id !== SHADOW_PLACEHOLDER_ITEM_ID).length
        if (sp.wip_limit != null && n > sp.wip_limit) {
          zeigeToast(`Spalte "${sp.titel}" ist über dem WIP-Limit (${n}/${sp.wip_limit}).`)
        }
      }
      // Erledigt-Spalten sind nach Abschlussdatum sortiert (nicht manuell) und nur
      // gefenstert geladen; darum wird die Karte dort ans Ende gehaengt (Datum ordnet neu)
      // und die betroffene(n) Fertig-Spalte(n) frisch nachgeladen.
      const zielPos = eintrag.spalte.erledigt ? 1_000_000 : pos
      verschiebeKarte(info.id, spalteId, zielPos)
        .then(() => {
          if (wechsel) {
            laden()  // Spaltenwechsel: offene Spalten + alle Fertig-Spalten auffrischen
          } else if (eintrag.spalte.erledigt) {
            ladeFertigSpalte(spalteId, true)  // Umsortieren in einer Fertig-Spalte
          }
        })
        .catch(() => laden())
    }
    zuletztGezogen = Date.now()
  }

  // -- Spalten-Drag --
  // Spalten werden ueber den Griff (dragHandle in Column) gezogen; die Zone ist immer
  // aktiv und faengt Karten-Zuege nicht ab, weil sie nur ueber einen Griff startet.
  function spaltenConsider(items: Eintrag[]) {
    ansicht = items
  }
  function spaltenFinalize(items: Eintrag[]) {
    ansicht = items
    const ids = items.filter((e) => e.id !== SHADOW_PLACEHOLDER_ITEM_ID).map((e) => e.spalte.id)
    setzeSpaltenReihenfolge(boardId, ids).catch(() => laden())
  }

  // -- Karte öffnen / bearbeiten --
  function oeffnen(id: string) {
    if (Date.now() - zuletztGezogen < 160) return
    ausgewaehlt = findeKarte(id) ?? null
  }
  function ersetzeKarte(k: Karte) {
    if (!board) return
    // Karte kann in einer offenen Spalte (board.karten) ODER einer gefensterten
    // Fertig-Spalte (fertigDaten) liegen - an beiden Stellen aktualisieren.
    board.karten = board.karten.map((x) => (x.id === k.id ? k : x))
    for (const [sid, d] of Object.entries(fertigDaten)) {
      if (d.karten.some((x) => x.id === k.id)) {
        fertigDaten = { ...fertigDaten, [sid]: { ...d, karten: d.karten.map((x) => (x.id === k.id ? k : x)) } }
      }
    }
    baueAnsicht()
    if (ausgewaehlt?.id === k.id) ausgewaehlt = k
  }
  async function karteAendern(daten: KarteAenderung) {
    if (!ausgewaehlt) return
    ersetzeKarte(await aktualisiereKarte(ausgewaehlt.id, daten))
  }
  async function karteKommentar(text: string) {
    if (!ausgewaehlt) return
    ersetzeKarte(await anhaengenKommentar(ausgewaehlt.id, ausgewaehlt.zustaendig ?? 'Ich', text))
  }
  async function loescheKarteMitUndo(k: Karte) {
    const snap = $state.snapshot(k) as Karte
    const spalteId = snap.spalte
    if (ausgewaehlt?.id === snap.id) ausgewaehlt = null
    await loescheKarte(snap.id)
    await laden()
    zeigeToast(`Karte "${snap.titel}" gelöscht`, async () => {
      await neuKarteAus(boardId, spalteId, snap)
      await laden()
    })
  }
  function karteLoeschen() {
    if (ausgewaehlt) loescheKarteMitUndo(ausgewaehlt)
  }
  function karteSchnellLoeschen(id: string) {
    const k = findeKarte(id)
    if (k) loescheKarteMitUndo(k)
  }

  // -- Anlegen / Spaltenpflege --
  async function karteAnlegen(spalteId: string, titel: string, typ: 'arbeit' | 'idee' = 'arbeit') {
    await erstelleKarte({ board_id: boardId, spalte: spalteId, titel, zustaendig: standardKuerzel, typ })
    await laden()
  }
  // Zeit-Verknuepfung per Drag-and-Drop (Kette auf eine andere Karte gezogen).
  async function verknuepfeKarten(quelleId: string, zielId: string) {
    await karteVerknuepfen(quelleId, zielId)
    await laden()
    zeigeToast('Aufgaben verknüpft - Zeit wird geteilt')
  }
  async function spalteAnlegen() {
    const t = spalteTitel.trim()
    if (!t) return
    await erstelleSpalte(boardId, t)
    spalteTitel = ''
    neueSpalte = false
    await laden()
  }
  async function spalteUmbenennen(id: string, daten: { titel: string; wip_limit: number | null }) {
    await aktualisiereSpalte(id, daten)
    await laden()
  }
  async function spalteVerschieben(id: string, richtung: -1 | 1) {
    await verschiebeSpalte(id, richtung)
    await laden()
  }
  async function spalteErledigt(id: string) {
    await setzeErledigtSpalte(id)
    await laden()
  }
  async function spalteLoeschen(id: string) {
    const eintrag = ansicht.find((e) => e.spalte.id === id)
    if (!eintrag) return
    const snap = {
      titel: eintrag.spalte.titel,
      wip: eintrag.spalte.wip_limit ?? null,
      karten: eintrag.karten.filter((k) => k.id !== SHADOW_PLACEHOLDER_ITEM_ID).map((k) => $state.snapshot(k) as Karte),
    }
    try {
      await loescheSpalte(id)
    } catch {
      /* letzte Spalte geschützt */
    }
    await laden()
    zeigeToast(`Spalte "${snap.titel}" gelöscht`, async () => {
      const sp = await erstelleSpalte(boardId, snap.titel, snap.wip)
      for (const k of snap.karten) await neuKarteAus(boardId, sp.id, k)
      await laden()
    })
  }
</script>

{#if board}
  <Toolbar bind:suche bind:sortModus bind:filterPrio bind:filterLabels {alleLabels} {mitglieder} reorderPausiert={kartenDragAus} />

  <div class="flaeche">
    <div
      class="spalten"
      use:dragHandleZone={{ items: ansicht, type: 'spalte', flipDurationMs: 160, dropTargetStyle: {} }}
      onconsider={(e) => spaltenConsider(e.detail.items)}
      onfinalize={(e) => spaltenFinalize(e.detail.items)}
    >
      {#each ansicht as eintrag, idx (eintrag.id)}
        <div class="wrap" animate:flip={{ duration: 160 }}>
          {#if eintrag.id === SHADOW_PLACEHOLDER_ITEM_ID}
            <div class="spalten-ph"></div>
          {:else}
            <Column
              spalte={eintrag.spalte}
              karten={anzeige(eintrag)}
              dragDisabled={kartenDragAus}
              zeitfilter={fertigFilter[eintrag.spalte.id] ?? 'heute'}
              onZeitfilter={(z) => setzeFertigFilter(eintrag.spalte.id, z)}
              akzent={AKZENTE[idx % AKZENTE.length]}
              eingeklappt={eingeklappt.has(eintrag.spalte.id)}
              istErste={idx === 0}
              istLetzte={idx === ansicht.length - 1}
              einzige={ansicht.length <= 1}
              onCardsConsider={(items) => cardsConsider(idx, items)}
              onCardsFinalize={(items, info) => cardsFinalize(idx, items, info)}
              onOeffnen={oeffnen}
              onLoeschenKarte={karteSchnellLoeschen}
              onVerknuepfen={verknuepfeKarten}
              onKarteAnlegen={(titel, typ) => karteAnlegen(eintrag.spalte.id, titel, typ)}
              onToggleEinklappen={() => toggleEinklappen(eintrag.spalte.id)}
              onSpalteUmbenennen={(daten) => spalteUmbenennen(eintrag.spalte.id, daten)}
              onSpalteVerschieben={(richtung) => spalteVerschieben(eintrag.spalte.id, richtung)}
              onSpalteLoeschen={() => spalteLoeschen(eintrag.spalte.id)}
              onSpalteErledigt={() => spalteErledigt(eintrag.spalte.id)}
              fertigMehr={eintrag.spalte.erledigt ? (fertigDaten[eintrag.spalte.id]?.hatMehr ?? false) : false}
              fertigLaden={fertigDaten[eintrag.spalte.id]?.laden ?? false}
              fertigGesamt={eintrag.spalte.erledigt ? (fertigDaten[eintrag.spalte.id]?.gesamt ?? 0) : 0}
              onNachladen={() => ladeFertigSpalte(eintrag.spalte.id, false)}
            />
          {/if}
        </div>
      {/each}
    </div>

    <div class="add-col">
      {#if neueSpalte}
        <!-- svelte-ignore a11y_autofocus -->
        <input class="feld" placeholder="Spaltentitel" bind:value={spalteTitel} aria-label="Neue Spalte" autofocus
          onkeydown={(e) => { if (e.key === 'Enter') spalteAnlegen(); if (e.key === 'Escape') { neueSpalte = false; spalteTitel = '' } }} />
        <div class="reihe">
          <button class="btn primaer" onclick={spalteAnlegen}>Hinzufügen</button>
          <button class="btn geist" onclick={() => { neueSpalte = false; spalteTitel = '' }}>Abbrechen</button>
        </div>
      {:else}
        <button class="add-btn" onclick={() => (neueSpalte = true)}><i class="fa-solid fa-plus" aria-hidden="true"></i> Spalte</button>
        <button class="add-btn archiv" onclick={() => (archivOffen = true)} title="Archivierte fertige Karten"><i class="fa-solid fa-box-archive" aria-hidden="true"></i> Archiv</button>
      {/if}
    </div>
  </div>

  {#if archivOffen && board}
    <Archiv
      {boardId}
      titel={board.titel}
      onSchliessen={() => (archivOffen = false)}
      onOeffneKarte={(k) => { ausgewaehlt = k; archivOffen = false }}
    />
  {/if}

  {#if ausgewaehlt}
    <CardDrawer
      karte={ausgewaehlt}
      spalten={board.spalten}
      boardKarten={board.karten}
      onSchliessen={() => (ausgewaehlt = null)}
      onAendern={karteAendern}
      onKommentar={karteKommentar}
      onLoeschen={karteLoeschen}
      onReload={laden}
      onOeffneKarte={oeffnen}
    />
  {/if}
{/if}

<style>
  .flaeche {
    flex: 1;
    min-height: 0;
    display: flex;
    align-items: stretch;
    gap: 12px;
    padding: 14px;
    overflow-x: auto;
    overflow-y: hidden;
  }
  .spalten {
    display: flex;
    align-items: stretch;
    gap: 12px;
    height: 100%;
  }
  .wrap {
    height: 100%;
    display: flex;
  }
  .spalten-ph {
    width: 286px;
    height: 100%;
    flex: none;
    border: 2px dashed var(--hl-primary);
    background: var(--hl-primary-weich);
    border-radius: var(--r-xl);
  }
  /* Gezogene Spalte deutlich anheben - klares Feedback, dass das Ziehen laeuft. */
  :global(#dnd-action-dragged-el .col) {
    box-shadow: var(--schatten-lift);
    outline: 2px solid var(--hl-primary);
    outline-offset: -2px;
    cursor: grabbing;
  }
  :global(#dnd-action-dragged-el .zu) {
    box-shadow: var(--schatten-lift);
    outline: 2px solid var(--hl-primary);
    outline-offset: -2px;
  }
  /* Gezogene Karte: nur anheben (Schatten folgt dem runden Rahmen), KEIN eckiges Outline. */
  :global(#dnd-action-dragged-el .card) {
    box-shadow: var(--schatten-lift);
    cursor: grabbing;
  }
  /* svelte-dnd-action fokussiert das schwebende Klon-Element - der (blaue, eckige)
     Fokusrahmen um die abgehobene Karte ist hier unerwuenscht; der Lift-Schatten genuegt.
     Der ID-Selektor schlaegt die globale :focus-visible-Regel ueber die Spezifitaet
     (kein !important noetig); Autor-outline:none unterdrueckt auch den UA-Fokusring.
     Wrapper zusaetzlich abrunden, falls ein Browser doch einen Rahmen zeichnet. */
  :global(#dnd-action-dragged-el) {
    border-radius: var(--r-l);
    outline: none;
  }
  .add-col {
    flex: 0 0 270px;
  }
  .add-btn {
    width: 100%;
    border: 1px dashed var(--border-2);
    background: transparent;
    color: var(--text-3);
    border-radius: var(--r-xl);
    padding: 11px;
    font-family: var(--font-display);
    font-size: 13px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 7px;
  }
  .add-btn:hover {
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
    margin-bottom: 7px;
  }
  .reihe {
    display: flex;
    gap: 7px;
  }
  .btn {
    border: 1px solid var(--border);
    border-radius: var(--r-m);
    padding: 6px 12px;
    font-size: 12.5px;
  }
  .btn.primaer {
    background: var(--hl-primary);
    color: var(--hl-on-primary);
    border-color: transparent;
    font-weight: 500;
  }
  .btn.geist {
    background: transparent;
    color: var(--text-2);
  }
</style>
