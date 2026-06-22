<script lang="ts">
  import { dndzone, SHADOW_PLACEHOLDER_ITEM_ID } from 'svelte-dnd-action'
  import { flip } from 'svelte/animate'
  import type { BoardDetail, Karte, Prioritaet, Spalte } from '../../types'
  import {
    ladeBoard,
    verschiebeKarte,
    erstelleKarte,
    aktualisiereKarte,
    anhaengenKommentar,
    setzeErfasst,
    loescheKarte,
    erstelleSpalte,
    aktualisiereSpalte,
    verschiebeSpalte,
    loescheSpalte,
    setzeSpaltenReihenfolge,
    type KarteAenderung,
  } from '../../api'
  import { zeigeToast } from '../../toaster.svelte'
  import { timer } from '../../timer.svelte'
  import { nav, setzeOffeneKarte } from '../../navigation.svelte'
  import { neuKarteAus } from '../../restore'
  import Column from './Column.svelte'
  import Toolbar from './Toolbar.svelte'
  import CardDrawer from './CardDrawer.svelte'

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

  let suche = $state('')
  let sortModus = $state<'manuell' | 'faellig' | 'prioritaet'>('manuell')
  let filterPrio = $state<Prioritaet | null>(null)
  let filterLabels = $state<string[]>([])

  let spaltenDragAus = $state(true)
  let neueSpalte = $state(false)
  let spalteTitel = $state('')
  let zuletztGezogen = 0

  const AKZENTE = ['#4f9be8', '#ffb300', '#a5d6a7', '#b39ddb', '#f48fb1', '#80cbc4', '#ff8a65', '#9fa8da']
  const PRIO_RANG: Record<string, number> = { hoch: 0, mittel: 1, niedrig: 2 }

  const kartenDragAus = $derived(suche !== '' || filterLabels.length > 0 || filterPrio !== null || sortModus !== 'manuell')
  const alleLabels = $derived([...new Set((board?.karten ?? []).flatMap((k) => k.labels))].sort())
  const mitglieder = $derived([...new Set((board?.karten ?? []).map((k) => k.zustaendig).filter((z): z is string => !!z))])

  // Aus der Suche/Deep-Link angesteuerte Karte öffnen, sobald dieses Board geladen ist
  // (über interne ID oder über den Karten-Schlüssel aus der URL).
  $effect(() => {
    const ziel = nav.ziel
    if (ziel && ziel.boardId === boardId && board) {
      const k = ziel.karteId
        ? board.karten.find((x) => x.id === ziel.karteId)
        : ziel.schluessel
          ? board.karten.find((x) => x.schluessel === ziel.schluessel)
          : null
      if (k) {
        ausgewaehlt = k
        nav.ziel = { boardId }
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
      karten: board!.karten.filter((k) => k.spalte === s.id).sort((a, b) => a.reihenfolge - b.reihenfolge),
    }))
  }

  async function laden() {
    board = await ladeBoard(boardId)
    baueAnsicht()
    // Offene Detailansicht auf den frischen Stand spiegeln (Timer-Start/Pause/Stopp, erfasste Zeit).
    if (ausgewaehlt) ausgewaehlt = board?.karten.find((k) => k.id === ausgewaehlt!.id) ?? ausgewaehlt
  }

  // Spalten-/Filterzustand je Board im Browser merken.
  function _ladeBoardUi(id: string): { suche?: string; sortModus?: typeof sortModus; filterPrio?: Prioritaet | null; filterLabels?: string[]; eingeklappt?: string[] } {
    try {
      return JSON.parse(localStorage.getItem('pw_board_' + id) || '{}')
    } catch {
      return {}
    }
  }
  function _merkeBoardUi(): void {
    try {
      localStorage.setItem('pw_board_' + boardId, JSON.stringify({
        suche, sortModus, filterPrio, filterLabels, eingeklappt: Array.from(eingeklappt),
      }))
    } catch {
      /* localStorage nicht verfügbar */
    }
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
    laden()
  })

  $effect(() => {
    void suche
    void sortModus
    void filterPrio
    void filterLabels
    void eingeklappt
    _merkeBoardUi()
  })

  // Timer-Änderungen (Start/Pause irgendwo) -> Board neu laden, damit der Lauf-Status stimmt.
  let letzterStand = 0
  $effect(() => {
    if (timer.stand !== letzterStand) {
      letzterStand = timer.stand
      laden()
    }
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
    if (!kartenDragAus) return eintrag.karten
    let liste = eintrag.karten.filter(passt)
    if (sortModus === 'faellig') {
      liste = [...liste].sort((a, b) => (a.faellig ?? '9999').localeCompare(b.faellig ?? '9999'))
    } else if (sortModus === 'prioritaet') {
      liste = [...liste].sort((a, b) => (PRIO_RANG[a.prioritaet ?? 'z'] ?? 9) - (PRIO_RANG[b.prioritaet ?? 'z'] ?? 9))
    }
    return liste
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
    const spalteId = ansicht[idx].spalte.id
    const pos = items.findIndex((k) => k.id === info.id)
    if (pos >= 0) {
      items[pos].spalte = spalteId
      verschiebeKarte(info.id, spalteId, pos).catch(() => laden())
    }
    zuletztGezogen = Date.now()
  }

  // -- Spalten-Drag --
  function spaltenConsider(items: Eintrag[]) {
    ansicht = items
  }
  function spaltenFinalize(items: Eintrag[]) {
    ansicht = items
    spaltenDragAus = true
    const ids = items.filter((e) => e.id !== SHADOW_PLACEHOLDER_ITEM_ID).map((e) => e.spalte.id)
    setzeSpaltenReihenfolge(boardId, ids).catch(() => laden())
  }

  // -- Karte öffnen / bearbeiten --
  function oeffnen(id: string) {
    if (Date.now() - zuletztGezogen < 160) return
    ausgewaehlt = board?.karten.find((k) => k.id === id) ?? null
  }
  function ersetzeKarte(k: Karte) {
    if (!board) return
    board.karten = board.karten.map((x) => (x.id === k.id ? k : x))
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
  async function karteErfasst(sekunden: number) {
    if (!ausgewaehlt) return
    ersetzeKarte(await setzeErfasst(ausgewaehlt.id, sekunden))
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
    const k = board?.karten.find((x) => x.id === id)
    if (k) loescheKarteMitUndo(k)
  }

  // -- Anlegen / Spaltenpflege --
  async function karteAnlegen(spalteId: string, titel: string) {
    await erstelleKarte({ board_id: boardId, spalte: spalteId, titel })
    await laden()
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
      use:dndzone={{ items: ansicht, type: 'spalte', dragDisabled: spaltenDragAus, flipDurationMs: 160, dropTargetStyle: {} }}
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
              akzent={AKZENTE[idx % AKZENTE.length]}
              eingeklappt={eingeklappt.has(eintrag.spalte.id)}
              istErste={idx === 0}
              istLetzte={idx === ansicht.length - 1}
              einzige={ansicht.length <= 1}
              onCardsConsider={(items) => cardsConsider(idx, items)}
              onCardsFinalize={(items, info) => cardsFinalize(idx, items, info)}
              onOeffnen={oeffnen}
              onLoeschenKarte={karteSchnellLoeschen}
              onKarteAnlegen={(titel) => karteAnlegen(eintrag.spalte.id, titel)}
              onGriffDown={() => (spaltenDragAus = false)}
              onToggleEinklappen={() => toggleEinklappen(eintrag.spalte.id)}
              onSpalteUmbenennen={(daten) => spalteUmbenennen(eintrag.spalte.id, daten)}
              onSpalteVerschieben={(richtung) => spalteVerschieben(eintrag.spalte.id, richtung)}
              onSpalteLoeschen={() => spalteLoeschen(eintrag.spalte.id)}
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
      {/if}
    </div>
  </div>

  {#if ausgewaehlt}
    <CardDrawer
      karte={ausgewaehlt}
      spalten={board.spalten}
      onSchliessen={() => (ausgewaehlt = null)}
      onAendern={karteAendern}
      onKommentar={karteKommentar}
      onErfasst={karteErfasst}
      onLoeschen={karteLoeschen}
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
