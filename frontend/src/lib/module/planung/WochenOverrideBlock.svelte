<script lang="ts">
  import {
    ladeWochenOverride, setzeWochenOverride, loescheWochenOverride,
    type Person, type WochenOverride,
  } from '../../api'
  import { WOCHENTAGE_KURZ } from '../../zeit'

  // Wochen-Override: abweichende Wochenstunden einzelner Wochen je Person.
  let { personen, sichtbarePersonen, nurEigene, eigenePersonId, melde }: {
    personen: Person[]
    sichtbarePersonen: Person[]
    nurEigene: boolean
    eigenePersonId: string | null
    melde: (text: string) => void
  } = $props()

  const WD = WOCHENTAGE_KURZ
  const jahr = new Date().getFullYear()

  let ovPerson = $state('')
  let ovJahr = $state(jahr)
  let ovKw = $state(1)
  let ovStunden = $state<number[]>([8, 8, 8, 8, 8, 0, 0])
  let ovListe = $state<WochenOverride[]>([])

  async function ladenOv(): Promise<void> {
    if (!ovPerson) { ovListe = []; return }
    ovListe = await ladeWochenOverride(ovPerson)
    const p = personen.find((x) => x.id === ovPerson)
    if (p) ovStunden = [...p.wochenstunden]
  }
  async function ovSpeichern(): Promise<void> {
    if (!ovPerson) return
    await setzeWochenOverride(ovPerson, ovJahr, ovKw, ovStunden.map((x) => Number(x) || 0))
    melde(`Wochen-Override KW ${ovKw}/${ovJahr} gespeichert.`)
    await ladenOv()
  }
  async function ovLoeschenF(o: WochenOverride): Promise<void> {
    await loescheWochenOverride(ovPerson, o.jahr, o.kw)
    await ladenOv()
  }

  $effect(() => {
    if (!ovPerson && personen[0]) ovPerson = personen[0].id
  })
  $effect(() => { void ovPerson; void personen.length; ladenOv() })
  // Mitarbeiter pflegen nur die eigene Person - Auswahlfeld fest darauf setzen.
  $effect(() => {
    if (nurEigene && eigenePersonId && ovPerson !== eigenePersonId) ovPerson = eigenePersonId
  })
</script>

<section class="block">
  <p class="sec">Wochen-Override (einzelne Woche abweichend vom Wochen-Soll)</p>
  <div class="neu">
    <select class="ovsel" bind:value={ovPerson} aria-label="Person" disabled={nurEigene}>{#each sichtbarePersonen as p (p.id)}<option value={p.id}>{p.name}</option>{/each}</select>
    <label class="ovk">Jahr <input class="ovnum jahr" type="number" min="2000" max="2100" bind:value={ovJahr} /></label>
    <label class="ovk">KW <input class="ovnum" type="number" min="1" max="53" bind:value={ovKw} /></label>
  </div>
  <div class="tab ovin">
    <div class="kopf"><span class="pn">Stunden</span>{#each WD as w (w)}<span class="wd">{w}</span>{/each}</div>
    <div class="zeile">
      <span class="pn">KW {ovKw}/{ovJahr}</span>
      {#each ovStunden as _h, i (i)}
        <input class="hw" type="number" min="0" max="24" step="0.5" bind:value={ovStunden[i]} />
      {/each}
    </div>
  </div>
  <div class="ovaktion"><button class="btn primaer" onclick={ovSpeichern}>Woche speichern</button></div>
  {#if ovListe.length}
    <div class="tab ovsaved">
      <div class="kopf"><span class="pn">Gespeichert</span>{#each WD as w (w)}<span class="wd">{w}</span>{/each}<span></span></div>
      {#each ovListe as o (o.jahr + '-' + o.kw)}
        <div class="zeile">
          <span class="pn">KW {o.kw}/{o.jahr}</span>
          {#each o.wochenstunden as h, i (i)}<span class="ovw">{h}</span>{/each}
          <button class="del" aria-label="Override löschen" onclick={() => ovLoeschenF(o)}><i class="fa-solid fa-trash" aria-hidden="true"></i></button>
        </div>
      {/each}
    </div>
  {:else}
    <p class="leer">Keine Overrides für diese Person.</p>
  {/if}
</section>

<style>
  .sec { font-family: var(--font-display); font-size: 11px; letter-spacing: 0.04em; text-transform: uppercase; color: var(--text-3); margin: 0 0 8px; }
  .block { margin-bottom: 22px; }
  .tab { border: 1px solid var(--border); border-radius: var(--r-l); overflow: hidden; background: var(--surface-col); }
  .kopf, .zeile { display: grid; grid-template-columns: 1fr repeat(7, 52px) 40px; align-items: center; gap: 6px; padding: 6px 10px; }
  .kopf { border-bottom: 1px solid var(--border); font-size: 10.5px; color: var(--text-3); text-transform: uppercase; }
  .zeile { border-top: 1px solid var(--border); font-size: 12.5px; }
  .kopf .wd, .zeile .hw { text-align: center; }
  .pn { color: var(--text-1); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .hw { width: 48px; border: 1px solid var(--border-2); background: var(--surface-2); color: var(--text-1); border-radius: var(--r-s); padding: 4px; font-size: 12px; font-family: var(--font-mono); }
  .del { border: none; background: transparent; color: var(--text-3); font-size: 11px; }
  .del:hover { color: var(--gefahr); }
  .neu { display: flex; gap: 8px; margin-top: 10px; flex-wrap: wrap; }
  .neu input, .neu select { border: 1px solid var(--border-2); background: var(--surface-2); color: var(--text-1); border-radius: var(--r-m); padding: 7px 9px; font-size: 12.5px; }
  /* Wochen-Override: eigene Raster, schmalere Spalten, Speichern auf eigener Zeile (nicht abgeschnitten). */
  .ovin .kopf, .ovin .zeile { grid-template-columns: 1fr repeat(7, 48px); gap: 5px; }
  .ovsaved .kopf, .ovsaved .zeile { grid-template-columns: 1fr repeat(7, 48px) 34px; gap: 5px; }
  .ovin .hw { width: 100%; }
  .ovsaved .del { justify-self: end; border: none; background: transparent; color: var(--text-3); font-size: 11px; }
  .ovsaved .del:hover { color: var(--gefahr); }
  .ovaktion { display: flex; justify-content: flex-end; margin-top: 8px; }
  .ovw { text-align: center; font-family: var(--font-mono); font-size: 12px; color: var(--text-2); }
  .ovsel { min-width: 150px; }
  .ovk { display: inline-flex; align-items: center; gap: 6px; color: var(--text-3); font-size: 12px; }
  .ovnum { width: 54px; border: 1px solid var(--border-2); background: var(--surface-2); color: var(--text-1); border-radius: var(--r-s); padding: 6px 8px; font-size: 12.5px; }
  .ovnum.jahr { width: 68px; }
  .btn { border: 1px solid var(--border); background: var(--surface-2); color: var(--text-2); border-radius: var(--r-m); padding: 7px 12px; font-size: 12.5px; }
  .btn.primaer { background: var(--hl-primary); color: var(--hl-on-primary); border-color: transparent; font-weight: 500; }
  .leer { color: var(--text-3); font-size: 12px; }
</style>
