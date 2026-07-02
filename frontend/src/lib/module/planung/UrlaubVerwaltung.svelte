<script lang="ts">
  import {
    aktualisierePerson, ladeUrlaub, setzeUrlaub, loescheUrlaub,
    type Person, type Urlaubstag, type Urlaubskonto, type Region,
  } from '../../api'
  import { dmy } from '../../zeit'

  // Urlaubsanspruch (Bundesland, Anspruch, Resturlaub Vorjahr, Konto) und
  // Urlaubseinträge (inkl. halber Tage) je Person.
  let {
    personen, sichtbarePersonen, nurEigene, eigenePersonId,
    konten, deRegionen, jahr,
    personenNeuLaden, kontenNeuLaden, feiertageNeuLaden, melde,
  }: {
    personen: Person[]
    sichtbarePersonen: Person[]
    nurEigene: boolean
    eigenePersonId: string | null
    konten: Record<string, Urlaubskonto>
    deRegionen: Region[]
    jahr: number
    personenNeuLaden: () => Promise<void>
    kontenNeuLaden: () => Promise<void>
    feiertageNeuLaden: () => Promise<void>
    melde: (text: string) => void
  } = $props()

  let urlaubPerson = $state('')
  let uVon = $state('')
  let uBis = $state('')
  let uAnteil = $state(1)
  let urlaub = $state<Urlaubstag[]>([])

  async function bundeslandAendern(p: Person, wert: string): Promise<void> {
    await aktualisierePerson(p.id, { bundesland: wert || null })
    await personenNeuLaden()
    // Das Backend stellt beim Bundesland-Wechsel die regionalen Feiertage sicher -
    // die Liste hier direkt nachladen, damit die Anzeige nicht veraltet.
    await feiertageNeuLaden().catch(() => {})
  }
  async function anspruchAendern(p: Person, wert: number): Promise<void> {
    await aktualisierePerson(p.id, { urlaubsanspruch: wert })
    await personenNeuLaden()
  }
  async function restAendern(p: Person, wert: number): Promise<void> {
    await aktualisierePerson(p.id, { resturlaub_vorjahr: wert })
    await personenNeuLaden()
  }
  async function restAusVorjahr(p: Person): Promise<void> {
    const k = konten[p.id]
    const vorschlag = Math.max(0, (p.urlaubsanspruch || 0) - (k?.genommen_vorjahr ?? 0))
    await aktualisierePerson(p.id, { resturlaub_vorjahr: vorschlag })
    await personenNeuLaden()
  }

  async function urlaubEintragen(): Promise<void> {
    if (!urlaubPerson || !uVon) return
    const { gesetzt, uebersprungen } = await setzeUrlaub({ person_id: urlaubPerson, von: uVon, bis: uBis || uVon, anteil: uAnteil })
    melde(`${gesetzt} Urlaubstage eingetragen` + (uebersprungen ? `, ${uebersprungen} freie Tage/Feiertage übersprungen.` : '.'))
    urlaub = await ladeUrlaub(urlaubPerson, `${jahr}-01-01`, `${jahr}-12-31`)
    await kontenNeuLaden()
  }
  async function urlaubLoeschen(u: Urlaubstag): Promise<void> {
    await loescheUrlaub(u.id)
    urlaub = await ladeUrlaub(urlaubPerson, `${jahr}-01-01`, `${jahr}-12-31`)
    await kontenNeuLaden()
  }

  $effect(() => {
    if (!urlaubPerson && personen[0]) urlaubPerson = personen[0].id
  })
  $effect(() => {
    if (urlaubPerson) ladeUrlaub(urlaubPerson, `${jahr}-01-01`, `${jahr}-12-31`).then((u) => (urlaub = u)).catch(() => {})
  })
  // Mitarbeiter pflegen nur die eigene Person - Auswahlfeld fest darauf setzen.
  $effect(() => {
    if (nurEigene && eigenePersonId && urlaubPerson !== eigenePersonId) urlaubPerson = eigenePersonId
  })
</script>

<section class="block">
  <p class="sec">Urlaubsanspruch {jahr} (Bundesland, Tage je Jahr, Resturlaub Vorjahr)</p>
  <div class="utab">
    <div class="ukopf"><span class="pn">Person</span><span>Bundesland</span><span>Anspruch</span><span>Rest Vorjahr</span><span>genommen</span><span>verbleibend</span><span></span></div>
    {#each sichtbarePersonen as p (p.id)}
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
        <button class="minibtn geist" title="Resturlaub aus dem Vorjahr berechnen (Anspruch minus im Vorjahr genommen)" onclick={() => restAusVorjahr(p)}>aus Vorjahr</button>
      </div>
    {/each}
    {#if !personen.length}<div class="uzeile leerz">Noch keine Personen.</div>{/if}
  </div>
  <p class="hinweis">Verbleibend = Anspruch + Resturlaub Vorjahr − die {jahr} genommenen Urlaubstage (halbe Tage zählen 0,5). Das Bundesland ist je Person hinterlegt und dient als Grundlage für die regionalen Feiertage (Import unten).</p>
</section>

<section class="block">
  <p class="sec">Urlaub</p>
  <div class="reihe">
    <select bind:value={urlaubPerson} disabled={nurEigene}>
      {#each sichtbarePersonen as p (p.id)}<option value={p.id}>{p.name}</option>{/each}
    </select>
    <label class="mini">von <input type="date" bind:value={uVon} /></label>
    <label class="mini">bis <input type="date" bind:value={uBis} /></label>
    <select bind:value={uAnteil}><option value={1}>ganzer Tag</option><option value={0.5}>halber Tag</option></select>
    <button class="btn primaer" onclick={urlaubEintragen}>Eintragen</button>
  </div>
  <div class="chips">
    {#each urlaub as u (u.id)}
      <span class="chip">{dmy(u.datum)}{#if u.anteil < 1} (halb){/if}<button aria-label="Entfernen" onclick={() => urlaubLoeschen(u)}><i class="fa-solid fa-xmark" aria-hidden="true"></i></button></span>
    {/each}
    {#if !urlaub.length}<span class="leer">Kein Urlaub {jahr}.</span>{/if}
  </div>
</section>

<style>
  .sec { font-family: var(--font-display); font-size: 11px; letter-spacing: 0.04em; text-transform: uppercase; color: var(--text-3); margin: 0 0 8px; }
  .block { margin-bottom: 22px; }
  .pn { color: var(--text-1); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
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
  .minibtn { border: 1px solid var(--border-2); background: var(--surface-2); color: var(--text-2); border-radius: var(--r-s); padding: 4px 8px; font-size: 10.5px; }
  .minibtn.geist { background: transparent; }
  .minibtn:hover { border-color: var(--hl-primary); color: var(--hl-primary-text); }
  .hinweis { font-size: 11.5px; color: var(--text-3); line-height: 1.55; margin: 8px 0 0; max-width: 80ch; }
  .reihe { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
  .reihe input, .reihe select { border: 1px solid var(--border-2); background: var(--surface-2); color: var(--text-1); border-radius: var(--r-m); padding: 7px 9px; font-size: 12.5px; }
  .mini { display: inline-flex; align-items: center; gap: 6px; color: var(--text-3); font-size: 11.5px; }
  .mini input { width: 130px; }
  .btn { border: 1px solid var(--border); background: var(--surface-2); color: var(--text-2); border-radius: var(--r-m); padding: 7px 12px; font-size: 12.5px; }
  .btn.primaer { background: var(--hl-primary); color: var(--hl-on-primary); border-color: transparent; font-weight: 500; }
  .chips { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px; }
  .chip { display: inline-flex; align-items: center; gap: 6px; font-size: 11px; padding: 3px 9px; border-radius: 999px; background: var(--surface-2); color: var(--text-2); }
  .chip button { border: none; background: transparent; color: var(--text-3); font-size: 10px; }
  .leer { color: var(--text-3); font-size: 12px; }
</style>
