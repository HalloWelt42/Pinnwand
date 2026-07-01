<script lang="ts">
  import { ladeProjekte, ladeProjektDetail, aktualisiereMappe, ladePersonen } from '../../api'
  import type { ProjektAufwand, ProjektDetail, Person, ProjektStatus } from '../../types'
  import { formatStd } from '../../zeit'
  import { zeigeToast } from '../../toaster.svelte'

  let { boardId }: { boardId: string } = $props()
  $effect(() => void boardId)

  let projekte = $state<ProjektAufwand[]>([])
  let personen = $state<Person[]>([])
  let laedt = $state(true)
  let offenId = $state<string | null>(null)
  let detail = $state<ProjektDetail | null>(null)
  let bearbeiteId = $state<string | null>(null)

  // Entwurf beim Bearbeiten der Projektfelder (bis zum Speichern).
  let eOwner = $state('')
  let eBudgetStd = $state('')
  let eStatus = $state<ProjektStatus>('aktiv')

  const STATUS: { wert: ProjektStatus; text: string }[] = [
    { wert: 'aktiv', text: 'aktiv' },
    { wert: 'pausiert', text: 'pausiert' },
    { wert: 'abgeschlossen', text: 'abgeschlossen' },
  ]
  const statusText = (s: ProjektStatus): string => STATUS.find((x) => x.wert === s)?.text ?? s

  async function laden(): Promise<void> {
    laedt = true
    try {
      projekte = await ladeProjekte()
    } catch {
      projekte = []
    } finally {
      laedt = false
    }
  }
  $effect(() => { laden() })
  $effect(() => { ladePersonen().then((p) => (personen = p)).catch(() => {}) })

  // Bezug fuer den Balken: gibt es ein Budget, misst der Balken gegen das Budget,
  // sonst gegen das Soll (Summe der Schaetzungen). Ist/Soll/Budget bleiben getrennt.
  function bezugSek(p: ProjektAufwand): number {
    if (p.budget_min && p.budget_min > 0) return p.budget_min * 60
    return p.soll_minuten * 60
  }
  function prozent(p: ProjektAufwand): number {
    const b = bezugSek(p)
    return b > 0 ? Math.round((p.ist_sekunden / b) * 100) : 0
  }
  function restSek(p: ProjektAufwand): number | null {
    const b = bezugSek(p)
    return b > 0 ? b - p.ist_sekunden : null
  }

  async function aufklappen(p: ProjektAufwand): Promise<void> {
    if (offenId === p.mappe_id) { offenId = null; detail = null; return }
    offenId = p.mappe_id
    detail = null
    try {
      detail = await ladeProjektDetail(p.mappe_id)
    } catch {
      detail = null
    }
  }

  function bearbeiten(p: ProjektAufwand): void {
    bearbeiteId = p.mappe_id
    eOwner = p.owner ?? ''
    eBudgetStd = p.budget_min ? String(p.budget_min / 60) : ''
    eStatus = p.status
  }
  function abbrechen(): void {
    bearbeiteId = null
  }
  async function speichern(p: ProjektAufwand): Promise<void> {
    const std = parseFloat(eBudgetStd.replace(',', '.'))
    const budget_min = Number.isFinite(std) && std > 0 ? Math.round(std * 60) : null
    try {
      await aktualisiereMappe(p.mappe_id, { owner: eOwner || null, budget_min, status: eStatus })
      bearbeiteId = null
      await laden()
    } catch (e) {
      zeigeToast(e instanceof Error ? e.message : 'Projekt konnte nicht gespeichert werden.')
    }
  }

  const nameFuerKuerzel = (k?: string | null): string =>
    (k ? (personen.find((p) => p.kuerzel === k)?.name ?? k) : '-')
</script>

<div class="projekte">
  <p class="sec">Projekte - Aufwand (Ist / Soll / Budget)</p>
  {#if laedt}
    <p class="leer">Lädt ...</p>
  {:else if projekte.length === 0}
    <p class="leer">Noch keine Projekte. Jede Mappe ist ein Projekt - lege links eine an.</p>
  {:else}
    <div class="liste">
      {#each projekte as p (p.mappe_id)}
        {@const pz = prozent(p)}
        {@const rest = restSek(p)}
        <div class="karte" class:offen={offenId === p.mappe_id}>
          <div class="kopf">
            <button class="titel" onclick={() => aufklappen(p)} title="Aufschluesselung anzeigen">
              <i class="fa-solid fa-chevron-{offenId === p.mappe_id ? 'down' : 'right'}" aria-hidden="true"></i>
              <span class="tn">{p.titel}</span>
            </button>
            <span class="status s-{p.status}">{statusText(p.status)}</span>
            <span class="owner" title="Verantwortlich">{p.owner ? p.owner : '-'}</span>
            <button class="edit" aria-label="Projekt bearbeiten" onclick={() => bearbeiten(p)}><i class="fa-solid fa-pen" aria-hidden="true"></i></button>
          </div>

          <div class="werte">
            <span class="w"><span class="l">Ist</span> <b>{formatStd(p.ist_sekunden)}</b></span>
            <span class="w"><span class="l">Soll</span> <b>{p.soll_minuten ? formatStd(p.soll_minuten * 60) : '-'}</b></span>
            <span class="w"><span class="l">Budget</span> <b>{p.budget_min ? formatStd(p.budget_min * 60) : '-'}</b></span>
            {#if rest !== null}
              <span class="w"><span class="l">Rest</span> <b class:knapp={rest < 0}>{formatStd(Math.abs(rest))}{rest < 0 ? ' über' : ''}</b></span>
            {/if}
            <span class="w rechts"><span class="l">Karten</span> <b>{p.karten}</b></span>
          </div>

          <div class="balken" title="{pz}% verbraucht">
            <div class="fuell" class:voll={pz >= 100} style="width:{Math.min(100, pz)}%"></div>
          </div>

          {#if bearbeiteId === p.mappe_id}
            <div class="edit-zeile">
              <label class="ef">Verantwortlich
                <select bind:value={eOwner}>
                  <option value="">-</option>
                  {#each personen as pe (pe.id)}{#if pe.kuerzel}<option value={pe.kuerzel}>{pe.kuerzel} - {pe.name}</option>{/if}{/each}
                </select>
              </label>
              <label class="ef">Budget (Std.)
                <input type="number" min="0" step="0.5" bind:value={eBudgetStd} placeholder="-" />
              </label>
              <label class="ef">Status
                <select bind:value={eStatus}>
                  {#each STATUS as s (s.wert)}<option value={s.wert}>{s.text}</option>{/each}
                </select>
              </label>
              <div class="eaktion">
                <button class="btn geist" onclick={abbrechen}>Abbrechen</button>
                <button class="btn primaer" onclick={() => speichern(p)}>Speichern</button>
              </div>
            </div>
          {/if}

          {#if offenId === p.mappe_id}
            <div class="detail">
              {#if detail === null}
                <p class="leer">Lädt Aufschlüsselung ...</p>
              {:else}
                <p class="dsub">Phasen (Boards)</p>
                <div class="dtab">
                  {#each detail.boards as b (b.board_id)}
                    <div class="dzeile">
                      <span class="dn">{b.titel}</span>
                      <span class="dv">Ist {formatStd(b.ist_sekunden)}</span>
                      <span class="dv">Soll {b.soll_minuten ? formatStd(b.soll_minuten * 60) : '-'}</span>
                      <span class="dv rechts">{b.karten} Karten</span>
                    </div>
                  {/each}
                  {#if detail.boards.length === 0}<p class="leer">Keine Boards.</p>{/if}
                </div>
                {#if detail.personen.length}
                  <p class="dsub">Nach Person</p>
                  <div class="dtab">
                    {#each detail.personen as pp (pp.kuerzel ?? '?')}
                      <div class="dzeile">
                        <span class="dn">{nameFuerKuerzel(pp.kuerzel)}</span>
                        <span class="dv rechts">Ist {formatStd(pp.ist_sekunden)}</span>
                      </div>
                    {/each}
                  </div>
                {/if}
              {/if}
            </div>
          {/if}
        </div>
      {/each}
    </div>
  {/if}
</div>

<style>
  .projekte { height: 100%; overflow-y: auto; padding: 16px; max-width: 920px; }
  .sec { font-family: var(--font-display); font-size: 11px; letter-spacing: 0.04em; text-transform: uppercase; color: var(--text-3); margin: 0 0 12px; }
  .leer { color: var(--text-3); font-size: 13px; padding: 8px 2px; }
  .liste { display: flex; flex-direction: column; gap: 10px; }
  .karte { border: 1px solid var(--border); border-radius: var(--r-l); background: var(--surface-col); padding: 12px 14px; }
  .karte.offen { border-color: var(--border-2); }
  .kopf { display: flex; align-items: center; gap: 10px; }
  .titel { flex: 1; display: flex; align-items: center; gap: 8px; border: none; background: transparent; color: var(--text-1); font-size: 14px; font-weight: 600; text-align: left; cursor: pointer; padding: 0; min-width: 0; }
  .titel i { color: var(--text-3); font-size: 11px; width: 12px; }
  .tn { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .status { font-size: 10.5px; padding: 2px 9px; border-radius: 999px; background: var(--surface-3); color: var(--text-2); white-space: nowrap; }
  .status.s-aktiv { background: var(--ok-bg, color-mix(in srgb, var(--ok) 18%, transparent)); color: var(--ok, #2e7d32); }
  .status.s-pausiert { background: var(--surface-3); color: var(--text-3); }
  .status.s-abgeschlossen { background: color-mix(in srgb, var(--hl-primary) 16%, transparent); color: var(--hl-primary-text); }
  .owner { font-size: 11.5px; color: var(--text-3); font-variant-numeric: tabular-nums; min-width: 34px; text-align: right; }
  .edit { border: none; background: transparent; color: var(--text-3); cursor: pointer; font-size: 12px; padding: 4px 6px; }
  .edit:hover { color: var(--hl-primary-text); }
  .werte { display: flex; flex-wrap: wrap; align-items: baseline; gap: 16px; margin: 10px 0 8px; font-size: 12.5px; }
  .w { color: var(--text-2); display: inline-flex; align-items: baseline; gap: 6px; }
  .w.rechts { margin-left: auto; }
  .w .l { font-size: 10.5px; text-transform: uppercase; letter-spacing: 0.03em; color: var(--text-3); }
  .w b { font-family: var(--font-mono); color: var(--text-1); }
  .w b.knapp { color: var(--gefahr); }
  .balken { height: 7px; border-radius: 999px; background: var(--surface-3); overflow: hidden; }
  .fuell { height: 100%; background: var(--hl-primary); border-radius: 999px; transition: width 0.2s; }
  .fuell.voll { background: var(--gefahr); }
  .edit-zeile { display: flex; flex-wrap: wrap; align-items: flex-end; gap: 12px; margin-top: 12px; padding-top: 12px; border-top: 1px solid var(--border); }
  .ef { display: flex; flex-direction: column; gap: 4px; font-size: 11px; color: var(--text-3); }
  .ef select, .ef input { border: 1px solid var(--border-2); background: var(--surface-2); color: var(--text-1); border-radius: var(--r-s); padding: 6px 8px; font-size: 12.5px; }
  .ef input { width: 100px; }
  .eaktion { display: flex; gap: 8px; margin-left: auto; }
  .btn { border: 1px solid var(--border); background: var(--surface-2); color: var(--text-2); border-radius: var(--r-m); padding: 7px 12px; font-size: 12.5px; cursor: pointer; }
  .btn.primaer { background: var(--hl-primary); color: var(--hl-on-primary); border-color: transparent; font-weight: 500; }
  .btn.geist { background: transparent; }
  .detail { margin-top: 12px; padding-top: 10px; border-top: 1px solid var(--border); }
  .dsub { font-size: 10.5px; text-transform: uppercase; letter-spacing: 0.03em; color: var(--text-3); margin: 6px 0 6px; }
  .dtab { display: flex; flex-direction: column; gap: 2px; margin-bottom: 6px; }
  .dzeile { display: flex; align-items: center; gap: 12px; padding: 5px 8px; border-radius: var(--r-s); font-size: 12.5px; }
  .dzeile:hover { background: var(--surface-2); }
  .dn { flex: 1; color: var(--text-1); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .dv { color: var(--text-2); font-family: var(--font-mono); font-size: 12px; }
  .dv.rechts { margin-left: auto; }
</style>
