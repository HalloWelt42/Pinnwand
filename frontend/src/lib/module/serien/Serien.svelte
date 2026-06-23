<script lang="ts">
  import { ladeBoard, ladeSerien, erstelleSerie, aktualisiereSerie, loescheSerie, serieVorschau, serieVorbuchen, ladePersonen, type Serie, type Person } from '../../api'
  import type { Spalte } from '../../types'
  import { isoKurz } from '../../zeit'
  import { personSicht } from '../../personSicht.svelte'
  import { zuletztKuerzel } from '../../zuletztKuerzel.svelte'

  let { boardId }: { boardId: string } = $props()

  const WD = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So']

  let serien = $state<Serie[]>([])
  let spalten = $state<Spalte[]>([])
  let personen = $state<Person[]>([])
  // Ausgewaehlte Teilnehmer (Kuerzel): je Teilnehmer entsteht eine eigene Serie.
  let teilnehmer = $state<string[]>([])
  let tnVorbelegt = false
  let vorschau = $state<Record<string, string[]>>({})
  let meldung = $state('')

  // Formular
  let titel = $state('')
  let typ = $state<'taeglich' | 'woechentlich' | 'monatlich'>('woechentlich')
  let intervall = $state(1)
  let wochentage = $state<number[]>([])
  let monatstag = $state(1)
  let monatsregel = $state<'tag' | 'erster_werktag' | 'letzter_werktag'>('tag')
  let uhrzeit = $state('')
  let dauerMin = $state(30)
  let spalteId = $state('')
  let vorlaufTage = $state(21)
  let wochenendenUeberspringen = $state(false)
  let feiertageUeberspringen = $state(false)

  async function laden(): Promise<void> {
    serien = await ladeSerien(boardId)
    const b = await ladeBoard(boardId)
    spalten = b.spalten
    if (!spalteId && spalten[0]) spalteId = spalten[0].id
    personen = (await ladePersonen().catch(() => [])).filter((p) => !!p.kuerzel)
    // Beim ersten Laden den Default-Teilnehmer setzen: aktive Identitaet, sonst
    // zuletzt genutztes Kuerzel, sonst erste Person. Danach entscheidet der Nutzer.
    if (!tnVorbelegt) {
      tnVorbelegt = true
      const ak = personSicht.id ? (personen.find((p) => p.id === personSicht.id)?.kuerzel ?? null) : null
      const def = ak ?? (zuletztKuerzel.wert || null) ?? (personen[0]?.kuerzel ?? null)
      if (def) teilnehmer = [def]
    }
  }
  $effect(() => {
    void boardId
    laden()
  })

  function wtUmschalten(i: number): void {
    wochentage = wochentage.includes(i) ? wochentage.filter((x) => x !== i) : [...wochentage, i].sort()
  }
  function tnUmschalten(kuerzel: string): void {
    teilnehmer = teilnehmer.includes(kuerzel) ? teilnehmer.filter((x) => x !== kuerzel) : [...teilnehmer, kuerzel]
  }

  async function anlegen(): Promise<void> {
    if (!titel.trim()) return
    const basis = {
      board_id: boardId,
      spalte_id: spalteId || null,
      titel: titel.trim(),
      typ,
      intervall,
      wochentage: typ === 'woechentlich' ? wochentage : [],
      monatstag: typ === 'monatlich' && monatsregel === 'tag' ? monatstag : null,
      monatsregel: typ === 'monatlich' ? monatsregel : 'tag',
      uhrzeit: uhrzeit || null,
      dauer_min: dauerMin || null,
      vorlauf_tage: vorlaufTage,
      wochenenden_ueberspringen: wochenendenUeberspringen,
      feiertage_ueberspringen: feiertageUeberspringen,
    }
    // Je angehaktem Teilnehmer eine eigene Serie (jeder trackt seine eigene Zeit).
    // Nur aktuell bekannte Kuerzel; ohne gueltige Auswahl eine Serie ohne Zustaendigen.
    const gewaehlt = teilnehmer.filter((k) => k && personen.some((p) => p.kuerzel === k))
    const ziele: (string | null)[] = gewaehlt.length ? gewaehlt : [null]
    let erstellt = 0
    try {
      for (const kz of ziele) {
        await erstelleSerie({ ...basis, zustaendig: kz })
        erstellt++
      }
    } catch (e) {
      console.error(e)
      meldung = `Nur ${erstellt} von ${ziele.length} Serien angelegt - bitte erneut versuchen.`
      await laden()
      return
    }
    titel = ''
    uhrzeit = ''
    wochentage = []
    meldung = erstellt > 1
      ? `${erstellt} Serien angelegt und vorgebucht (je Teilnehmer eine).`
      : 'Serie angelegt und vorgebucht.'
    await laden()
  }

  async function umschaltenAktiv(s: Serie): Promise<void> {
    await aktualisiereSerie(s.id, { aktiv: !s.aktiv })
    await laden()
  }
  async function entfernen(s: Serie): Promise<void> {
    await loescheSerie(s.id)
    await laden()
  }
  async function vorbuchen(s: Serie): Promise<void> {
    const { erzeugt } = await serieVorbuchen(s.id)
    meldung = erzeugt ? `${erzeugt} Termine vorgebucht.` : 'Bereits aktuell - nichts Neues.'
  }
  async function zeigeVorschau(s: Serie): Promise<void> {
    vorschau = { ...vorschau, [s.id]: (await serieVorschau(s.id, 30)).termine }
  }

  function rhythmus(s: Serie): string {
    const iv = s.intervall > 1 ? `alle ${s.intervall} ` : ''
    if (s.typ === 'taeglich') return `${iv}Tage`.trim()
    if (s.typ === 'monatlich') {
      const wann = s.monatsregel === 'erster_werktag' ? 'erster Werktag' : s.monatsregel === 'letzter_werktag' ? 'letzter Werktag' : `Tag ${s.monatstag ?? '-'}`
      return `${iv}Monate, ${wann}`.trim()
    }
    const tage = s.wochentage.length ? s.wochentage.map((i) => WD[i]).join(', ') : 'wie Start'
    return `${iv}Wochen (${tage})`.trim()
  }
</script>

<div class="serien">
  <section class="neu">
    <p class="sec">Neue Serie</p>
    <div class="form">
      <input class="f titel" placeholder="Titel (z.B. REKO-Telko)" bind:value={titel} />
      <select class="f" bind:value={typ}>
        <option value="taeglich">täglich</option>
        <option value="woechentlich">wöchentlich</option>
        <option value="monatlich">monatlich</option>
      </select>
      <label class="f mini">Intervall <input type="number" min="1" bind:value={intervall} /></label>
      {#if typ === 'woechentlich'}
        <div class="wd">
          {#each WD as w, i (w)}
            <button type="button" class="wdb" class:an={wochentage.includes(i)} onclick={() => wtUmschalten(i)}>{w}</button>
          {/each}
        </div>
      {/if}
      {#if typ === 'monatlich'}
        <select class="f" bind:value={monatsregel}>
          <option value="tag">an festem Tag</option>
          <option value="erster_werktag">erster Werktag</option>
          <option value="letzter_werktag">letzter Werktag</option>
        </select>
        {#if monatsregel === 'tag'}
          <label class="f mini">Monatstag <input type="number" min="1" max="31" bind:value={monatstag} /></label>
        {/if}
      {/if}
      <label class="f mini">Uhrzeit <input type="time" bind:value={uhrzeit} /></label>
      <label class="f mini">Dauer (min) <input type="number" min="0" bind:value={dauerMin} /></label>
      <select class="f" bind:value={spalteId}>
        {#each spalten as s (s.id)}<option value={s.id}>{s.titel}</option>{/each}
      </select>
      <label class="f mini">Vorlauf (Tage) <input type="number" min="0" bind:value={vorlaufTage} /></label>
      <label class="f chk"><input type="checkbox" bind:checked={wochenendenUeberspringen} /> Wochenenden überspringen</label>
      <label class="f chk"><input type="checkbox" bind:checked={feiertageUeberspringen} /> Feiertage überspringen</label>
      {#if personen.length}
        <div class="tn">
          <span class="tn-lbl">Teilnehmer</span>
          {#each personen as p (p.id)}
            <label class="tnb" class:an={teilnehmer.includes(p.kuerzel ?? '')}>
              <input type="checkbox" checked={teilnehmer.includes(p.kuerzel ?? '')} onchange={() => tnUmschalten(p.kuerzel ?? '')} />
              {p.kuerzel} - {p.name}
            </label>
          {/each}
        </div>
      {/if}
      <button class="btn primaer" onclick={anlegen}>Anlegen + vorbuchen</button>
    </div>
    {#if meldung}<p class="meldung">{meldung}</p>{/if}
  </section>

  <section class="liste">
    <p class="sec">Serien dieses Boards</p>
    {#if !serien.length}<p class="leer">Noch keine Serien.</p>{/if}
    {#each serien as s (s.id)}
      <div class="serie" class:aus={!s.aktiv}>
        <div class="kopf">
          <span class="t">{s.uhrzeit ? s.uhrzeit + ' ' : ''}{s.titel}</span>
          {#if s.zustaendig}<span class="kz" title="Zustaendig">{s.zustaendig}</span>{/if}
          <span class="rhy">{rhythmus(s)}{#if s.dauer_min} &middot; {s.dauer_min} min{/if}</span>
          <span class="akt">
            <button class="ic" title="Vorschau" onclick={() => zeigeVorschau(s)}><i class="fa-solid fa-calendar-day" aria-hidden="true"></i></button>
            <button class="ic" title="Jetzt vorbuchen" onclick={() => vorbuchen(s)}><i class="fa-solid fa-bolt" aria-hidden="true"></i></button>
            <button class="ic" title={s.aktiv ? 'Pausieren' : 'Aktivieren'} onclick={() => umschaltenAktiv(s)}><i class="fa-solid {s.aktiv ? 'fa-pause' : 'fa-play'}" aria-hidden="true"></i></button>
            <button class="ic rot" title="Löschen" onclick={() => entfernen(s)}><i class="fa-solid fa-trash" aria-hidden="true"></i></button>
          </span>
        </div>
        {#if vorschau[s.id]}
          <div class="vs">{vorschau[s.id].slice(0, 8).map(isoKurz).join(' · ') || 'keine kommenden Termine'}</div>
        {/if}
      </div>
    {/each}
  </section>
</div>

<style>
  .serien {
    height: 100%;
    overflow-y: auto;
    padding: 16px;
    max-width: 900px;
  }
  .sec {
    font-family: var(--font-display);
    font-size: 11px;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: var(--text-3);
    margin: 0 0 8px;
  }
  .neu {
    margin-bottom: 18px;
  }
  .form {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    align-items: center;
  }
  .f {
    border: 1px solid var(--border-2);
    background: var(--surface-2);
    color: var(--text-1);
    border-radius: var(--r-m);
    padding: 7px 9px;
    font-size: 12.5px;
  }
  .f.titel {
    flex: 1;
    min-width: 200px;
  }
  .f.mini {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    color: var(--text-3);
    font-size: 11.5px;
  }
  .f.mini input {
    width: 64px;
    border: none;
    background: transparent;
    color: var(--text-1);
    font-size: 12.5px;
  }
  .f.chk {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    color: var(--text-2);
    font-size: 12px;
    border: none;
    background: transparent;
  }
  .tn {
    flex-basis: 100%;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 6px;
  }
  .tn-lbl {
    font-size: 11.5px;
    color: var(--text-3);
    margin-right: 2px;
  }
  .tnb {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    border: 1px solid var(--border-2);
    background: var(--surface-2);
    color: var(--text-2);
    border-radius: var(--r-s);
    padding: 5px 9px;
    font-size: 12px;
  }
  .tnb.an {
    background: var(--hl-primary-weich);
    color: var(--hl-primary-text);
    border-color: var(--hl-primary);
  }
  .kz {
    font-family: var(--font-mono);
    font-size: 10.5px;
    color: var(--hl-primary-text);
    background: var(--hl-primary-weich);
    padding: 1px 6px;
    border-radius: var(--r-s);
  }
  .wd {
    display: flex;
    gap: 3px;
  }
  .wdb {
    width: 32px;
    height: 32px;
    border-radius: var(--r-s);
    border: 1px solid var(--border-2);
    background: var(--surface-2);
    color: var(--text-2);
    font-size: 11px;
  }
  .wdb.an {
    background: var(--hl-primary);
    color: var(--hl-on-primary);
    border-color: transparent;
  }
  .btn {
    border: 1px solid var(--border);
    border-radius: var(--r-m);
    padding: 8px 13px;
    font-size: 12.5px;
  }
  .btn.primaer {
    background: var(--hl-primary);
    color: var(--hl-on-primary);
    border-color: transparent;
    font-weight: 500;
  }
  .meldung {
    margin-top: 8px;
    font-size: 12px;
    color: var(--ok);
  }
  .leer {
    color: var(--text-3);
    font-size: 12.5px;
  }
  .serie {
    border: 1px solid var(--border);
    background: var(--surface-col);
    border-radius: var(--r-m);
    padding: 10px 12px;
    margin-bottom: 6px;
  }
  .serie.aus {
    opacity: 0.55;
  }
  .kopf {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .t {
    font-weight: 500;
    color: var(--text-1);
    font-size: 13px;
  }
  .rhy {
    font-size: 11.5px;
    color: var(--text-3);
  }
  .akt {
    margin-left: auto;
    display: flex;
    gap: 2px;
  }
  .ic {
    width: 28px;
    height: 28px;
    border-radius: var(--r-s);
    border: none;
    background: transparent;
    color: var(--text-3);
    font-size: 12px;
  }
  .ic:hover {
    background: var(--surface-3);
    color: var(--hl-primary-text);
  }
  .ic.rot:hover {
    color: var(--gefahr);
  }
  .vs {
    margin-top: 8px;
    font-size: 11.5px;
    color: var(--text-2);
    font-family: var(--font-mono);
  }
</style>
