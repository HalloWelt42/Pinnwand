<script lang="ts">
  import {
    ladePersonen, erstellePerson, aktualisierePerson, loeschePerson,
    ladeUrlaub, setzeUrlaub, loescheUrlaub, ladeUrlaubskonten,
    ladeLaender, feiertageVorschau, feiertageUebernehmen, ladeFeiertage, loescheFeiertage,
    ladeAbwesenheitstypen, aktualisiereAbwesenheitstyp, ladeTagesregeln, setzeTagesregel, loescheTagesregel,
    type Person, type Urlaubstag, type Feiertag, type Urlaubskonto, type Region,
    type AbwesenheitTyp, type Tagesregel,
  } from '../../api'

  let { boardId }: { boardId: string } = $props()
  $effect(() => void boardId)

  const WD = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So']
  const jahr = new Date().getFullYear()

  let personen = $state<Person[]>([])
  let neuerName = $state('')
  let neuesKuerzel = $state('')
  let konten = $state<Record<string, Urlaubskonto>>({})

  // Urlaub
  let urlaubPerson = $state('')
  let uVon = $state('')
  let uBis = $state('')
  let uAnteil = $state(1)
  let urlaub = $state<Urlaubstag[]>([])

  // Feiertage
  let laender = $state<Record<string, Region[]>>({})
  let ftLand = $state('DE')
  let ftRegion = $state('')
  let ftJahr = $state(jahr)
  let vorschau = $state<Feiertag[]>([])
  let feiertage = $state<Feiertag[]>([])
  let meldung = $state('')

  // Abwesenheits-Arten + Regeln (Konfiguration)
  let abwTypen = $state<AbwesenheitTyp[]>([])
  let regeln = $state<Tagesregel[]>([])
  let rArt = $state<'jahrestag' | 'wochentag'>('jahrestag')
  let rMonat = $state(12)
  let rTag = $state(24)
  let rWochentag = $state(4)
  let rAnteil = $state(0.5)
  let rNotiz = $state('')

  async function ladenPersonen(): Promise<void> {
    personen = await ladePersonen()
    if (!urlaubPerson && personen[0]) urlaubPerson = personen[0].id
    await ladenKonten()
  }
  async function ladenKonten(): Promise<void> {
    try {
      const liste = await ladeUrlaubskonten(jahr)
      konten = Object.fromEntries(liste.map((k) => [k.person_id, k]))
    } catch { /* Planung bleibt nutzbar */ }
  }
  const deRegionen = $derived(laender['DE'] ?? [])

  async function bundeslandAendern(p: Person, wert: string): Promise<void> {
    await aktualisierePerson(p.id, { bundesland: wert || null })
    await ladenPersonen()
  }
  async function anspruchAendern(p: Person, wert: number): Promise<void> {
    await aktualisierePerson(p.id, { urlaubsanspruch: wert })
    await ladenPersonen()
  }
  async function restAendern(p: Person, wert: number): Promise<void> {
    await aktualisierePerson(p.id, { resturlaub_vorjahr: wert })
    await ladenPersonen()
  }
  async function restAusVorjahr(p: Person): Promise<void> {
    const k = konten[p.id]
    const vorschlag = Math.max(0, (p.urlaubsanspruch || 0) - (k?.genommen_vorjahr ?? 0))
    await aktualisierePerson(p.id, { resturlaub_vorjahr: vorschlag })
    await ladenPersonen()
  }
  $effect(() => { ladenPersonen() })
  $effect(() => {
    ladeLaender().then((d) => (laender = d.laender)).catch(() => {})
    ladeFeiertage(`${jahr}-01-01`, `${jahr}-12-31`).then((f) => (feiertage = f)).catch(() => {})
  })
  $effect(() => {
    if (urlaubPerson) ladeUrlaub(urlaubPerson, `${jahr}-01-01`, `${jahr}-12-31`).then((u) => (urlaub = u)).catch(() => {})
  })
  $effect(() => { ladenKonfig() })

  async function ladenKonfig(): Promise<void> {
    abwTypen = await ladeAbwesenheitstypen().catch(() => [])
    regeln = await ladeTagesregeln().catch(() => [])
  }
  async function anrechnenAendern(t: AbwesenheitTyp, wert: boolean): Promise<void> {
    await aktualisiereAbwesenheitstyp(t.code, { anrechnen: wert })
    await ladenKonfig()
    await ladenKonten()
  }
  async function farbeAendern(t: AbwesenheitTyp, wert: string): Promise<void> {
    await aktualisiereAbwesenheitstyp(t.code, { farbe: wert })
    await ladenKonfig()
  }
  async function regelHinzufuegen(): Promise<void> {
    const d: Partial<Tagesregel> = rArt === 'jahrestag'
      ? { art: 'jahrestag', monat: rMonat, tag: rTag, anteil: rAnteil, notiz: rNotiz || null }
      : { art: 'wochentag', wochentag: rWochentag, anteil: rAnteil, notiz: rNotiz || null }
    await setzeTagesregel(d)
    rNotiz = ''
    await ladenKonfig()
  }
  async function regelLoeschen(id: string): Promise<void> {
    await loescheTagesregel(id)
    await ladenKonfig()
  }
  async function brueckeUmschalten(r: Tagesregel): Promise<void> {
    await setzeTagesregel({ ...r, aktiv: !r.aktiv })
    await ladenKonfig()
  }
  const MON = ['', 'Jan', 'Feb', 'Maer', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez']
  const WDV = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So']
  function regelText(r: Tagesregel): string {
    if (r.art === 'jahrestag') return `${r.tag}. ${MON[r.monat ?? 0]} (jaehrlich)`
    if (r.art === 'wochentag') return `jeden ${WDV[r.wochentag ?? 0]}`
    return 'Brueckentage'
  }

  const regionen = $derived(laender[ftLand] ?? [])
  const regionNamen = $derived(new Map((laender[ftLand] ?? laender['DE'] ?? []).map((r) => [r.code, r.name])))
  const regionName = (code: string | null | undefined): string => (code ? (regionNamen.get(code) ?? code) : 'bundesweit')

  const WTAG = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So']
  function wtag(iso: string): string {
    const d = new Date(iso + 'T00:00:00')
    return WTAG[(d.getDay() + 6) % 7]
  }
  function dmy(iso: string): string {
    const [j, m, t] = iso.slice(0, 10).split('-')
    return `${t}.${m}.${j}`
  }

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
    const { gesetzt, uebersprungen } = await setzeUrlaub({ person_id: urlaubPerson, von: uVon, bis: uBis || uVon, anteil: uAnteil })
    meldung = `${gesetzt} Urlaubstage eingetragen` + (uebersprungen ? `, ${uebersprungen} freie Tage/Feiertage uebersprungen.` : '.')
    urlaub = await ladeUrlaub(urlaubPerson, `${jahr}-01-01`, `${jahr}-12-31`)
    await ladenKonten()
  }
  async function urlaubLoeschen(u: Urlaubstag): Promise<void> {
    await loescheUrlaub(u.id)
    urlaub = await ladeUrlaub(urlaubPerson, `${jahr}-01-01`, `${jahr}-12-31`)
    await ladenKonten()
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
    <p class="sec">Urlaubsanspruch {jahr} (Bundesland, Tage je Jahr, Resturlaub Vorjahr)</p>
    <div class="utab">
      <div class="ukopf"><span class="pn">Person</span><span>Bundesland</span><span>Anspruch</span><span>Rest Vorjahr</span><span>genommen</span><span>verbleibend</span><span></span></div>
      {#each personen as p (p.id)}
        {@const k = konten[p.id]}
        <div class="uzeile">
          <span class="pn"><b>{p.kuerzel ?? ''}</b> {p.name}</span>
          <select class="bl" value={p.bundesland ?? ''} onchange={(e) => bundeslandAendern(p, e.currentTarget.value)} aria-label="Bundesland">
            <option value="">-</option>
            {#each deRegionen as r (r.code)}<option value={r.code}>{r.name}</option>{/each}
          </select>
          <input class="uz" type="number" min="0" step="0.5" value={p.urlaubsanspruch} onchange={(e) => anspruchAendern(p, parseFloat(e.currentTarget.value) || 0)} aria-label="Urlaubsanspruch" />
          <input class="uz" type="number" min="0" step="0.5" value={p.resturlaub_vorjahr} onchange={(e) => restAendern(p, parseFloat(e.currentTarget.value) || 0)} aria-label="Resturlaub Vorjahr" />
          <span class="uw">{k ? k.genommen : 0}</span>
          <span class="uw" class:knapp={k ? k.verbleibend < 0 : false}>{k ? k.verbleibend : '-'}</span>
          <button class="mini geist" title="Resturlaub aus dem Vorjahr berechnen (Anspruch minus im Vorjahr genommen)" onclick={() => restAusVorjahr(p)}>aus Vorjahr</button>
        </div>
      {/each}
      {#if !personen.length}<div class="uzeile leerz">Noch keine Personen.</div>{/if}
    </div>
    <p class="hinweis">Verbleibend = Anspruch + Resturlaub Vorjahr − die {jahr} genommenen Urlaubstage (halbe Tage zaehlen 0,5). Das Bundesland ist je Person hinterlegt und dient als Grundlage fuer die regionalen Feiertage (Import unten).</p>
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
        {#each regionen as r (r.code)}<option value={r.code}>{r.name}</option>{/each}
      </select>
      <label class="mini">Jahr <input type="number" min="2000" max="2100" bind:value={ftJahr} /></label>
      <button class="btn" onclick={ftVorschau}>Vorschau</button>
      {#if vorschau.length}<button class="btn primaer" onclick={ftUebernehmen}>{vorschau.length} uebernehmen</button>{/if}
      {#if feiertage.length}<button class="btn geist" onclick={ftLoeschen}>{jahr} entfernen</button>{/if}
    </div>
    {#if vorschau.length}
      <div class="ftbox">
        <p class="ftkopf"><i class="fa-solid fa-eye" aria-hidden="true"></i> Vorschau: {vorschau.length} Feiertage gefunden (noch nicht uebernommen)</p>
        <div class="ftliste">
          {#each vorschau as f (f.datum + (f.region ?? ''))}
            <div class="ftz vs">
              <span class="ftd">{dmy(f.datum)}</span>
              <span class="ftw">{wtag(f.datum)}</span>
              <span class="ftn">{f.name}</span>
              <span class="ftg" class:land={f.region}>{regionName(f.region)}</span>
            </div>
          {/each}
        </div>
      </div>
    {/if}
    <div class="ftbox">
      <p class="ftkopf">Uebernommene Feiertage {jahr} ({feiertage.length})</p>
      {#if !feiertage.length}<p class="leer">Noch keine Feiertage uebernommen.</p>{/if}
      {#if feiertage.length}
        <div class="ftliste">
          {#each feiertage as f (f.datum + (f.region ?? ''))}
            <div class="ftz">
              <span class="ftd">{dmy(f.datum)}</span>
              <span class="ftw">{wtag(f.datum)}</span>
              <span class="ftn">{f.name}</span>
              <span class="ftg" class:land={f.region}>{regionName(f.region)}</span>
            </div>
          {/each}
        </div>
      {/if}
    </div>
  </section>

  <section class="block">
    <p class="sec">Abwesenheits-Arten</p>
    <div class="atab">
      {#each abwTypen as t (t.code)}
        <div class="azeile">
          <input class="cfarbe" type="color" value={t.farbe} onchange={(e) => farbeAendern(t, e.currentTarget.value)} aria-label="Farbe" />
          <span class="aname">{t.name}</span>
          <span class="adez">{t.anwesend ? 'gilt als anwesend' : t.reduziert_soll ? 'reduziert Soll' : ''}</span>
          <label class="chk"><input type="checkbox" checked={t.anrechnen} onchange={(e) => anrechnenAendern(t, e.currentTarget.checked)} /> zaehlt gegen Urlaubsanspruch</label>
        </div>
      {/each}
    </div>
  </section>

  <section class="block">
    <p class="sec">Halbtags- und Sonderregeln</p>
    <p class="hinweis">Gelten global fuer alle. Anteil 0,5 = halber Tag, 0 = frei.</p>
    <div class="rliste">
      {#each regeln as r (r.id)}
        <div class="rzeile">
          {#if r.art === 'brueckentag'}
            <label class="chk"><input type="checkbox" checked={r.aktiv} onchange={() => brueckeUmschalten(r)} /> Brueckentage automatisch frei</label>
          {:else}
            <span class="rtext">{regelText(r)} - {r.anteil === 0 ? 'frei' : 'halber Tag'}{r.notiz ? ' (' + r.notiz + ')' : ''}</span>
            <button class="del" aria-label="Regel loeschen" onclick={() => regelLoeschen(r.id)}><i class="fa-solid fa-xmark" aria-hidden="true"></i></button>
          {/if}
        </div>
      {/each}
    </div>
    <div class="reihe rneu">
      <select bind:value={rArt}>
        <option value="jahrestag">fester Jahrestag</option>
        <option value="wochentag">Wochentag</option>
      </select>
      {#if rArt === 'jahrestag'}
        <select bind:value={rMonat}>{#each MON.slice(1) as m, i (i)}<option value={i + 1}>{m}</option>{/each}</select>
        <input class="kz" type="number" min="1" max="31" bind:value={rTag} aria-label="Tag" />
      {:else}
        <select bind:value={rWochentag}>{#each WDV as w, i (i)}<option value={i}>{w}</option>{/each}</select>
      {/if}
      <select bind:value={rAnteil}><option value={0.5}>halber Tag</option><option value={0}>frei</option></select>
      <input placeholder="Notiz" bind:value={rNotiz} />
      <button class="btn primaer" onclick={regelHinzufuegen}>Regel hinzufuegen</button>
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
  .btn { border: 1px solid var(--border); background: var(--surface-2); color: var(--text-2); border-radius: var(--r-m); padding: 7px 12px; font-size: 12.5px; }
  .btn.primaer { background: var(--hl-primary); color: var(--hl-on-primary); border-color: transparent; font-weight: 500; }
  .btn.geist { background: transparent; color: var(--text-2); }
  .chips { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px; }
  .chip { display: inline-flex; align-items: center; gap: 6px; font-size: 11px; padding: 3px 9px; border-radius: 999px; background: var(--surface-2); color: var(--text-2); }
  .chip button { border: none; background: transparent; color: var(--text-3); font-size: 10px; }
  .leer { color: var(--text-3); font-size: 12px; }

  .utab { border: 1px solid var(--border); border-radius: var(--r-l); overflow: hidden; background: var(--surface-col); }
  .ukopf, .uzeile { display: grid; grid-template-columns: 1fr 104px 72px 88px 80px 90px 88px; align-items: center; gap: 8px; padding: 6px 10px; }
  .ukopf { border-bottom: 1px solid var(--border); font-size: 10.5px; color: var(--text-3); text-transform: uppercase; }
  .ukopf span:not(.pn) { text-align: right; }
  .uzeile { border-top: 1px solid var(--border); font-size: 12.5px; }
  .uz { width: 100%; border: 1px solid var(--border-2); background: var(--surface-2); color: var(--text-1); border-radius: var(--r-s); padding: 4px 6px; font-size: 12px; font-family: var(--font-mono); text-align: right; }
  .bl { width: 100%; border: 1px solid var(--border-2); background: var(--surface-2); color: var(--text-1); border-radius: var(--r-s); padding: 4px 6px; font-size: 12px; }
  .uw { text-align: right; font-family: var(--font-mono); font-size: 12px; color: var(--text-2); }
  .uw.knapp { color: var(--gefahr); }
  .leerz { padding: 10px; color: var(--text-3); font-size: 12px; }
  .mini { border: 1px solid var(--border-2); background: var(--surface-2); color: var(--text-2); border-radius: var(--r-s); padding: 4px 6px; font-size: 10.5px; }
  .mini.geist { background: transparent; }
  .mini:hover { border-color: var(--hl-primary); color: var(--hl-primary-text); }
  .hinweis { font-size: 11.5px; color: var(--text-3); line-height: 1.55; margin: 8px 0 0; max-width: 80ch; }

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

  .atab { border: 1px solid var(--border); border-radius: var(--r-l); overflow: hidden; background: var(--surface-col); }
  .azeile { display: grid; grid-template-columns: 36px 160px 1fr auto; align-items: center; gap: 10px; padding: 7px 12px; border-top: 1px solid var(--border); font-size: 12.5px; }
  .azeile:first-child { border-top: none; }
  .cfarbe { width: 28px; height: 24px; border: 1px solid var(--border-2); border-radius: var(--r-s); background: none; padding: 0; }
  .aname { color: var(--text-1); }
  .adez { color: var(--text-3); font-size: 11.5px; }
  .rliste { display: flex; flex-direction: column; gap: 5px; margin-bottom: 10px; }
  .rzeile { display: flex; align-items: center; gap: 8px; border: 1px solid var(--border); background: var(--surface-col); border-radius: var(--r-m); padding: 7px 11px; font-size: 12.5px; }
  .rtext { flex: 1; color: var(--text-1); }
  .rneu .kz { width: 64px; }
</style>
