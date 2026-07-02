<script lang="ts">
  import {
    ladeTerminSerien, erstelleTerminSerie, aktualisiereTerminSerie, loescheTerminSerie,
    ladeTerminInstanzen, bestaetigeTermin, lehneTerminAb, ladePersonen,
    type TerminSerie, type TerminInstanz, type Person,
  } from '../../api'
  import { isoLang, ymd } from '../../zeit'

  let { boardId }: { boardId: string } = $props()
  $effect(() => void boardId)

  const WD = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So']

  let serien = $state<TerminSerie[]>([])
  let personen = $state<Person[]>([])
  let instanzen = $state<TerminInstanz[]>([])
  let meldung = $state('')
  let loeschId = $state<string | null>(null)
  let dauerEntwurf = $state<Record<string, number>>({})

  // Formular
  let titel = $state('')
  let kuerzel = $state('')
  let typ = $state<'taeglich' | 'woechentlich' | 'monatlich'>('taeglich')
  let intervall = $state(1)
  let wochentage = $state<number[]>([])
  let monatstag = $state(1)
  let monatsregel = $state<'tag' | 'erster_werktag' | 'letzter_werktag'>('tag')
  let uhrzeit = $state('')
  let dauerMin = $state(60)
  let start = $state('')
  let weSkip = $state(true)
  let ftSkip = $state(true)
  let urlaubSkip = $state(true)

  async function laden(): Promise<void> {
    serien = await ladeTerminSerien()
    personen = (await ladePersonen()).filter((p) => p.kuerzel)
    if (!kuerzel && personen[0]?.kuerzel) kuerzel = personen[0].kuerzel
    const heute = new Date()
    const vor = new Date(heute.getTime() - 90 * 86400000)
    instanzen = await ladeTerminInstanzen({ von: ymd(vor), bis: ymd(heute) })
  }
  $effect(() => { laden() })

  function wtUmschalten(i: number): void {
    wochentage = wochentage.includes(i) ? wochentage.filter((x) => x !== i) : [...wochentage, i].sort()
  }

  async function anlegen(): Promise<void> {
    if (!titel.trim()) return
    await erstelleTerminSerie({
      titel: titel.trim(),
      kuerzel: kuerzel || null,
      typ,
      intervall,
      wochentage: typ === 'woechentlich' ? wochentage : [],
      monatstag: typ === 'monatlich' && monatsregel === 'tag' ? monatstag : null,
      monatsregel: typ === 'monatlich' ? monatsregel : 'tag',
      uhrzeit: uhrzeit || null,
      dauer_min: dauerMin,
      start: start || null,
      wochenenden_ueberspringen: weSkip,
      feiertage_ueberspringen: ftSkip,
      urlaub_ueberspringen: urlaubSkip,
    })
    titel = ''
    uhrzeit = ''
    wochentage = []
    meldung = 'Termin-Serie angelegt.'
    await laden()
  }
  async function aktivToggle(s: TerminSerie): Promise<void> {
    await aktualisiereTerminSerie(s.id, { aktiv: !s.aktiv })
    await laden()
  }
  async function loeschenBestaetigt(s: TerminSerie): Promise<void> {
    await loescheTerminSerie(s.id)
    loeschId = null
    meldung = 'Serie geloescht (bestaetigte Termine bleiben als Verlauf).'
    await laden()
  }
  function rhythmus(s: TerminSerie): string {
    const iv = s.intervall > 1 ? `alle ${s.intervall} ` : ''
    if (s.typ === 'taeglich') return `${iv}Tage`.trim()
    if (s.typ === 'monatlich') {
      const wann = s.monatsregel === 'erster_werktag' ? 'erster Werktag' : s.monatsregel === 'letzter_werktag' ? 'letzter Werktag' : `Tag ${s.monatstag ?? '-'}`
      return `${iv}Monate, ${wann}`.trim()
    }
    const tage = s.wochentage.length ? s.wochentage.map((i) => WD[i]).join(', ') : 'wie Start'
    return `${iv}Wochen (${tage})`.trim()
  }

  function dauerVon(i: TerminInstanz): number {
    return dauerEntwurf[i.id] ?? i.effektiv_min ?? i.geplant_min
  }
  async function bestaetigen(i: TerminInstanz): Promise<void> {
    await bestaetigeTermin(i.id, dauerVon(i))
    await laden()
  }
  async function ablehnen(i: TerminInstanz): Promise<void> {
    await lehneTerminAb(i.id)
    await laden()
  }
  const statusLabel: Record<string, string> = { schwebend: 'schwebend', bestaetigt: 'bestaetigt', abgelehnt: 'abgelehnt' }
</script>

<div class="termine">
  <section class="block">
    <p class="sec">Neue Termin-Serie</p>
    <div class="form">
      <input class="f titel" placeholder="Titel (z.B. Daily Standup)" bind:value={titel} />
      <select class="f" bind:value={kuerzel} aria-label="Person">
        {#each personen as p (p.id)}<option value={p.kuerzel}>{p.kuerzel} - {p.name}</option>{/each}
      </select>
      <select class="f" bind:value={typ}>
        <option value="taeglich">täglich</option>
        <option value="woechentlich">wöchentlich</option>
        <option value="monatlich">monatlich</option>
      </select>
      <label class="f mini">Intervall <input type="number" min="1" bind:value={intervall} /></label>
      {#if typ === 'woechentlich'}
        <div class="wd">
          {#each WD as w, i (w)}<button type="button" class="wdb" class:an={wochentage.includes(i)} onclick={() => wtUmschalten(i)}>{w}</button>{/each}
        </div>
      {/if}
      {#if typ === 'monatlich'}
        <select class="f" bind:value={monatsregel}>
          <option value="tag">an festem Tag</option>
          <option value="erster_werktag">erster Werktag</option>
          <option value="letzter_werktag">letzter Werktag</option>
        </select>
        {#if monatsregel === 'tag'}<label class="f mini">Monatstag <input type="number" min="1" max="31" bind:value={monatstag} /></label>{/if}
      {/if}
      <label class="f mini">Uhrzeit <input type="time" bind:value={uhrzeit} /></label>
      <label class="f mini">Dauer (min) <input type="number" min="0" step="5" bind:value={dauerMin} /></label>
      <label class="f mini">Ab <input type="date" bind:value={start} /></label>
      <label class="f chk"><input type="checkbox" bind:checked={weSkip} /> Wochenenden überspringen</label>
      <label class="f chk"><input type="checkbox" bind:checked={ftSkip} /> Feiertage überspringen</label>
      <label class="f chk"><input type="checkbox" bind:checked={urlaubSkip} /> an Urlaubstagen überspringen</label>
      <button class="btn primaer" onclick={anlegen}>Anlegen</button>
    </div>
    {#if meldung}<p class="meldung">{meldung}</p>{/if}
  </section>

  <section class="block">
    <p class="sec">Termin-Serien</p>
    {#if !serien.length}<p class="leer">Noch keine Termin-Serien.</p>{/if}
    {#each serien as s (s.id)}
      <div class="serie" class:aus={!s.aktiv}>
        <div class="kopf">
          <span class="t">{s.uhrzeit ? s.uhrzeit + ' ' : ''}{s.titel}</span>
          <span class="meta">{s.kuerzel ?? '-'} &middot; {rhythmus(s)} &middot; {s.dauer_min} min</span>
          <span class="aktionen">
            <button class="tbtn geist" onclick={() => aktivToggle(s)}>{s.aktiv ? 'Pausieren' : 'Aktivieren'}</button>
            {#if loeschId === s.id}
              <button class="tbtn rot" onclick={() => loeschenBestaetigt(s)}>Wirklich löschen</button>
              <button class="tbtn geist" onclick={() => (loeschId = null)}>Abbrechen</button>
            {:else}
              <button class="tbtn geist" onclick={() => (loeschId = s.id)} aria-label="Löschen"><i class="fa-solid fa-trash" aria-hidden="true"></i></button>
            {/if}
          </span>
        </div>
      </div>
    {/each}
  </section>

  <section class="block">
    <p class="sec">Verlauf und offene Termine</p>
    {#if !instanzen.length}<p class="leer">Keine Termine im Zeitraum.</p>{/if}
    {#each instanzen as i (i.id)}
      <div class="inst {i.status}">
        <span class="idatum">{isoLang(i.datum)}</span>
        <span class="ititel">{i.uhrzeit ? i.uhrzeit + ' ' : ''}{i.titel} <span class="ik">{i.kuerzel ?? ''}</span></span>
        <span class="istatus s-{i.status}">{statusLabel[i.status]}{#if i.status === 'bestaetigt'} {i.effektiv_min} min{/if}</span>
        <span class="iakt">
          <input class="dauer" type="number" min="0" step="5" value={dauerVon(i)} onchange={(e) => (dauerEntwurf[i.id] = parseInt(e.currentTarget.value) || 0)} />
          <span class="me">min</span>
          <button class="tbtn" onclick={() => bestaetigen(i)}>{i.status === 'bestaetigt' ? 'Aendern' : 'Bestätigen'}</button>
          {#if i.status !== 'abgelehnt'}<button class="tbtn geist" onclick={() => ablehnen(i)}>Fand nicht statt</button>{/if}
        </span>
      </div>
    {/each}
  </section>
</div>

<style>
  .termine { padding: 16px; overflow-y: auto; height: 100%; display: flex; flex-direction: column; gap: 16px; }
  .block { background: var(--surface-col); border: 1px solid var(--border); border-radius: var(--r-l); padding: 14px 16px; }
  .sec { font-family: var(--font-display); font-size: 10.5px; letter-spacing: 0.04em; text-transform: uppercase; color: var(--text-3); margin: 0 0 10px; }
  .form { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
  .f { border: 1px solid var(--border); background: var(--surface-2); color: var(--text-1); border-radius: var(--r-m); padding: 7px 9px; font-size: 12.5px; }
  .f.titel { flex: 1; min-width: 180px; }
  .f.mini { display: inline-flex; align-items: center; gap: 6px; color: var(--text-3); }
  .f.mini input { width: 76px; border: none; background: transparent; color: var(--text-1); }
  .f.chk { display: inline-flex; align-items: center; gap: 6px; color: var(--text-2); border: none; background: transparent; }
  .wd { display: flex; gap: 3px; }
  .wdb { border: 1px solid var(--border); background: var(--surface-2); color: var(--text-2); border-radius: var(--r-s); padding: 6px 9px; font-size: 11.5px; }
  .wdb.an { background: var(--hl-primary); color: var(--hl-on-primary); border-color: transparent; }
  .btn { border: 1px solid var(--border); border-radius: var(--r-m); padding: 7px 13px; font-size: 12.5px; }
  .btn.primaer { background: var(--hl-primary); color: var(--hl-on-primary); border-color: transparent; font-weight: 500; }
  .meldung { color: var(--ok); font-size: 12px; margin: 8px 0 0; }
  .leer { color: var(--text-3); font-size: 12.5px; margin: 0; }
  .serie { padding: 7px 0; border-bottom: 1px solid var(--border); }
  .serie.aus { opacity: 0.55; }
  .serie:last-child { border-bottom: none; }
  .kopf { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
  .kopf .t { font-size: 13px; color: var(--text-1); font-weight: 500; }
  .kopf .meta { font-size: 11.5px; color: var(--text-3); }
  .kopf .aktionen { margin-left: auto; display: flex; gap: 6px; }
  .tbtn { border: 1px solid var(--hl-primary); background: var(--hl-primary); color: var(--hl-on-primary); border-radius: var(--r-s); padding: 4px 9px; font-size: 11.5px; white-space: nowrap; }
  .tbtn.geist { background: transparent; color: var(--text-2); border-color: var(--border-2); }
  .tbtn.rot { background: transparent; color: var(--gefahr); border-color: var(--gefahr); }
  .inst { display: flex; align-items: center; gap: 10px; padding: 6px 0; border-bottom: 1px solid var(--border); font-size: 12.5px; }
  .inst:last-child { border-bottom: none; }
  .inst.abgelehnt { opacity: 0.5; }
  .idatum { flex: 0 0 96px; font-variant-numeric: tabular-nums; color: var(--text-2); }
  .ititel { flex: 1; min-width: 0; color: var(--text-1); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .ititel .ik { color: var(--text-3); font-size: 11px; }
  .istatus { flex: 0 0 auto; font-size: 11px; }
  .s-schwebend { color: var(--due-amber-fg, #b4690e); }
  .s-bestaetigt { color: var(--ok); }
  .s-abgelehnt { color: var(--text-3); }
  .iakt { display: flex; align-items: center; gap: 6px; }
  .iakt .dauer { width: 64px; border: 1px solid var(--border); background: var(--surface-2); color: var(--text-1); border-radius: var(--r-s); padding: 4px 6px; font-size: 12px; }
  .iakt .me { color: var(--text-3); font-size: 11px; }
</style>
