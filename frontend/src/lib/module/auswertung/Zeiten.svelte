<script lang="ts">
  import type { BoardDetail, Zeiteintrag } from '../../types'
  import { zeigeToast } from '../../toaster.svelte'
  import { ladeBoard, ladeZeiteintraege, erstelleZeiteintrag, aktualisiereZeiteintrag, loescheZeiteintrag, ladeTerminInstanzen, ladePersonen, type TerminInstanz, type Person, type KiVorschlag } from '../../api'
  import { ymd, addTage, montagDer, isoWoche, formatStd, stdDezimal, wochentag, tagKurz } from '../../zeit'
  import { formatDauerVoll, parseZeit } from '../../timer.svelte'
  import { personSicht } from '../../personSicht.svelte'
  import KiAssistent from '../../ki/KiAssistent.svelte'

  let { boardId }: { boardId: string } = $props()

  // Eigentum: der Zeiteintrag gehoert der Person, der die Karte zugewiesen ist
  // (konsistent zur Stunden-Sicht). Bei aktiver Personen-Sicht sind fremde
  // Eintraege nur lesbar; bei "Alle" (Team) ist alles editierbar.
  let personen = $state<Person[]>([])
  $effect(() => { ladePersonen().then((p) => (personen = p)).catch(() => {}) })
  const aktivKuerzel = $derived(
    personSicht.id ? (personen.find((p) => p.id === personSicht.id)?.kuerzel ?? null) : null,
  )
  function istFremd(e: Zeiteintrag): boolean {
    // Eigentum haengt am Eintrags-Kuerzel (Snapshot); Fallback Karten-Kuerzel.
    return !!personSicht.id && ((e.kuerzel ?? e.karte_zustaendig) ?? null) !== aktivKuerzel
  }

  let anker = $state(new Date())
  let board = $state<BoardDetail | null>(null)
  let eintraege = $state<Zeiteintrag[]>([])
  let termine = $state<TerminInstanz[]>([])

  let nKarte = $state('')
  let nDatum = $state(ymd(new Date()))
  let nDauer = $state('')
  let nKommentar = $state('')

  const montag = $derived(montagDer(anker))
  const von = $derived(ymd(montag))
  const bis = $derived(ymd(addTage(montag, 6)))
  const kw = $derived(isoWoche(montag))
  const tage = $derived(Array.from({ length: 7 }, (_, i) => addTage(montag, i)))
  const wocheSumme = $derived(
    eintraege.reduce((s, e) => s + e.sekunden, 0) + termine.reduce((s, t) => s + (t.effektiv_min ?? 0) * 60, 0),
  )

  async function laden() {
    board = await ladeBoard(boardId)
    eintraege = await ladeZeiteintraege(von, bis)
    try {
      termine = (await ladeTerminInstanzen({ status: 'bestaetigt', von, bis })) ?? []
    } catch {
      termine = []
    }
  }
  $effect(() => {
    void von
    void boardId
    laden()
  })

  function eintraegeAm(tag: Date): Zeiteintrag[] {
    const key = ymd(tag)
    return eintraege.filter((e) => e.datum === key).sort((a, b) => (a.start ?? '').localeCompare(b.start ?? ''))
  }
  function termineAm(tag: Date): TerminInstanz[] {
    const key = ymd(tag)
    return termine.filter((t) => t.datum === key)
  }
  function tagSumme(tag: Date): number {
    return eintraegeAm(tag).reduce((s, e) => s + e.sekunden, 0)
      + termineAm(tag).reduce((s, t) => s + (t.effektiv_min ?? 0) * 60, 0)
  }

  async function dauerAendern(e: Zeiteintrag, wert: string) {
    const sek = parseZeit(wert)
    if (sek == null || sek === e.sekunden) return // unveraendert -> keine Rundung zurueckschreiben
    await aktualisiereZeiteintrag(e.id, { sekunden: sek })
    await laden()
  }
  async function kommentarAendern(e: Zeiteintrag, wert: string) {
    if ((e.kommentar ?? '') === wert) return
    await aktualisiereZeiteintrag(e.id, { kommentar: wert || null })
    await laden()
  }
  async function loeschen(e: Zeiteintrag) {
    const snap = { karte_id: e.karte_id, datum: e.datum, sekunden: e.sekunden, kommentar: e.kommentar ?? null }
    await loescheZeiteintrag(e.id)
    await laden()
    // Abrechnungsrelevante Daten bekommen dasselbe Undo-Schutznetz wie Karten.
    zeigeToast('Zeiteintrag gelöscht', async () => {
      await erstelleZeiteintrag(snap)
      await laden()
    })
  }
  async function hinzufuegen() {
    const sek = parseZeit(nDauer)
    if (!nKarte || sek == null) return
    await erstelleZeiteintrag({ karte_id: nKarte, datum: nDatum, sekunden: sek, kommentar: nKommentar || null })
    nDauer = ''
    nKommentar = ''
    // Woche dem gebuchten Tag folgen lassen, damit der Eintrag sichtbar ist
    // (auch wenn auf einen Tag ausserhalb der aktuellen Woche gebucht wurde).
    anker = new Date(nDatum + 'T00:00:00')
    await laden()
  }

  // KI hilft, in einer langen Kartenliste die gemeinte Karte zu finden; der Mensch
  // bestaetigt. Bei mehreren Treffern wird der erste uebernommen.
  function kiKarteKontext(): Record<string, unknown> {
    return {
      elemente: (board?.karten ?? []).map((k) => ({ id: k.id, text: `${k.schluessel} ${k.titel}` })),
    }
  }
  function kiKarteUebernehmen(gewaehlt: KiVorschlag[]): void {
    if (gewaehlt.length) nKarte = gewaehlt[0].id
  }

  // Zeit der angezeigten Woche je Karte (aus den datierten Eintraegen) - so wird
  // unterschieden, was IN DIESER WOCHE lief, auch wenn sich eine Aufgabe weit streckt.
  const istWocheJeKarte = $derived.by(() => {
    const m: Record<string, number> = {}
    for (const e of eintraege) m[e.karte_id] = (m[e.karte_id] ?? 0) + e.sekunden
    return m
  })
  const sollIst = $derived(
    (board?.karten ?? [])
      .map((k) => {
        const soll = (k.schaetzung_min ?? 0) * 60
        const ist = k.erfasst_sek ?? 0
        const woche = istWocheJeKarte[k.id] ?? 0
        return { k, soll, ist, woche, prozent: soll > 0 ? (ist / soll) * 100 : null }
      })
      .filter((r) => r.soll > 0 || r.ist > 0 || r.woche > 0)
      .sort((a, b) => b.woche - a.woche || b.ist - a.ist),
  )
</script>

<div class="zeiten">
  <header class="kopf">
    <div class="nav">
      <button class="ib" aria-label="Vorige Woche" onclick={() => (anker = addTage(montag, -7))}><i class="fa-solid fa-chevron-left" aria-hidden="true"></i></button>
      <div class="wo">
        <span class="kw">KW {kw}</span>
        <span class="spanne">{tagKurz(montag)} - {tagKurz(addTage(montag, 6))}</span>
      </div>
      <button class="ib" aria-label="Nächste Woche" onclick={() => (anker = addTage(montag, 7))}><i class="fa-solid fa-chevron-right" aria-hidden="true"></i></button>
      <button class="heute" onclick={() => (anker = new Date())}>Heute</button>
    </div>
    <div class="summe"><span class="s-label">Woche</span><span class="s-wert">{formatStd(wocheSumme)} h</span></div>
  </header>

  {#if sollIst.length}
    <section class="block">
      <p class="sec">Aufwand je Karte (diese Woche / gesamt gegen Schätzung)</p>
      <div class="tabelle">
        <div class="zeile kopfz">
          <span class="key"></span>
          <span class="titel">Karte</span>
          <span class="wwert">Diese Woche</span>
          <span class="werte">Gesamt / Soll</span>
          <span class="bar"></span>
          <span class="pz">%</span>
        </div>
        {#each sollIst as r (r.k.id)}
          <div class="zeile">
            <span class="key">{r.k.schluessel}</span>
            <span class="titel">{r.k.titel}</span>
            <span class="wwert" class:null={r.woche === 0}>{r.woche ? formatStd(r.woche) + ' h' : '-'}</span>
            <span class="werte">{formatStd(r.ist)} / {r.soll ? formatStd(r.soll) : '-'} h</span>
            <span class="bar"><span class:ueber={r.prozent != null && r.prozent > 100} style="width:{r.prozent != null ? Math.min(r.prozent, 100) : 0}%"></span></span>
            <span class="pz" class:ueber={r.prozent != null && r.prozent > 100}>{r.prozent != null ? Math.round(r.prozent) + '%' : '-'}</span>
          </div>
        {/each}
      </div>
    </section>
  {/if}

  <section class="block">
    <p class="sec">Zeit nachtragen</p>
    <div class="nachtrag">
      <select bind:value={nKarte} aria-label="Karte">
        <option value="" disabled>Karte wählen ...</option>
        {#each board?.karten ?? [] as k (k.id)}<option value={k.id}>{k.schluessel} · {k.titel}</option>{/each}
      </select>
      <KiAssistent typ="auswahl" titel="Karte finden" platzhalter="Welche Aufgabe? z.B. Upload-Bug" uebernehmenText="Waehlen" kontext={kiKarteKontext} onUebernehmen={kiKarteUebernehmen} />
      <input type="date" bind:value={nDatum} aria-label="Datum" />
      <input class="dauer" placeholder="1:30 oder 1,5" bind:value={nDauer} aria-label="Dauer" />
      <input class="komm" placeholder="Kommentar" bind:value={nKommentar} aria-label="Kommentar" onkeydown={(e) => { if (e.key === 'Enter') hinzufuegen() }} />
      <button class="btn primaer" onclick={hinzufuegen}>Hinzufügen</button>
    </div>
  </section>

  <section class="block">
    {#each tage as tag (ymd(tag))}
      {@const liste = eintraegeAm(tag)}
      {@const tliste = termineAm(tag)}
      <div class="tag">
        <div class="tagkopf">
          <span class="wd">{wochentag(tag)}</span>
          <span class="dt">{tagKurz(tag)}</span>
          <span class="tsum">{formatStd(tagSumme(tag))} h</span>
        </div>
        {#each liste as e (e.id)}
          {@const fremd = istFremd(e)}
          <div class="eintrag" class:fremd>
            <span class="key">{e.karte_schluessel ?? ''}</span>
            <span class="etitel">{e.karte_titel ?? e.karte_id}</span>
            {#if fremd}
              <span class="edauer ro">{formatDauerVoll(e.sekunden)}</span>
              <span class="rofremd" title={`Zeiteintrag von ${e.karte_zustaendig} - nur lesbar`}><i class="fa-solid fa-lock" aria-hidden="true"></i> {e.kommentar || e.karte_zustaendig}</span>
            {:else}
              <input class="edauer" value={formatDauerVoll(e.sekunden)} aria-label="Dauer (h:mm:ss)" title="h:mm:ss, h:mm oder Dezimalstunden (1,5)" onchange={(ev) => dauerAendern(e, ev.currentTarget.value)} />
              <input class="ekomm" value={e.kommentar ?? ''} placeholder="Kommentar ..." aria-label="Kommentar" onblur={(ev) => kommentarAendern(e, ev.currentTarget.value)} />
              {#if !e.manuell}<span class="auto" title="Automatisch erfasst"><i class="fa-solid fa-stopwatch" aria-hidden="true"></i></span>{/if}
              <button class="del" aria-label="Eintrag löschen" onclick={() => loeschen(e)}><i class="fa-solid fa-trash" aria-hidden="true"></i></button>
            {/if}
          </div>
        {/each}
        {#each tliste as t (t.id)}
          <div class="tzeile" title="Bestätigter Termin (in Termine änderbar)">
            <span class="ticon"><i class="fa-solid fa-calendar-check" aria-hidden="true"></i></span>
            <span class="etitel">{t.uhrzeit ? t.uhrzeit + ' ' : ''}{t.titel}{#if t.kuerzel} <span class="tk">{t.kuerzel}</span>{/if}</span>
            <span class="tdauer">{formatStd((t.effektiv_min ?? 0) * 60)} h</span>
            <span class="tlabel">Termin</span>
          </div>
        {/each}
        {#if !liste.length && !tliste.length}<div class="leer">keine Zeiten</div>{/if}
      </div>
    {/each}
  </section>
</div>

<style>
  .zeiten {
    height: 100%;
    overflow-y: auto;
    padding: 16px;
    max-width: 1000px;
  }
  .kopf {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
  }
  .nav {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .ib {
    width: 30px;
    height: 30px;
    border-radius: var(--r-m);
    border: 1px solid var(--border);
    background: var(--surface-2);
    color: var(--text-2);
  }
  .ib:hover {
    color: var(--hl-primary-text);
    border-color: var(--hl-primary);
  }
  .wo {
    display: flex;
    flex-direction: column;
    align-items: center;
    min-width: 150px;
  }
  .kw {
    font-family: var(--font-display);
    font-size: 15px;
    font-weight: 600;
    color: var(--text-1);
  }
  .spanne {
    font-size: 11px;
    color: var(--text-3);
  }
  .heute {
    border: 1px solid var(--border);
    background: var(--surface-2);
    color: var(--text-2);
    border-radius: var(--r-m);
    padding: 6px 12px;
    font-size: 12.5px;
  }
  .summe {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
  }
  .s-label {
    font-size: 11px;
    color: var(--text-3);
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }
  .s-wert {
    font-family: var(--font-mono);
    font-size: 20px;
    font-weight: 500;
    color: var(--text-1);
  }
  .block {
    margin-bottom: 18px;
  }
  .sec {
    font-family: var(--font-display);
    font-size: 11px;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: var(--text-3);
    margin: 0 0 8px;
  }
  .tabelle {
    background: var(--surface-col);
    border: 1px solid var(--border);
    border-radius: var(--r-l);
    overflow: hidden;
  }
  .tabelle .zeile {
    display: grid;
    grid-template-columns: 64px 1fr 92px 120px 130px 44px;
    align-items: center;
    gap: 10px;
    padding: 8px 12px;
    border-top: 1px solid var(--border);
    font-size: 12.5px;
  }
  .tabelle .zeile:first-child {
    border-top: none;
  }
  .kopfz {
    background: var(--surface-2);
  }
  .kopfz span {
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--text-3);
  }
  .wwert {
    font-family: var(--font-mono);
    font-size: 12px;
    color: var(--text-1);
    font-weight: 600;
    text-align: right;
  }
  .wwert.null {
    color: var(--text-3);
    font-weight: 400;
  }
  .kopfz .wwert,
  .kopfz .werte,
  .kopfz .pz {
    text-align: right;
  }
  .key {
    font-family: var(--font-mono);
    font-size: 10.5px;
    color: var(--text-3);
  }
  .titel,
  .etitel {
    color: var(--text-1);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .werte {
    font-family: var(--font-mono);
    font-size: 12px;
    color: var(--text-2);
    text-align: right;
  }
  .bar {
    height: 7px;
    border-radius: 4px;
    background: var(--border);
    overflow: hidden;
  }
  .bar > span {
    display: block;
    height: 100%;
    background: var(--hl-primary);
  }
  .bar > span.ueber {
    background: var(--gefahr);
  }
  .pz {
    text-align: right;
    color: var(--text-2);
    font-variant-numeric: tabular-nums;
  }
  .pz.ueber {
    color: var(--due-rot-fg);
    font-weight: 600;
  }
  .nachtrag {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    align-items: center;
  }
  .nachtrag select,
  .nachtrag input {
    border: 1px solid var(--border-2);
    background: var(--surface-2);
    color: var(--text-1);
    border-radius: var(--r-m);
    padding: 7px 9px;
    font-size: 12.5px;
  }
  .nachtrag select {
    flex: 1;
    min-width: 180px;
  }
  .nachtrag .dauer {
    width: 110px;
  }
  .nachtrag .komm {
    flex: 1;
    min-width: 160px;
  }
  .btn {
    border: 1px solid var(--border);
    border-radius: var(--r-m);
    padding: 7px 13px;
    font-size: 12.5px;
  }
  .btn.primaer {
    background: var(--hl-primary);
    color: var(--hl-on-primary);
    border-color: transparent;
    font-weight: 500;
  }
  .tag {
    border-top: 1px solid var(--border);
    padding: 10px 0;
  }
  .tagkopf {
    display: flex;
    align-items: baseline;
    gap: 10px;
    margin-bottom: 6px;
  }
  .wd {
    font-family: var(--font-display);
    font-weight: 600;
    font-size: 13px;
    color: var(--text-1);
  }
  .dt {
    font-size: 11px;
    color: var(--text-3);
  }
  .tsum {
    margin-left: auto;
    font-family: var(--font-mono);
    font-size: 12px;
    color: var(--text-2);
  }
  .eintrag {
    display: grid;
    grid-template-columns: 60px 1fr 84px 1.4fr auto auto;
    align-items: center;
    gap: 9px;
    padding: 4px 0;
  }
  .edauer,
  .ekomm {
    border: 1px solid transparent;
    background: var(--surface-2);
    color: var(--text-1);
    border-radius: var(--r-s);
    padding: 5px 8px;
    font-size: 12px;
  }
  .edauer {
    font-family: var(--font-mono);
    text-align: center;
  }
  .edauer:hover,
  .ekomm:hover {
    border-color: var(--border-2);
  }
  .edauer:focus,
  .ekomm:focus {
    border-color: var(--hl-primary);
    outline: none;
  }
  .auto {
    color: var(--text-3);
    font-size: 11px;
  }
  .del {
    border: none;
    background: transparent;
    color: var(--text-3);
    font-size: 11px;
  }
  .del:hover {
    color: var(--gefahr);
  }
  .eintrag.fremd {
    opacity: 0.9;
  }
  .edauer.ro {
    background: transparent;
    border-color: transparent;
    color: var(--text-2);
    cursor: default;
  }
  .rofremd {
    grid-column: 4 / -1;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    color: var(--text-3);
    font-size: 11.5px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .rofremd i {
    font-size: 10px;
  }
  .leer {
    font-size: 12px;
    color: var(--text-3);
    padding: 2px 0 4px;
  }
  .tzeile {
    display: flex;
    align-items: center;
    gap: 9px;
    padding: 4px 0;
    font-size: 12px;
    color: var(--text-2);
  }
  .tzeile .ticon {
    color: var(--hl-primary-text);
    font-size: 11px;
    width: 60px;
  }
  .tzeile .etitel {
    flex: 1;
  }
  .tzeile .tk {
    color: var(--text-3);
    font-size: 11px;
  }
  .tzeile .tdauer {
    font-family: var(--font-mono);
    font-size: 12px;
    color: var(--text-2);
  }
  .tzeile .tlabel {
    font-size: 10px;
    color: var(--hl-primary-text);
    background: var(--hl-primary-weich);
    border-radius: 999px;
    padding: 1px 7px;
  }
</style>
