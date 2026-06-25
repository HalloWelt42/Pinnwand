<script lang="ts">
  // Verknuepfte Aufgaben (geteilte Zeitgruppe): Mitglieder anzeigen/oeffnen, weitere
  // Aufgabe per Suche verknuepfen, Verknuepfung loesen, Schalter "Zeit teilen".
  // Die Zeit zaehlt weiter EINMAL je zeiteintrag; dies ist nur die Gruppen-/Anzeigeschicht.
  import type { Karte } from '../../types'
  import { karteVerknuepfen, verknuepfungLoesen, gruppeZeitTeilen } from '../../api'

  let {
    karte,
    boardKarten = [],
    onReload,
    onOeffneKarte,
  }: {
    karte: Karte
    boardKarten?: Karte[]
    onReload?: () => void | Promise<void>
    onOeffneKarte?: (id: string) => void
  } = $props()

  const geteilt = $derived(!!karte.gruppe_id && karte.gruppe_zeit_geteilt !== false)

  let vSuche = $state('')
  const vTreffer = $derived.by(() => {
    const q = vSuche.trim().toLowerCase()
    if (!q) return []
    const drin = new Set([karte.id, ...(karte.gruppe_mitglieder ?? []).map((m) => m.id)])
    return boardKarten
      .filter((k) => !drin.has(k.id) && k.typ !== 'idee')
      .filter((k) => k.titel.toLowerCase().includes(q) || (k.schluessel ?? '').toLowerCase().includes(q))
      .slice(0, 8)
  })

  // Suchfeld bei Kartenwechsel leeren.
  let zuletzt: string | null = null
  $effect(() => {
    if (karte.id !== zuletzt) {
      zuletzt = karte.id
      vSuche = ''
    }
  })

  async function verknuepfeMit(ziel: Karte): Promise<void> {
    vSuche = ''
    await karteVerknuepfen(karte.id, ziel.id)
    await onReload?.()
  }
  async function loeseVerknuepfung(): Promise<void> {
    await verknuepfungLoesen(karte.id)
    await onReload?.()
  }
  async function zeitTeilenUmschalten(): Promise<void> {
    if (!karte.gruppe_id) return
    await gruppeZeitTeilen(karte.gruppe_id, !geteilt)
    await onReload?.()
  }
</script>

<p class="sec">Verknüpfte Aufgaben</p>
{#if (karte.gruppe_mitglieder?.length ?? 0)}
  <div class="vliste">
    {#each karte.gruppe_mitglieder ?? [] as m (m.id)}
      <div class="vrow">
        <button class="vlink" onclick={() => onOeffneKarte?.(m.id)} title="Aufgabe öffnen">
          {#if m.schluessel}<span class="vkey">{m.schluessel}</span>{/if}<span class="vtitel">{m.titel}</span>
        </button>
      </div>
    {/each}
  </div>
  <label class="grpschalter"><input type="checkbox" checked={geteilt} onchange={zeitTeilenUmschalten} /> Zeit teilen (zählt einmal über die Gruppe)</label>
  <button class="mini geist" onclick={loeseVerknuepfung}><i class="fa-solid fa-link-slash" aria-hidden="true"></i> Diese Karte loslösen</button>
{/if}
<input class="feld" placeholder="Aufgabe suchen und verknüpfen ..." bind:value={vSuche} aria-label="Aufgabe verknuepfen" />
{#if vTreffer.length}
  <div class="ttreffer">
    {#each vTreffer as t (t.id)}
      <button class="ttr" onclick={() => verknuepfeMit(t)}><i class="fa-solid fa-link" aria-hidden="true"></i> <span>{t.schluessel ? t.schluessel + ' ' : ''}{t.titel}</span></button>
    {/each}
  </div>
{/if}

<style>
  .sec { font-family: var(--font-display); font-size: 10.5px; letter-spacing: 0.04em; text-transform: uppercase; color: var(--text-3); margin: 18px 0 8px; }
  .vliste { display: flex; flex-direction: column; gap: 4px; margin-bottom: 6px; }
  .vlink { display: inline-flex; align-items: center; gap: 7px; width: 100%; text-align: left; border: 1px solid var(--border); background: var(--surface-2); color: var(--text-1); border-radius: var(--r-s); padding: 6px 9px; font-size: 12px; }
  .vlink:hover { border-color: var(--hl-primary); }
  .vkey { font-family: var(--font-mono); font-size: 10px; color: var(--text-3); }
  .vtitel { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .grpschalter { display: flex; align-items: center; gap: 7px; font-size: 12px; color: var(--text-2); margin: 2px 0 8px; }
  .mini { border: 1px solid var(--hl-primary); background: var(--hl-primary); color: var(--hl-on-primary); border-radius: var(--r-s); padding: 4px 9px; font-size: 11.5px; white-space: nowrap; cursor: pointer; }
  .mini.geist { background: transparent; color: var(--text-2); border-color: var(--border-2); }
  .feld { width: 100%; box-sizing: border-box; border: 1px solid var(--border); background: var(--surface-2); color: var(--text-1); border-radius: var(--r-m); padding: 7px 9px; font-size: 12.5px; margin-top: 6px; }
  .ttreffer { display: flex; flex-direction: column; gap: 3px; margin-top: 5px; }
  .ttr { display: flex; align-items: center; gap: 8px; text-align: left; border: 1px solid var(--border); background: var(--surface-2); color: var(--text-1); border-radius: var(--r-m); padding: 7px 10px; font-size: 12.5px; cursor: pointer; }
  .ttr span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .ttr:hover { border-color: var(--hl-primary); }
</style>
