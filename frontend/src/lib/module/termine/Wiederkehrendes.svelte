<script lang="ts">
  import { onMount } from 'svelte'
  import Serien from '../serien/Serien.svelte'
  import Termine from './Termine.svelte'
  import { ladeMappen, ladeBoards } from '../../api'
  import type { Projektmappe, Board } from '../../types'
  import { leseText, schreibeText } from '../../uiSpeicher'

  // Globale Ansicht: die boardId-Prop der Ansichts-Schnittstelle wird hier nicht
  // gebraucht (das Board fuer den Aufgaben-Modus waehlt man unten selbst).
  let { boardId: _ignoriert = '' }: { boardId?: string } = $props()
  $effect(() => void _ignoriert)

  // Eine Ansicht fuer alles Wiederkehrende. Der Modus bestimmt das Ergebnis:
  // "aufgabe" -> Board-Karte mit Soll (Serie), "termin" -> Meeting mit Folgetag-
  // Bestaetigung (Termin). Die bestehenden Komponenten werden wiederverwendet.
  let modus = $state<'aufgabe' | 'termin'>('aufgabe')
  const _modus = leseText('pw_wk_modus')
  if (_modus === 'aufgabe' || _modus === 'termin') modus = _modus
  function setzeModus(m: 'aufgabe' | 'termin'): void {
    modus = m
    schreibeText('pw_wk_modus', m)
  }

  let mappen = $state<Projektmappe[]>([])
  let boards = $state<Board[]>([])
  let mappeId = $state('')
  let boardId = $state('')

  onMount(async () => {
    try {
      mappen = await ladeMappen()
      if (mappen[0]) {
        mappeId = mappen[0].id
        boards = await ladeBoards(mappeId)
        boardId = boards[0]?.id ?? ''
      }
    } catch { /* Board-Auswahl bleibt leer */ }
  })
  async function waehleMappe(id: string): Promise<void> {
    mappeId = id
    boards = await ladeBoards(id)
    boardId = boards[0]?.id ?? ''
  }
</script>

<div class="wk">
  <div class="kopf">
    <h2>Wiederkehrendes</h2>
    <div class="seg">
      <button class:an={modus === 'aufgabe'} onclick={() => setzeModus('aufgabe')}>
        <i class="fa-solid fa-table-columns" aria-hidden="true"></i> Aufgaben-Serie
      </button>
      <button class:an={modus === 'termin'} onclick={() => setzeModus('termin')}>
        <i class="fa-solid fa-calendar-check" aria-hidden="true"></i> Termin / Meeting
      </button>
    </div>
  </div>

  <p class="hinweis"><i class="fa-solid fa-circle-info" aria-hidden="true"></i> Ein Thema entweder als Aufgabe ODER als Termin führen - nicht beides. Sonst wird die Zeit in den Auswertungen doppelt gezählt.</p>

  {#if modus === 'aufgabe'}
    <p class="erkl">Wiederkehrende Aufgabe als Board-Karte (mit Soll und Timer). Wird auf dem gewählten Board vorgebucht.</p>
    <div class="boardwahl">
      <span class="lbl">Board</span>
      <select bind:value={mappeId} onchange={(e) => waehleMappe(e.currentTarget.value)} aria-label="Mappe">
        {#each mappen as m (m.id)}<option value={m.id}>{m.titel}</option>{/each}
      </select>
      <select bind:value={boardId} aria-label="Board">
        {#each boards as b (b.id)}<option value={b.id}>{b.titel}</option>{/each}
      </select>
    </div>
    {#if boardId}
      {#key boardId}<Serien {boardId} />{/key}
    {:else}
      <p class="erkl">Lege zuerst ein Board an, um Aufgaben-Serien zu nutzen.</p>
    {/if}
  {:else}
    <p class="erkl">Wiederkehrendes Meeting ohne Board-Karte. Schreibt nach Bestätigung am Folgetag Zeit gut.</p>
    <Termine boardId="" />
  {/if}
</div>

<style>
  .wk { height: 100%; overflow-y: auto; }
  .kopf { display: flex; align-items: center; justify-content: space-between; gap: 14px; flex-wrap: wrap; padding: 16px 16px 0; }
  .kopf h2 { margin: 0; font-family: var(--font-display); font-size: 17px; color: var(--text-1); }
  .seg { display: inline-flex; border: 1px solid var(--border); border-radius: var(--r-m); overflow: hidden; }
  .seg button {
    border: none; background: var(--surface-2); color: var(--text-2);
    padding: 8px 14px; font-size: 12.5px; display: inline-flex; align-items: center; gap: 7px;
  }
  .seg button + button { border-left: 1px solid var(--border); }
  .seg button:hover { color: var(--text-1); }
  .seg button.an { background: var(--hl-primary); color: var(--hl-on-primary); }
  .erkl { color: var(--text-3); font-size: 12.5px; margin: 12px 16px 0; }
  .hinweis { color: var(--text-2); font-size: 12px; margin: 10px 16px 0; display: flex; align-items: center; gap: 7px; }
  .hinweis i { color: var(--hl-primary-text); }
  .boardwahl { display: flex; align-items: center; gap: 8px; padding: 10px 16px 0; }
  .boardwahl .lbl { color: var(--text-3); font-size: 12px; }
  .boardwahl select {
    border: 1px solid var(--border-2); background: var(--surface-2); color: var(--text-1);
    border-radius: var(--r-m); padding: 7px 9px; font-size: 12.5px;
  }
</style>
