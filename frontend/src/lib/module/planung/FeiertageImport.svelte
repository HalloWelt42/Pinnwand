<script lang="ts">
  import {
    feiertageVorschau, feiertageUebernehmen, loescheFeiertage,
    type Feiertag, type Region,
  } from '../../api'
  import { dmy, wtagKurz } from '../../zeit'

  // Feiertage-Import: Land/Region/Jahr wählen, Vorschau ansehen und erst
  // dann übernehmen (nur für Admins).
  let { laender, feiertage, jahr, melde, feiertageNeuLaden }: {
    laender: Record<string, Region[]>
    feiertage: Feiertag[]
    jahr: number
    melde: (text: string) => void
    feiertageNeuLaden: () => Promise<void>
  } = $props()

  let ftLand = $state('DE')
  let ftRegion = $state('')
  let ftJahr = $state(new Date().getFullYear())
  let vorschau = $state<Feiertag[]>([])

  const regionen = $derived(laender[ftLand] ?? [])
  const regionNamen = $derived(new Map((laender[ftLand] ?? laender['DE'] ?? []).map((r) => [r.code, r.name])))
  const regionName = (code: string | null | undefined): string => (code ? (regionNamen.get(code) ?? code) : 'bundesweit')

  async function ftVorschau(): Promise<void> {
    vorschau = (await feiertageVorschau(ftLand, ftRegion || null, ftJahr)).eintraege
  }
  async function ftUebernehmen(): Promise<void> {
    const { uebernommen } = await feiertageUebernehmen(ftLand, ftRegion || null, ftJahr)
    melde(`${uebernommen} Feiertage übernommen.`)
    vorschau = []
    await feiertageNeuLaden()
  }
  async function ftLoeschen(): Promise<void> {
    await loescheFeiertage(jahr, ftRegion || null)
    await feiertageNeuLaden()
  }
</script>

<section class="block">
  <p class="sec">Feiertage</p>
  <div class="reihe">
    <select bind:value={ftLand} onchange={() => (ftRegion = '')}>
      {#each Object.keys(laender) as l (l)}<option value={l}>{l}</option>{/each}
    </select>
    <select bind:value={ftRegion}>
      <option value="">(ganzes Land)</option>
      {#each regionen as r (r.code)}<option value={r.code}>{r.name}</option>{/each}
    </select>
    <label class="mini">Jahr <input type="number" min="2000" max="2100" bind:value={ftJahr} /></label>
    <button class="btn" onclick={ftVorschau}>Vorschau</button>
    {#if vorschau.length}<button class="btn primaer" onclick={ftUebernehmen}>{vorschau.length} übernehmen</button>{/if}
    {#if feiertage.length}<button class="btn geist" onclick={ftLoeschen}>{jahr} entfernen</button>{/if}
  </div>
  {#if vorschau.length}
    <div class="ftbox">
      <p class="ftkopf"><i class="fa-solid fa-eye" aria-hidden="true"></i> Vorschau: {vorschau.length} Feiertage gefunden (noch nicht übernommen)</p>
      <div class="ftliste">
        {#each vorschau as f (f.datum + (f.region ?? ''))}
          <div class="ftz vs">
            <span class="ftd">{dmy(f.datum)}</span>
            <span class="ftw">{wtagKurz(f.datum)}</span>
            <span class="ftn">{f.name}</span>
            <span class="ftg" class:land={f.region}>{regionName(f.region)}</span>
          </div>
        {/each}
      </div>
    </div>
  {/if}
  <div class="ftbox">
    <p class="ftkopf">Übernommene Feiertage {jahr} ({feiertage.length})</p>
    {#if !feiertage.length}<p class="leer">Noch keine Feiertage übernommen.</p>{/if}
    {#if feiertage.length}
      <div class="ftliste">
        {#each feiertage as f (f.datum + (f.region ?? ''))}
          <div class="ftz">
            <span class="ftd">{dmy(f.datum)}</span>
            <span class="ftw">{wtagKurz(f.datum)}</span>
            <span class="ftn">{f.name}</span>
            <span class="ftg" class:land={f.region}>{regionName(f.region)}</span>
          </div>
        {/each}
      </div>
    {/if}
  </div>
</section>

<style>
  .sec { font-family: var(--font-display); font-size: 11px; letter-spacing: 0.04em; text-transform: uppercase; color: var(--text-3); margin: 0 0 8px; }
  .block { margin-bottom: 22px; }
  .reihe { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
  .reihe input, .reihe select { border: 1px solid var(--border-2); background: var(--surface-2); color: var(--text-1); border-radius: var(--r-m); padding: 7px 9px; font-size: 12.5px; }
  .mini { display: inline-flex; align-items: center; gap: 6px; color: var(--text-3); font-size: 11.5px; }
  .mini input { width: 130px; }
  .btn { border: 1px solid var(--border); background: var(--surface-2); color: var(--text-2); border-radius: var(--r-m); padding: 7px 12px; font-size: 12.5px; }
  .btn.primaer { background: var(--hl-primary); color: var(--hl-on-primary); border-color: transparent; font-weight: 500; }
  .btn.geist { background: transparent; color: var(--text-2); }
  .leer { color: var(--text-3); font-size: 12px; }
  .ftbox { margin-top: 12px; }
  .ftkopf { font-size: 12px; color: var(--text-2); margin: 0 0 6px; display: flex; align-items: center; gap: 7px; }
  .ftkopf i { color: var(--hl-primary-text); }
  .ftliste { border: 1px solid var(--border); border-radius: var(--r-m); overflow: hidden; background: var(--surface-col); max-height: 320px; overflow-y: auto; }
  .ftz { display: grid; grid-template-columns: 78px 34px 1fr 150px; align-items: center; gap: 8px; padding: 6px 11px; font-size: 12.5px; border-top: 1px solid var(--border); }
  .ftz:first-child { border-top: none; }
  .ftz.vs { background: color-mix(in srgb, var(--hl-primary) 6%, transparent); }
  .ftd { font-family: var(--font-mono); font-size: 11.5px; color: var(--text-2); }
  .ftw { color: var(--text-3); font-size: 11px; }
  .ftn { color: var(--text-1); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .ftg { justify-self: end; font-size: 10.5px; padding: 2px 8px; border-radius: 999px; background: var(--surface-3); color: var(--text-3); white-space: nowrap; }
  .ftg.land { background: var(--due-rot-bg); color: var(--due-rot-fg); }
</style>
