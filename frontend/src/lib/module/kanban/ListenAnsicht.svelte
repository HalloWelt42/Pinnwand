<script lang="ts">
  // Tabellen-/Listenansicht des Boards: dieselben (gefilterten) Karten wie die
  // Spaltenansicht, flach als sortierbare Tabelle. Bearbeitet wird weiterhin im
  // Drawer - die Liste ist eine Lese- und Einstiegs-Sicht.
  import type { Karte } from '../../types'
  import { formatStd, isoKurz } from '../../zeit'

  interface Zeile {
    karte: Karte
    spalteTitel: string
    erledigt: boolean
  }

  let { zeilen, onOeffnen }: { zeilen: Zeile[]; onOeffnen: (id: string) => void } = $props()

  type SortFeld = 'schluessel' | 'titel' | 'status' | 'zustaendig' | 'prioritaet' | 'faellig' | 'zeit'
  let sortFeld = $state<SortFeld>('status')
  let sortAuf = $state(true)

  const PRIO_RANG: Record<string, number> = { hoch: 0, mittel: 1, niedrig: 2 }

  function wert(z: Zeile): string | number {
    const k = z.karte
    switch (sortFeld) {
      case 'schluessel': return k.schluessel ?? ''
      case 'titel': return k.titel.toLowerCase()
      case 'status': return z.spalteTitel.toLowerCase()
      case 'zustaendig': return k.zustaendig ?? '~'
      case 'prioritaet': return PRIO_RANG[k.prioritaet ?? ''] ?? 9
      case 'faellig': return k.faellig ?? '9999'
      case 'zeit': return k.erfasst_sek ?? 0
    }
  }
  const sortiert = $derived.by(() => {
    const r = sortAuf ? 1 : -1
    return [...zeilen].sort((a, b) => {
      const x = wert(a)
      const y = wert(b)
      if (typeof x === 'number' && typeof y === 'number') return (x - y) * r
      return String(x).localeCompare(String(y)) * r
    })
  })
  function sortiere(f: SortFeld): void {
    if (sortFeld === f) sortAuf = !sortAuf
    else {
      sortFeld = f
      sortAuf = true
    }
  }

  const SPALTEN: { feld: SortFeld; titel: string }[] = [
    { feld: 'schluessel', titel: 'Nr.' },
    { feld: 'titel', titel: 'Titel' },
    { feld: 'status', titel: 'Status' },
    { feld: 'zustaendig', titel: 'Zuständig' },
    { feld: 'prioritaet', titel: 'Priorität' },
    { feld: 'faellig', titel: 'Fällig' },
    { feld: 'zeit', titel: 'Zeit' },
  ]
</script>

<div class="liste">
  <table>
    <thead>
      <tr>
        {#each SPALTEN as s (s.feld)}
          <th class={s.feld}>
            <button class="sk" onclick={() => sortiere(s.feld)}>
              {s.titel}
              {#if sortFeld === s.feld}<i class="fa-solid {sortAuf ? 'fa-caret-up' : 'fa-caret-down'}" aria-hidden="true"></i>{/if}
            </button>
          </th>
        {/each}
      </tr>
    </thead>
    <tbody>
      {#each sortiert as z (z.karte.id)}
        {@const k = z.karte}
        <tr class:fertig={z.erledigt} onclick={() => onOeffnen(k.id)}>
          <td class="schluessel mono">{k.schluessel ?? ''}</td>
          <td class="titel">
            {#if k.typ === 'idee'}<i class="fa-regular fa-lightbulb idee" aria-hidden="true" title="Idee"></i>{/if}
            {#if k.blockiert_grund}<i class="fa-solid fa-hand blockiert" aria-hidden="true" title="Blockiert: {k.blockiert_grund}"></i>{/if}
            <span>{k.titel}</span>
            {#each k.labels.slice(0, 3) as l (l)}<span class="lbl">{l}</span>{/each}
          </td>
          <td class="status">{z.spalteTitel}</td>
          <td class="zustaendig">{#if k.zustaendig}<span class="av">{k.zustaendig}</span>{/if}</td>
          <td class="prioritaet">
            {#if k.prioritaet}<span class="prio {k.prioritaet}">{k.prioritaet}</span>{/if}
          </td>
          <td class="faellig mono">{k.faellig ? isoKurz(k.faellig) : ''}</td>
          <td class="zeit mono">
            {#if k.erfasst_sek}{formatStd(k.erfasst_sek)} h{/if}
            {#if k.schaetzung_min != null}<span class="soll">/ {formatStd(k.schaetzung_min * 60)} h</span>{/if}
          </td>
        </tr>
      {/each}
    </tbody>
  </table>
  {#if !zeilen.length}
    <p class="leer">Keine Karten (Filter aktiv?).</p>
  {/if}
</div>

<style>
  .liste { height: 100%; overflow: auto; padding: 12px 14px; }
  table { width: 100%; border-collapse: collapse; font-size: 12.5px; }
  thead th {
    position: sticky; top: 0; z-index: 1; background: var(--surface-col);
    text-align: left; padding: 0; border-bottom: 1px solid var(--border-2);
  }
  .sk {
    display: inline-flex; align-items: center; gap: 6px; width: 100%;
    border: none; background: transparent; color: var(--text-3);
    font-family: var(--font-display); font-size: 11px; letter-spacing: 0.04em;
    text-transform: uppercase; padding: 8px 10px; text-align: left;
  }
  .sk:hover { color: var(--text-1); }
  tbody tr { cursor: pointer; border-bottom: 1px solid var(--border); }
  tbody tr:hover { background: var(--surface-2); }
  tbody td { padding: 7px 10px; color: var(--text-1); vertical-align: middle; }
  tr.fertig td { color: var(--text-3); }
  tr.fertig .titel span { text-decoration: line-through; }
  .mono { font-family: var(--font-mono); font-size: 11px; color: var(--text-3); }
  .titel { min-width: 220px; }
  .titel .idee { color: var(--prio-mittel); margin-right: 5px; }
  .titel .blockiert { color: var(--gefahr); margin-right: 5px; font-size: 11px; }
  .lbl {
    margin-left: 6px; font-size: 10px; padding: 1px 7px; border-radius: 999px;
    background: var(--surface-3); color: var(--text-2); white-space: nowrap;
  }
  .av {
    display: inline-flex; align-items: center; justify-content: center;
    min-width: 24px; height: 24px; padding: 0 4px; border-radius: 50%;
    background: var(--hl-primary-weich); color: var(--hl-primary-text);
    font-size: 10px; font-weight: 600;
  }
  .prio { font-size: 10.5px; padding: 2px 8px; border-radius: 999px; }
  .prio.hoch { background: color-mix(in srgb, var(--prio-hoch) 18%, transparent); color: var(--prio-hoch); }
  .prio.mittel { background: color-mix(in srgb, var(--prio-mittel) 18%, transparent); color: var(--prio-mittel); }
  .prio.niedrig { background: color-mix(in srgb, var(--prio-niedrig) 18%, transparent); color: var(--prio-niedrig); }
  .soll { color: var(--text-3); margin-left: 3px; }
  .leer { color: var(--text-3); font-size: 12.5px; padding: 14px 4px; }
</style>
