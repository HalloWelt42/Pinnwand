<script lang="ts">
  // Tabellen-/Listenansicht des Boards: dieselben (gefilterten) Karten wie die
  // Spaltenansicht, flach als sortierbare Tabelle. Bearbeitet wird weiterhin im
  // Drawer - die Liste ist eine Lese- und Einstiegs-Sicht.
  import type { Karte, KarteAenderung, Prioritaet, Spalte } from '../../types'
  import { formatStd, isoKurz } from '../../zeit'

  interface Zeile {
    karte: Karte
    spalteTitel: string
    erledigt: boolean
  }

  let {
    zeilen,
    spalten,
    mitglieder,
    onOeffnen,
    onBulkVerschieben,
    onBulkAendern,
    onBulkLoeschen,
  }: {
    zeilen: Zeile[]
    spalten: Spalte[]
    mitglieder: string[]
    onOeffnen: (id: string) => void
    onBulkVerschieben: (ids: string[], spalteId: string) => Promise<void>
    onBulkAendern: (ids: string[], daten: KarteAenderung) => Promise<void>
    onBulkLoeschen: (ids: string[]) => Promise<void>
  } = $props()

  // Mehrfachauswahl fuer Sammel-Aktionen (Status/Zustaendig/Prioritaet/Loeschen).
  let auswahl = $state<Set<string>>(new Set())
  $effect(() => {
    // Zeilen-Wechsel (Filter, Reload): verschwundene Karten aus der Auswahl raeumen.
    const ids = new Set(zeilen.map((z) => z.karte.id))
    if ([...auswahl].some((id) => !ids.has(id))) {
      auswahl = new Set([...auswahl].filter((id) => ids.has(id)))
    }
  })
  function umschalten(id: string): void {
    const s = new Set(auswahl)
    s.has(id) ? s.delete(id) : s.add(id)
    auswahl = s
  }
  const alleGewaehlt = $derived(zeilen.length > 0 && zeilen.every((z) => auswahl.has(z.karte.id)))
  function alleUmschalten(): void {
    auswahl = alleGewaehlt ? new Set() : new Set(zeilen.map((z) => z.karte.id))
  }
  let laeuft = $state(false)
  async function aktion(f: () => Promise<void>): Promise<void> {
    if (laeuft) return
    laeuft = true
    try {
      await f()
      auswahl = new Set()
    } finally {
      laeuft = false
    }
  }
  let zielSpalte = $state('')
  let zielPerson = $state('')
  let zielPrio = $state('')

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
  {#if auswahl.size}
    <div class="bulk">
      <span class="bz">{auswahl.size} ausgewählt</span>
      <select bind:value={zielSpalte} aria-label="Status setzen" disabled={laeuft}
        onchange={() => { if (zielSpalte) aktion(() => onBulkVerschieben([...auswahl], zielSpalte)).then(() => (zielSpalte = '')) }}>
        <option value="">Status setzen ...</option>
        {#each spalten as s (s.id)}<option value={s.id}>{s.titel}</option>{/each}
      </select>
      <select bind:value={zielPerson} aria-label="Zuständig setzen" disabled={laeuft}
        onchange={() => { if (zielPerson) aktion(() => onBulkAendern([...auswahl], { zustaendig: zielPerson === '-' ? null : zielPerson })).then(() => (zielPerson = '')) }}>
        <option value="">Zuständig ...</option>
        <option value="-">niemand</option>
        {#each mitglieder as m (m)}<option value={m}>{m}</option>{/each}
      </select>
      <select bind:value={zielPrio} aria-label="Priorität setzen" disabled={laeuft}
        onchange={() => { if (zielPrio) aktion(() => onBulkAendern([...auswahl], { prioritaet: zielPrio === '-' ? null : (zielPrio as Prioritaet) })).then(() => (zielPrio = '')) }}>
        <option value="">Priorität ...</option>
        <option value="hoch">hoch</option>
        <option value="mittel">mittel</option>
        <option value="niedrig">niedrig</option>
        <option value="-">keine</option>
      </select>
      <button class="bloeschen" disabled={laeuft} onclick={() => aktion(() => onBulkLoeschen([...auswahl]))}>
        <i class="fa-solid fa-trash" aria-hidden="true"></i> Löschen
      </button>
      <button class="babbruch" disabled={laeuft} onclick={() => (auswahl = new Set())}>Auswahl aufheben</button>
    </div>
  {/if}
  <table>
    <thead>
      <tr>
        <th class="check">
          <input type="checkbox" checked={alleGewaehlt} aria-label="Alle auswählen" onchange={alleUmschalten} />
        </th>
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
        <tr class:fertig={z.erledigt} class:gewaehlt={auswahl.has(k.id)} onclick={() => onOeffnen(k.id)}>
          <td class="check" onclick={(e) => e.stopPropagation()}>
            <input type="checkbox" checked={auswahl.has(k.id)} aria-label="Karte auswählen" onchange={() => umschalten(k.id)} />
          </td>
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
  .check { width: 30px; text-align: center; }
  th.check { padding: 8px 6px; }
  td.check { cursor: default; }
  .check input { accent-color: var(--hl-primary); cursor: pointer; }
  tr.gewaehlt { background: var(--hl-primary-weich); }
  .bulk {
    position: sticky; top: 0; z-index: 2;
    display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
    background: var(--surface-3); border: 1px solid var(--hl-primary);
    border-radius: var(--r-m); padding: 7px 10px; margin-bottom: 10px; font-size: 12px;
  }
  .bulk .bz { color: var(--hl-primary-text); font-weight: 600; }
  .bulk select {
    border: 1px solid var(--border); background: var(--surface-1); color: var(--text-1);
    border-radius: var(--r-s); padding: 5px 7px; font-size: 12px;
  }
  .bloeschen {
    display: inline-flex; align-items: center; gap: 6px;
    border: 1px solid var(--gefahr); background: transparent; color: var(--gefahr);
    border-radius: var(--r-m); padding: 5px 10px; font-size: 12px;
  }
  .bloeschen:hover { background: var(--gefahr); color: #fff; }
  .babbruch { border: none; background: transparent; color: var(--text-3); font-size: 12px; margin-left: auto; }
  .babbruch:hover { color: var(--text-1); }
</style>
