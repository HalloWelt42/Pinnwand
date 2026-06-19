<script lang="ts">
  import {
    ladePersonen, erstellePerson, aktualisierePerson, loeschePerson,
    ladeUrlaub, setzeUrlaub, loescheUrlaub,
    ladeLaender, feiertageVorschau, feiertageUebernehmen, ladeFeiertage, loescheFeiertage,
    type Person, type Urlaubstag, type Feiertag,
  } from '../../api'

  let { boardId }: { boardId: string } = $props()
  $effect(() => void boardId)

  const WD = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So']
  const jahr = new Date().getFullYear()

  let personen = $state<Person[]>([])
  let neuerName = $state('')
  let neuesKuerzel = $state('')

  // Urlaub
  let urlaubPerson = $state('')
  let uVon = $state('')
  let uBis = $state('')
  let uAnteil = $state(1)
  let urlaub = $state<Urlaubstag[]>([])

  // Feiertage
  let laender = $state<Record<string, string[]>>({})
  let ftLand = $state('DE')
  let ftRegion = $state('')
  let ftJahr = $state(jahr)
  let vorschau = $state<Feiertag[]>([])
  let feiertage = $state<Feiertag[]>([])
  let meldung = $state('')

  async function ladenPersonen(): Promise<void> {
    personen = await ladePersonen()
    if (!urlaubPerson && personen[0]) urlaubPerson = personen[0].id
  }
  $effect(() => { ladenPersonen() })
  $effect(() => {
    ladeLaender().then((d) => (laender = d.laender)).catch(() => {})
    ladeFeiertage(`${jahr}-01-01`, `${jahr}-12-31`).then((f) => (feiertage = f)).catch(() => {})
  })
  $effect(() => {
    if (urlaubPerson) ladeUrlaub(urlaubPerson, `${jahr}-01-01`, `${jahr}-12-31`).then((u) => (urlaub = u)).catch(() => {})
  })

  const regionen = $derived(laender[ftLand] ?? [])

  async function personAnlegen(): Promise<void> {
    if (!neuerName.trim()) return
    await erstellePerson({ name: neuerName.trim(), kuerzel: neuesKuerzel.trim() || null })
    neuerName = ''
    neuesKuerzel = ''
    await ladenPersonen()
  }
  async function stundeAendern(p: Person, i: number, wert: number): Promise<void> {
    const ws = [...p.wochenstunden]
    ws[i] = wert
    await aktualisierePerson(p.id, { wochenstunden: ws })
    await ladenPersonen()
  }
  async function personEntfernen(p: Person): Promise<void> {
    await loeschePerson(p.id)
    await ladenPersonen()
  }

  async function urlaubEintragen(): Promise<void> {
    if (!urlaubPerson || !uVon) return
    const { gesetzt } = await setzeUrlaub({ person_id: urlaubPerson, von: uVon, bis: uBis || uVon, anteil: uAnteil })
    meldung = `${gesetzt} Urlaubstage eingetragen.`
    urlaub = await ladeUrlaub(urlaubPerson, `${jahr}-01-01`, `${jahr}-12-31`)
  }
  async function urlaubLoeschen(u: Urlaubstag): Promise<void> {
    await loescheUrlaub(u.id)
    urlaub = await ladeUrlaub(urlaubPerson, `${jahr}-01-01`, `${jahr}-12-31`)
  }

  async function ftVorschau(): Promise<void> {
    vorschau = (await feiertageVorschau(ftLand, ftRegion || null, ftJahr)).eintraege
  }
  async function ftUebernehmen(): Promise<void> {
    const { uebernommen } = await feiertageUebernehmen(ftLand, ftRegion || null, ftJahr)
    meldung = `${uebernommen} Feiertage uebernommen.`
    vorschau = []
    feiertage = await ladeFeiertage(`${jahr}-01-01`, `${jahr}-12-31`)
  }
  async function ftLoeschen(): Promise<void> {
    await loescheFeiertage(jahr, ftRegion || null)
    feiertage = await ladeFeiertage(`${jahr}-01-01`, `${jahr}-12-31`)
  }
</script>

<div class="planung">
  {#if meldung}<p class="meldung">{meldung}</p>{/if}

  <section class="block">
    <p class="sec">Personen und Wochen-Soll (Stunden je Wochentag)</p>
    <div class="tab">
      <div class="kopf"><span class="pn">Person</span>{#each WD as w (w)}<span class="wd">{w}</span>{/each}<span class="pw"></span></div>
      {#each personen as p (p.id)}
        <div class="zeile">
          <span class="pn"><b>{p.kuerzel ?? ''}</b> {p.name}</span>
          {#each p.wochenstunden as h, i (i)}
            <input class="hw" type="number" min="0" max="24" step="0.5" value={h} onchange={(e) => stundeAendern(p, i, parseFloat(e.currentTarget.value) || 0)} />
          {/each}
          <span class="pw"><button class="del" aria-label="Person loeschen" onclick={() => personEntfernen(p)}><i class="fa-solid fa-trash" aria-hidden="true"></i></button></span>
        </div>
      {/each}
    </div>
    <div class="neu">
      <input placeholder="Name" bind:value={neuerName} />
      <input class="kz" placeholder="Kuerzel" bind:value={neuesKuerzel} />
      <button class="btn primaer" onclick={personAnlegen}>Person hinzufuegen</button>
    </div>
  </section>

  <section class="block">
    <p class="sec">Urlaub</p>
    <div class="reihe">
      <select bind:value={urlaubPerson}>
        {#each personen as p (p.id)}<option value={p.id}>{p.name}</option>{/each}
      </select>
      <label class="mini">von <input type="date" bind:value={uVon} /></label>
      <label class="mini">bis <input type="date" bind:value={uBis} /></label>
      <select bind:value={uAnteil}><option value={1}>ganzer Tag</option><option value={0.5}>halber Tag</option></select>
      <button class="btn primaer" onclick={urlaubEintragen}>Eintragen</button>
    </div>
    <div class="chips">
      {#each urlaub as u (u.id)}
        <span class="chip">{u.datum}{#if u.anteil < 1} (halb){/if}<button aria-label="Entfernen" onclick={() => urlaubLoeschen(u)}><i class="fa-solid fa-xmark" aria-hidden="true"></i></button></span>
      {/each}
      {#if !urlaub.length}<span class="leer">Kein Urlaub {jahr}.</span>{/if}
    </div>
  </section>

  <section class="block">
    <p class="sec">Feiertage</p>
    <div class="reihe">
      <select bind:value={ftLand} onchange={() => (ftRegion = '')}>
        {#each Object.keys(laender) as l (l)}<option value={l}>{l}</option>{/each}
      </select>
      <select bind:value={ftRegion}>
        <option value="">(ganzes Land)</option>
        {#each regionen as r (r)}<option value={r}>{r}</option>{/each}
      </select>
      <label class="mini">Jahr <input type="number" min="2000" max="2100" bind:value={ftJahr} /></label>
      <button class="btn" onclick={ftVorschau}>Vorschau</button>
      {#if vorschau.length}<button class="btn primaer" onclick={ftUebernehmen}>{vorschau.length} uebernehmen</button>{/if}
      {#if feiertage.length}<button class="btn geist" onclick={ftLoeschen}>{jahr} entfernen</button>{/if}
    </div>
    {#if vorschau.length}
      <div class="chips vorschau">
        {#each vorschau as f (f.datum)}<span class="chip vs">{f.datum} {f.name}</span>{/each}
      </div>
    {/if}
    <div class="chips">
      {#each feiertage as f (f.datum + (f.region ?? ''))}<span class="chip ft">{f.datum} {f.name}</span>{/each}
      {#if !feiertage.length}<span class="leer">Noch keine Feiertage uebernommen.</span>{/if}
    </div>
  </section>
</div>

<style>
  .planung { height: 100%; overflow-y: auto; padding: 16px; max-width: 920px; }
  .sec { font-family: var(--font-display); font-size: 11px; letter-spacing: 0.04em; text-transform: uppercase; color: var(--text-3); margin: 0 0 8px; }
  .block { margin-bottom: 22px; }
  .meldung { color: var(--ok); font-size: 12px; margin: 0 0 10px; }
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
  .neu input, .reihe input, .reihe select { border: 1px solid var(--border-2); background: var(--surface-2); color: var(--text-1); border-radius: var(--r-m); padding: 7px 9px; font-size: 12.5px; }
  .neu .kz { width: 90px; }
  .reihe { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
  .mini { display: inline-flex; align-items: center; gap: 6px; color: var(--text-3); font-size: 11.5px; }
  .mini input { width: 130px; }
  .btn { border: 1px solid var(--border); border-radius: var(--r-m); padding: 7px 12px; font-size: 12.5px; }
  .btn.primaer { background: var(--hl-primary); color: var(--hl-on-primary); border-color: transparent; font-weight: 500; }
  .btn.geist { background: transparent; color: var(--text-2); }
  .chips { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px; }
  .chip { display: inline-flex; align-items: center; gap: 6px; font-size: 11px; padding: 3px 9px; border-radius: 999px; background: var(--surface-2); color: var(--text-2); }
  .chip button { border: none; background: transparent; color: var(--text-3); font-size: 10px; }
  .chip.ft { background: var(--due-rot-bg); color: var(--due-rot-fg); }
  .chip.vs { background: var(--hl-primary-weich); color: var(--hl-primary-text); }
  .vorschau { max-height: 160px; overflow-y: auto; }
  .leer { color: var(--text-3); font-size: 12px; }
</style>
