<script lang="ts">
  import type { Karte, Prioritaet, Spalte, Zeiteintrag } from '../../types'
  import type { KarteAenderung, TranskriptTreffer, Person, TranskriptMarke, KiVorschlag } from '../../api'
  import { transkripteSuche, ladePersonen, ladeMarken, erstelleMarke, aktualisiereMarke, loescheMarke, zusammenfassungVorschlag, erstelleZeiteintrag, ladeKartenZeiten, aktualisiereZeiteintrag, loescheZeiteintrag, karteVerknuepfen, verknuepfungLoesen, gruppeZeitTeilen } from '../../api'
  import KiAssistent from '../../ki/KiAssistent.svelte'
  import { merkeKuerzel } from '../../zuletztKuerzel.svelte'
  import { oeffneTranskript } from '../../navigation.svelte'
  import { labelFarbe } from '../../labels'
  import { theme } from '../../theme/theme.svelte'
  import { isoLang, isoDatumZeit, ymd } from '../../zeit'
  import { timer, timerStarten, timerPausieren, timerStoppen, erfassteSekunden, formatDauerVoll, formatPlan, parseZeit, mmss } from '../../timer.svelte'
  import Markdown from '../../Markdown.svelte'
  import FarbWahl from '../../FarbWahl.svelte'
  import DokumentVerwaltung from '../../DokumentVerwaltung.svelte'
  import { tts, vorlesen, stoppeVorlesen } from '../../tts.svelte'

  let {
    karte,
    spalten,
    boardKarten = [],
    onSchliessen,
    onAendern,
    onKommentar,
    onLoeschen,
    onReload,
    onOeffneKarte,
  }: {
    karte: Karte
    spalten: Spalte[]
    boardKarten?: Karte[]
    onSchliessen: () => void
    onAendern: (daten: KarteAenderung) => void
    onKommentar: (text: string) => void
    onLoeschen: () => void
    onReload?: () => void | Promise<void>
    onOeffneKarte?: (id: string) => void
  } = $props()

  const dunkel = $derived(theme.modus === 'dunkel')

  // Lese- (Standard) vs. Bearbeitungsmodus. Vollbild erzwingt Bearbeiten des
  // ganzen Tickets. Kleine Dinge (Checkboxen, Zeit-/Zeileneintraege, Labels,
  // Kommentar) bleiben in BEIDEN Modi direkt bearbeitbar.
  let modus = $state<'lesen' | 'bearbeiten'>('lesen')
  let vollbild = $state(false)
  const bearbeiten = $derived(modus === 'bearbeiten' || vollbild)
  const istIdee = $derived(karte.typ === 'idee')
  function zuBearbeiten(): void { if (modus === 'lesen') modus = 'bearbeiten' }
  function typUmschalten(): void { onAendern({ typ: istIdee ? 'arbeit' : 'idee' }) }

  // Personen fuer die Zustaendig-Auswahl (echtes Dropdown statt Freitext, verhindert
  // Tippfehler/leeres Kuerzel). Einmalig beim Oeffnen laden.
  let personen = $state<Person[]>([])
  $effect(() => {
    ladePersonen().then((p) => (personen = p.filter((x) => !!x.kuerzel))).catch(() => {})
  })
  // Aktuelles Kuerzel der Karte mit aufnehmen, falls es (z.B. aus Altdaten) nicht
  // in der Personenliste steht - sonst wuerde die Auswahl es nicht anzeigen.
  const kuerzelWahl = $derived.by(() => {
    const z = karte.zustaendig
    if (z && !personen.some((p) => p.kuerzel === z)) {
      return [{ id: '_aktuell', name: z, kuerzel: z } as Person, ...personen]
    }
    return personen
  })
  function zustaendigSetzen(wert: string): void {
    const z = wert || null
    onAendern({ zustaendig: z })
    merkeKuerzel(z)
  }

  let beschr = $state('')
  let neuerPunkt = $state('')
  let neuesLabel = $state('')
  let kommentar = $state('')
  let gespeichert = $state(false)
  let spTimer: ReturnType<typeof setTimeout> | null = null

  let notiz = $state('')
  let notizGespeichert = $state(false)
  let notizTimer: ReturnType<typeof setTimeout> | null = null

  function notizAuto() {
    if (notizTimer) clearTimeout(notizTimer)
    notizGespeichert = false
    notizTimer = setTimeout(() => {
      onAendern({ notizen: notiz || null })
      notizGespeichert = true
    }, 600)
  }

  // Transkript-Verknuepfung
  let tSuche = $state('')
  let tTreffer = $state<TranskriptTreffer[]>([])
  let tTimer: ReturnType<typeof setTimeout> | null = null
  function tSuchen() {
    if (tTimer) clearTimeout(tTimer)
    const q = tSuche
    tTimer = setTimeout(async () => {
      try { tTreffer = (await transkripteSuche(q, 12)).treffer } catch { tTreffer = [] }
    }, 220)
  }
  function transkriptVerknuepfen(t: TranskriptTreffer) {
    onAendern({ transkript_id: t.id, transkript_name: t.name })
    tSuche = ''
    tTreffer = []
  }
  function transkriptEntfernen() {
    onAendern({ transkript_id: null, transkript_name: null })
  }

  // -- Transkript-Verweise (mehrere Marken je Karte, mit Position + Zusammenfassung) --
  let marken = $state<TranskriptMarke[]>([])
  let mSuche = $state('')
  let mTreffer = $state<TranskriptTreffer[]>([])
  let mTimer: ReturnType<typeof setTimeout> | null = null
  const zusTimer: Record<string, ReturnType<typeof setTimeout>> = {}
  let kiLaeuft = $state<string | null>(null)
  let kiVorschau = $state<Record<string, string>>({})
  let kiFehler = $state<Record<string, string>>({})

  async function ladeMarkenFuer(): Promise<void> {
    try { marken = (await ladeMarken(karte.id)).marken } catch { marken = [] }
  }
  function mSuchen(): void {
    if (mTimer) clearTimeout(mTimer)
    const q = mSuche
    mTimer = setTimeout(async () => {
      try { mTreffer = (await transkripteSuche(q, 12)).treffer } catch { mTreffer = [] }
    }, 220)
  }
  async function markeHinzufuegen(t: TranskriptTreffer): Promise<void> {
    const m = await erstelleMarke({ karte_id: karte.id, transkript_id: t.id, transkript_name: t.name })
    marken = [...marken, m]
    mSuche = ''
    mTreffer = []
  }
  function markeOeffnen(m: TranskriptMarke): void {
    oeffneTranskript(m.transkript_id, m.position_sek ?? null)
  }
  async function markeLoeschen(m: TranskriptMarke): Promise<void> {
    await loescheMarke(m.id)
    marken = marken.filter((x) => x.id !== m.id)
  }
  function zusAendern(m: TranskriptMarke, wert: string): void {
    m.zusammenfassung = wert
    if (zusTimer[m.id]) clearTimeout(zusTimer[m.id])
    zusTimer[m.id] = setTimeout(() => { aktualisiereMarke(m.id, { zusammenfassung: wert }).catch(() => {}) }, 600)
  }
  async function kiVorschlag(m: TranskriptMarke): Promise<void> {
    kiFehler = { ...kiFehler, [m.id]: '' }
    kiLaeuft = m.id
    try {
      const { zusammenfassung } = await zusammenfassungVorschlag(m.transkript_id, m.position_sek ?? null)
      kiVorschau = { ...kiVorschau, [m.id]: zusammenfassung }
    } catch (e) {
      kiFehler = { ...kiFehler, [m.id]: e instanceof Error ? e.message : 'KI nicht verfügbar' }
    } finally {
      kiLaeuft = null
    }
  }
  function kiVerwerfen(m: TranskriptMarke): void {
    const { [m.id]: _weg, ...rest } = kiVorschau
    kiVorschau = rest
  }
  function kiUebernehmen(m: TranskriptMarke): void {
    const t = kiVorschau[m.id]
    if (t == null) return
    m.zusammenfassung = t
    aktualisiereMarke(m.id, { zusammenfassung: t }).catch(() => {})
    kiVerwerfen(m)
  }

  function autoSpeichern() {
    if (spTimer) clearTimeout(spTimer)
    gespeichert = false
    spTimer = setTimeout(() => {
      onAendern({ beschreibung: beschr || null })
      gespeichert = true
    }, 600)
  }
  function bearbeitenFertig() {
    if (spTimer) clearTimeout(spTimer)
    onAendern({ beschreibung: beschr || null })
    if (notizTimer) clearTimeout(notizTimer)
    onAendern({ notizen: notiz || null })
    vollbild = false
    modus = 'lesen'
  }
  function vorlesenUmschalten() {
    if (tts.laeuft) stoppeVorlesen()
    else vorlesen(beschr)
  }

  // Beschreibungs-Entwurf folgt der Karte (auch beim ersten Öffnen).
  let zuletzt = $state<string | null>(null)
  $effect(() => {
    if (karte.id !== zuletzt) {
      zuletzt = karte.id
      beschr = karte.beschreibung ?? ''
      notiz = karte.notizen ?? ''
      notizGespeichert = false
      mSuche = ''
      mTreffer = []
      kiVorschau = {}
      modus = 'lesen'
      vollbild = false
      punktEdit = null
      vSuche = ''
      vTreffer = []
      ladeMarkenFuer()
      ladeKartenZeitenFuer()
    }
  })

  const erledigt = $derived(karte.checkliste.filter((c) => c.erledigt).length)

  function punktUmschalten(i: number) {
    const neu = karte.checkliste.map((c, idx) => (idx === i ? { ...c, erledigt: !c.erledigt } : c))
    onAendern({ checkliste: neu })
  }
  function punktHinzufuegen() {
    const t = neuerPunkt.trim()
    if (!t) return
    onAendern({ checkliste: [...karte.checkliste, { text: t, erledigt: false }] })
    neuerPunkt = ''
  }
  function punktEntfernen(i: number) {
    onAendern({ checkliste: karte.checkliste.filter((_, idx) => idx !== i) })
  }
  // Checklisten-Punkt umbenennen: betroffene Zeile als Eingabe, neues Array senden.
  let punktEdit = $state<number | null>(null)
  function punktText(i: number, wert: string) {
    const t = wert.trim()
    punktEdit = null
    if (!t || t === karte.checkliste[i]?.text) return
    onAendern({ checkliste: karte.checkliste.map((c, idx) => (idx === i ? { ...c, text: t } : c)) })
  }

  // -- Verknuepfte Aufgaben (geteilte Zeitgruppe) --
  let vSuche = $state('')
  const vTrefferRoh = $derived.by(() => {
    const q = vSuche.trim().toLowerCase()
    if (!q) return []
    const drin = new Set([karte.id, ...(karte.gruppe_mitglieder ?? []).map((m) => m.id)])
    return boardKarten
      .filter((k) => !drin.has(k.id) && k.typ !== 'idee')
      .filter((k) => k.titel.toLowerCase().includes(q) || (k.schluessel ?? '').toLowerCase().includes(q))
      .slice(0, 8)
  })
  let vTreffer = $state<Karte[]>([])
  $effect(() => { vTreffer = vTrefferRoh })
  async function verknuepfeMit(ziel: Karte): Promise<void> {
    vSuche = ''
    vTreffer = []
    await karteVerknuepfen(karte.id, ziel.id)
    await onReload?.()
  }
  async function loeseVerknuepfung(): Promise<void> {
    await verknuepfungLoesen(karte.id)
    await onReload?.()
  }
  async function zeitTeilenUmschalten(): Promise<void> {
    if (!karte.gruppe_id) return
    await gruppeZeitTeilen(karte.gruppe_id, !(karte.gruppe_zeit_geteilt !== false))
    await onReload?.()
  }
  function labelHinzufuegen() {
    const l = neuesLabel.trim()
    if (!l || karte.labels.includes(l)) {
      neuesLabel = ''
      return
    }
    onAendern({ labels: [...karte.labels, l] })
    neuesLabel = ''
  }
  // KI-Vorschlag fuer Labels aus Titel/Beschreibung; der Mensch waehlt per Checkliste.
  function kiLabelKontext(): Record<string, unknown> {
    return {
      titel: karte.titel,
      beschreibung: karte.beschreibung ?? '',
      vorhandene_labels: karte.labels,
      bereits_an_karte: karte.labels,
    }
  }
  function kiLabelUebernehmen(gewaehlt: KiVorschlag[]): void {
    const neue = gewaehlt.map((v) => v.id).filter((l) => l && !karte.labels.includes(l))
    if (neue.length) onAendern({ labels: [...karte.labels, ...neue] })
  }
  function labelEntfernen(l: string) {
    onAendern({ labels: karte.labels.filter((x) => x !== l) })
  }
  function kommentarSenden() {
    const t = kommentar.trim()
    if (!t) return
    onKommentar(t)
    kommentar = ''
  }
  function zeitKurz(iso: string): string {
    return isoDatumZeit(iso)
  }
  function initialen(name: string): string {
    const teile = name.trim().split(/\s+/)
    const i = (teile[0]?.[0] ?? '') + (teile[1]?.[0] ?? '')
    return (i || name.slice(0, 2)).toUpperCase()
  }
  function tage(iso?: string | null): number | null {
    if (!iso) return null
    const t = new Date(iso).getTime()
    if (Number.isNaN(t)) return null
    return Math.floor((Date.now() - t) / 86400000)
  }
  function datum(iso?: string | null): string {
    return iso ? isoLang(iso) : '-'
  }
  // -- Ticketzeit nach Tagen: alle Zeiteintraege dieser Karte (alle Tage) --
  // Ticketzeit = Summe je Karte; jeder Eintrag ist einem Tag (= Arbeitszeit) zugeordnet.
  // Korrekturen laufen ueber datierte Eintraege, damit die Arbeitszeit dem richtigen
  // Tag gutgeschrieben wird (keine undatierte Gesamt-Eingabe mehr).
  let kartenZeiten = $state<Zeiteintrag[]>([])
  async function ladeKartenZeitenFuer(): Promise<void> {
    try {
      kartenZeiten = (await ladeKartenZeiten(karte.id)).sort((a, b) => b.datum.localeCompare(a.datum))
    } catch {
      kartenZeiten = []
    }
  }
  async function zeileDatum(e: Zeiteintrag, datum: string): Promise<void> {
    if (!datum || datum === e.datum) return
    await aktualisiereZeiteintrag(e.id, { datum })
    timer.stand++
    await ladeKartenZeitenFuer()
  }
  async function zeileDauer(e: Zeiteintrag, wert: string): Promise<void> {
    const sek = parseZeit(wert)
    if (sek == null || sek === e.sekunden) return
    await aktualisiereZeiteintrag(e.id, { sekunden: Math.max(0, sek) })
    timer.stand++
    await ladeKartenZeitenFuer()
  }
  async function zeileLoeschen(e: Zeiteintrag): Promise<void> {
    await loescheZeiteintrag(e.id)
    timer.stand++
    await ladeKartenZeitenFuer()
  }

  // Zeit fuer einen beliebigen Tag nachtragen (zusaetzlich zu Start/Stopp).
  let nbDatum = $state(ymd(new Date()))
  let nbDauer = $state('')
  async function bucheTag(): Promise<void> {
    const sek = parseZeit(nbDauer)
    if (sek == null || sek <= 0) return
    await erstelleZeiteintrag({ karte_id: karte.id, datum: nbDatum, sekunden: sek })
    nbDauer = ''
    timer.stand++ // Board laedt neu -> erfasste Zeit (Ticketzeit) der Karte aktualisiert sich
    await ladeKartenZeitenFuer()
  }

  const imStatus = $derived(tage(karte.bewegt_am) ?? 0)
  const durchlauf = $derived(tage(karte.erstellt_am) ?? 0)
  const laeuft = $derived(!!karte.laeuft_seit)
  // Pausiert = diese Karte ist die aktive Sitzung, laeuft aber gerade nicht (Fortsetzen moeglich).
  const pausiert = $derived(!laeuft && timer.aktiv?.id === karte.id)
  const sek = $derived(laeuft ? erfassteSekunden(karte, timer.jetzt) : (karte.erfasst_sek ?? 0))
  const planMin = $derived(karte.schaetzung_min ?? null)
  const prozent = $derived(planMin && planMin > 0 ? (sek / 60 / planMin) * 100 : null)
  // Geteilte Zeitgruppe: kombinierte Zeit nur zur Anzeige (zaehlt einmal).
  const geteilt = $derived(!!karte.gruppe_id && karte.gruppe_zeit_geteilt !== false)
  const gruppeAnzahl = $derived((karte.gruppe_mitglieder?.length ?? 0) + 1)
  const spalteTitel = $derived(spalten.find((s) => s.id === karte.spalte)?.titel ?? '')
  const prioText: Record<string, string> = { hoch: 'Hoch', mittel: 'Mittel', niedrig: 'Niedrig' }
</script>

<div class="backdrop" role="presentation" onclick={onSchliessen}></div>
<aside class="drawer" class:vollbild aria-label="Kartendetails">
  <header>
    {#if karte.schluessel}<span class="key">{karte.schluessel}</span>{/if}
    <span class="pfad">{spalteTitel}</span>
    <span class="kopf-werkzeuge">
      <button class="mini geist" class:an={istIdee} title="Zwischen Arbeit und Idee umschalten" onclick={typUmschalten}>
        <i class="fa-{istIdee ? 'regular fa-lightbulb' : 'solid fa-briefcase'}" aria-hidden="true"></i> {istIdee ? 'Idee' : 'Arbeit'}
      </button>
      {#if !vollbild}
        <button class="mini geist" class:an={modus === 'bearbeiten'} onclick={() => (modus = modus === 'bearbeiten' ? 'lesen' : 'bearbeiten')}>
          <i class="fa-solid {modus === 'bearbeiten' ? 'fa-book-open' : 'fa-pen'}" aria-hidden="true"></i> {modus === 'bearbeiten' ? 'Lesen' : 'Bearbeiten'}
        </button>
      {/if}
      <button class="mini geist" title={vollbild ? 'Vollbild schliessen' : 'Vollbild bearbeiten'} onclick={() => { if (vollbild) bearbeitenFertig(); else vollbild = true }}>
        <i class="fa-solid {vollbild ? 'fa-compress' : 'fa-expand'}" aria-hidden="true"></i>
      </button>
      <button class="ib" aria-label="Schließen" onclick={onSchliessen}><i class="fa-solid fa-xmark" aria-hidden="true"></i></button>
    </span>
  </header>

  <div class="body" class:lesen={!bearbeiten}>
    {#if bearbeiten}
      <input class="titel" value={karte.titel} aria-label="Titel" onchange={(e) => onAendern({ titel: e.currentTarget.value })} />
    {:else}
      <button class="titel-h" title="Zum Bearbeiten klicken" onclick={zuBearbeiten}>{karte.titel}</button>
    {/if}

    <div class="sec-reihe">
      <p class="sec">Beschreibung</p>
      <span class="md-werkzeuge">
        {#if bearbeiten && gespeichert}<span class="gesp">gespeichert</span>{/if}
        {#if !bearbeiten && beschr.trim()}
          <button class="mini geist" onclick={vorlesenUmschalten}><i class="fa-solid {tts.laeuft ? 'fa-stop' : 'fa-volume-high'}" aria-hidden="true"></i> {tts.laeuft ? 'Stopp' : 'Vorlesen'}</button>
        {/if}
      </span>
    </div>
    {#if bearbeiten}
      <div class="md-split">
        <textarea class="desc" placeholder="Markdown ... (Überschriften, Listen, Code, Tabellen, $Mathe$, Mermaid)" bind:value={beschr} oninput={autoSpeichern}></textarea>
        <div class="md-vorschau"><Markdown md={beschr || '*Vorschau*'} /></div>
      </div>
    {:else if beschr.trim()}
      <button class="md-ansicht" title="Zum Bearbeiten klicken" onclick={zuBearbeiten}><Markdown md={beschr} /></button>
    {:else}
      <button class="leer-hinweis" onclick={zuBearbeiten}>Keine Beschreibung. Klicken zum Bearbeiten.</button>
    {/if}

    <p class="sec">Notizen {#if bearbeiten && notizGespeichert}<span class="gesp">gespeichert</span>{/if}</p>
    {#if bearbeiten}
      <div class="md-split">
        <textarea class="desc" placeholder="Notizen (Markdown) ..." bind:value={notiz} oninput={notizAuto}></textarea>
        <div class="md-vorschau"><Markdown md={notiz || '*Vorschau*'} /></div>
      </div>
    {:else if notiz.trim()}
      <button class="md-ansicht" title="Zum Bearbeiten klicken" onclick={zuBearbeiten}><Markdown md={notiz} /></button>
    {:else}
      <button class="leer-hinweis" onclick={zuBearbeiten}>Keine Notizen. Klicken zum Bearbeiten.</button>
    {/if}

    <div class="meta">
      <div class="zeile"><span class="lbl"><i class="fa-solid fa-list-check" aria-hidden="true"></i> Status</span>
        {#if bearbeiten}
          <select value={karte.spalte} onchange={(e) => onAendern({ spalte: e.currentTarget.value })}>
            {#each spalten as s (s.id)}<option value={s.id}>{s.titel}</option>{/each}
          </select>
        {:else}<span class="wert">{spalteTitel}</span>{/if}
      </div>
      <div class="zeile"><span class="lbl"><i class="fa-solid fa-flag" aria-hidden="true"></i> Priorität</span>
        {#if bearbeiten}
          <select value={karte.prioritaet ?? ''} onchange={(e) => onAendern({ prioritaet: (e.currentTarget.value || null) as Prioritaet | null })}>
            <option value="">keine</option>
            <option value="hoch">Hoch</option>
            <option value="mittel">Mittel</option>
            <option value="niedrig">Niedrig</option>
          </select>
        {:else}<span class="wert">{karte.prioritaet ? prioText[karte.prioritaet] : '-'}</span>{/if}
      </div>
      <div class="zeile"><span class="lbl"><i class="fa-solid fa-play" aria-hidden="true"></i> Start</span>
        {#if bearbeiten}
          <input type="date" value={karte.start ?? ''} onchange={(e) => onAendern({ start: e.currentTarget.value || null })} />
        {:else}<span class="wert">{datum(karte.start)}</span>{/if}
      </div>
      <div class="zeile"><span class="lbl"><i class="fa-solid fa-calendar" aria-hidden="true"></i> Fällig</span>
        {#if bearbeiten}
          <input type="date" value={karte.faellig ?? ''} onchange={(e) => onAendern({ faellig: e.currentTarget.value || null })} />
        {:else}<span class="wert">{datum(karte.faellig)}</span>{/if}
      </div>
      <div class="zeile"><span class="lbl"><i class="fa-solid fa-user" aria-hidden="true"></i> Zuständig</span>
        {#if bearbeiten}
          <select value={karte.zustaendig ?? ''} onchange={(e) => zustaendigSetzen(e.currentTarget.value)}>
            <option value="">(niemand)</option>
            {#each kuerzelWahl as p (p.id)}<option value={p.kuerzel}>{p.kuerzel} - {p.name}</option>{/each}
          </select>
        {:else}<span class="wert">{karte.zustaendig || '(niemand)'}</span>{/if}
      </div>
      <div class="zeile"><span class="lbl"><i class="fa-solid fa-palette" aria-hidden="true"></i> Cover</span>
        {#if bearbeiten}
          <FarbWahl value={karte.cover ?? null} onWahl={(c) => onAendern({ cover: c })} />
        {:else if karte.cover}<span class="cswatch" style="background:{karte.cover}"></span>{:else}<span class="wert">-</span>{/if}
      </div>
    </div>

    <div class="zeiten">
      <span class:warn={imStatus >= 8}><i class="fa-solid fa-hourglass-half" aria-hidden="true"></i> Im Status: {imStatus} Tage</span>
      <span><i class="fa-solid fa-stopwatch" aria-hidden="true"></i> Durchlaufzeit: {durchlauf} Tage</span>
      <span><i class="fa-regular fa-calendar-plus" aria-hidden="true"></i> Erstellt: {datum(karte.erstellt_am)}</span>
    </div>

    {#if istIdee}
      <p class="idee-hinweis"><i class="fa-regular fa-lightbulb" aria-hidden="true"></i> Ideenticket - keine Zeiterfassung. Auf "Arbeit" umschalten, um Zeit zu buchen.</p>
    {:else}
      <p class="sec">Zeiterfassung</p>
      <div class="timer">
        {#if laeuft}
          <button class="tbtn an" onclick={() => timerPausieren(karte.id)}><i class="fa-solid fa-pause" aria-hidden="true"></i> Pause</button>
          <button class="tbtn stopp" onclick={() => timerStoppen(karte.id)}><i class="fa-solid fa-stop" aria-hidden="true"></i> Stopp</button>
        {:else if pausiert}
          <button class="tbtn play" onclick={() => timerStarten(karte.id)}><i class="fa-solid fa-play" aria-hidden="true"></i> Fortsetzen</button>
          <button class="tbtn stopp" onclick={() => timerStoppen(karte.id)}><i class="fa-solid fa-stop" aria-hidden="true"></i> Stopp</button>
        {:else}
          <button class="tbtn play" onclick={() => timerStarten(karte.id)}><i class="fa-solid fa-play" aria-hidden="true"></i> Start</button>
        {/if}
        <span class="erfasst" title="Ticketzeit gesamt (Summe aller Tage)">{formatDauerVoll(sek)}</span>
        <label class="plan">Schätzung
          <input type="number" min="0" step="0.25" value={planMin ? planMin / 60 : ''}
            onchange={(e) => { const v = parseFloat(e.currentTarget.value); onAendern({ schaetzung_min: Number.isFinite(v) && v > 0 ? Math.round(v * 60) : null }) }} />
          Std
        </label>
      </div>
      {#if geteilt}
        <p class="grpzeit"><i class="fa-solid fa-link" aria-hidden="true"></i> Geteilt über {gruppeAnzahl} Aufgaben: {formatDauerVoll(karte.gruppe_sek ?? 0)} - zählt einmal</p>
      {/if}
      <p class="zcap">Ticketzeit gesamt (Summe aller Tage). Die Tage darunter bilden die Arbeitszeit des jeweiligen Tages.</p>
      {#if prozent != null}
        <div class="fortschritt" class:ueber={prozent > 100}><span style="width:{Math.min(prozent, 100)}%"></span></div>
        <div class="pinfo" class:ueber={prozent > 100}>{Math.round(prozent)}% von {formatPlan(planMin ?? 0)}{#if prozent > 100} - überschritten{/if}</div>
      {/if}
      <div class="tagbuchung">
        <input type="date" bind:value={nbDatum} aria-label="Datum für Nachtrag" />
        <input class="tbdauer" placeholder="z.B. 0:30 oder 1,5" bind:value={nbDauer} aria-label="Dauer"
          onkeydown={(e) => { if (e.key === 'Enter') bucheTag() }} />
        <button class="mini" onclick={bucheTag}>Tag buchen</button>
      </div>
      <p class="taginfo">Zeit für einen beliebigen Tag nachtragen (zusätzlich zu Start/Stopp).</p>
      {#if kartenZeiten.length}
        <div class="tageliste">
          {#each kartenZeiten as e (e.id)}
            <div class="tagrow">
              <input type="date" value={e.datum} onchange={(ev) => zeileDatum(e, ev.currentTarget.value)} aria-label="Tag des Eintrags" />
              <input class="trdauer" value={formatDauerVoll(e.sekunden)} onchange={(ev) => zeileDauer(e, ev.currentTarget.value)} aria-label="Dauer" title="Dauer (z.B. 1:30:00 oder 1,5)" />
              {#if !e.manuell}<span class="trauto" title="Aus Start/Stopp"><i class="fa-solid fa-stopwatch" aria-hidden="true"></i></span>{/if}
              <button class="ic" aria-label="Eintrag löschen" onclick={() => zeileLoeschen(e)}><i class="fa-solid fa-xmark" aria-hidden="true"></i></button>
            </div>
          {/each}
        </div>
      {/if}

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
    {/if}

    <p class="sec">Labels <span class="sec-ki"><KiAssistent typ="labels" titel="Labels vorschlagen" platzhalter="Worauf achten? (optional)" uebernehmenText="Hinzufuegen" kontext={kiLabelKontext} onUebernehmen={kiLabelUebernehmen} /></span></p>
    <div class="labels">
      {#each karte.labels as l (l)}
        {@const f = labelFarbe(l, dunkel)}
        <span class="lab" style="background:{f.bg};color:{f.fg}">{l}<button aria-label="Label entfernen" onclick={() => labelEntfernen(l)}><i class="fa-solid fa-xmark" aria-hidden="true"></i></button></span>
      {/each}
      <input class="labinput" placeholder="+ Label" bind:value={neuesLabel} onkeydown={(e) => { if (e.key === 'Enter') labelHinzufuegen() }} onblur={labelHinzufuegen} />
    </div>

    <p class="sec">Checkliste {#if karte.checkliste.length}<span class="dezent">&middot; {erledigt} von {karte.checkliste.length}</span>{/if}</p>
    {#if karte.checkliste.length}
      <div class="chkbar"><span style="width:{(erledigt / karte.checkliste.length) * 100}%"></span></div>
    {/if}
    {#each karte.checkliste as punkt, i (i)}
      <div class="chk" class:done={punkt.erledigt}>
        <button class="box" aria-label="Umschalten" onclick={() => punktUmschalten(i)}>
          <i class="fa-{punkt.erledigt ? 'solid fa-square-check' : 'regular fa-square'}" aria-hidden="true"></i>
        </button>
        {#if punktEdit === i}
          <!-- svelte-ignore a11y_autofocus -->
          <input class="chkedit" value={punkt.text} autofocus aria-label="Punkt-Text"
            onblur={(e) => punktText(i, e.currentTarget.value)}
            onkeydown={(e) => { if (e.key === 'Enter') e.currentTarget.blur(); else if (e.key === 'Escape') punktEdit = null }} />
        {:else}
          <button class="chktext" title="Zum Umbenennen klicken" onclick={() => (punktEdit = i)}>{punkt.text}</button>
        {/if}
        <button class="del" aria-label="Punkt entfernen" onclick={() => punktEntfernen(i)}><i class="fa-solid fa-xmark" aria-hidden="true"></i></button>
      </div>
    {/each}
    <input class="feld" placeholder="+ Punkt hinzufügen" bind:value={neuerPunkt} onkeydown={(e) => { if (e.key === 'Enter') punktHinzufuegen() }} />

    <p class="sec">Dokumente</p>
    <DokumentVerwaltung kontext="karte" kontextId={karte.id} />

    <p class="sec">Transkript</p>
    {#if karte.transkript_id}
      <div class="tlink">
        <i class="fa-solid fa-headphones" aria-hidden="true"></i>
        <span class="tname">{karte.transkript_name ?? 'Verknüpftes Transkript'}</span>
        <button class="mini geist" onclick={() => oeffneTranskript(karte.transkript_id!)}>Öffnen</button>
        <button class="ic" aria-label="Verknüpfung entfernen" onclick={transkriptEntfernen}><i class="fa-solid fa-xmark" aria-hidden="true"></i></button>
      </div>
    {:else}
      <input class="feld" placeholder="Transkript suchen und verknüpfen ..." bind:value={tSuche} oninput={tSuchen} />
      {#if tTreffer.length}
        <div class="ttreffer">
          {#each tTreffer as t (t.id)}
            <button class="ttr" onclick={() => transkriptVerknuepfen(t)}><i class="fa-regular fa-file-audio" aria-hidden="true"></i> <span>{t.name}</span></button>
          {/each}
        </div>
      {/if}
    {/if}

    <p class="sec">Transkript-Verweise</p>
    {#each marken as m (m.id)}
      <div class="marke">
        <div class="mkopf">
          <i class="fa-solid fa-headphones" aria-hidden="true"></i>
          <span class="mname">{m.titel || m.transkript_name || 'Transkript'}</span>
          {#if m.position_sek != null}<span class="mzeit">{mmss(m.position_sek)}</span>{/if}
          {#if m.sprecher}<span class="mspk">{m.sprecher}</span>{/if}
          <button class="mini geist" onclick={() => markeOeffnen(m)}><i class="fa-solid fa-arrow-up-right-from-square" aria-hidden="true"></i> Öffnen</button>
          <button class="ic" aria-label="Verweis entfernen" onclick={() => markeLoeschen(m)}><i class="fa-solid fa-xmark" aria-hidden="true"></i></button>
        </div>
        {#if m.segment_text}<div class="mseg">{m.segment_text}</div>{/if}
        <textarea class="mzus" rows="2" placeholder="Zusammenfassung dieses Abschnitts ..." value={m.zusammenfassung ?? ''} oninput={(e) => zusAendern(m, e.currentTarget.value)}></textarea>
        <div class="mreihe">
          <button class="mini geist" disabled={kiLaeuft === m.id} onclick={() => kiVorschlag(m)}>
            <i class="fa-solid fa-wand-magic-sparkles" aria-hidden="true"></i> {kiLaeuft === m.id ? 'erzeugt ...' : 'KI-Vorschlag'}
          </button>
          {#if kiFehler[m.id]}<span class="mfehler">{kiFehler[m.id]}</span>{/if}
        </div>
        {#if kiVorschau[m.id] != null}
          <div class="kivorschau">
            <div class="kitext">{kiVorschau[m.id]}</div>
            <div class="mreihe">
              <button class="mini" onclick={() => kiUebernehmen(m)}>Übernehmen</button>
              <button class="mini geist" onclick={() => kiVerwerfen(m)}>Verwerfen</button>
            </div>
          </div>
        {/if}
      </div>
    {/each}
    <input class="feld" placeholder="Transkript suchen und als Verweis anhängen ..." bind:value={mSuche} oninput={mSuchen} />
    {#if mTreffer.length}
      <div class="ttreffer">
        {#each mTreffer as t (t.id)}
          <button class="ttr" onclick={() => markeHinzufuegen(t)}><i class="fa-regular fa-file-audio" aria-hidden="true"></i> <span>{t.name}</span></button>
        {/each}
      </div>
    {/if}

    <p class="sec">Aktivität</p>
    {#each karte.kommentare as k (k.zeit + k.autor)}
      <div class="cmt"><span class="av">{initialen(k.autor)}</span><div class="ct"><b>{k.autor}</b> <span class="zeit">{zeitKurz(k.zeit)}</span><button class="cmt-vor" aria-label="Kommentar vorlesen" title="Vorlesen" onclick={() => vorlesen(k.text)}><i class="fa-solid fa-volume-high" aria-hidden="true"></i></button><div class="cmt-md"><Markdown md={k.text} /></div></div></div>
    {/each}
    <div class="cmtinput">
      <input placeholder="Kommentar schreiben ..." bind:value={kommentar} onkeydown={(e) => { if (e.key === 'Enter') kommentarSenden() }} />
      <button class="btn primaer" onclick={kommentarSenden}>Senden</button>
    </div>

    <div class="fuss">
      <button class="btn geist rot" onclick={onLoeschen}><i class="fa-solid fa-trash" aria-hidden="true"></i> Karte löschen</button>
    </div>
  </div>
</aside>

<style>
  .backdrop {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.45);
    z-index: 40;
  }
  .drawer {
    position: fixed;
    top: 0;
    right: 0;
    bottom: 0;
    width: 540px;
    max-width: 94vw;
    z-index: 41;
    background: var(--surface-col);
    border-left: 1px solid var(--border-2);
    box-shadow: var(--schatten-pop);
    display: flex;
    flex-direction: column;
  }
  header {
    display: flex;
    align-items: center;
    gap: 9px;
    padding: 12px 14px;
    border-bottom: 1px solid var(--border);
  }
  .key {
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--hl-primary-text);
    background: var(--hl-primary-weich);
    padding: 2px 7px;
    border-radius: var(--r-s);
  }
  .pfad {
    font-size: 11px;
    color: var(--text-3);
  }
  .ib {
    width: 28px;
    height: 28px;
    border-radius: var(--r-s);
    border: 1px solid var(--border);
    background: var(--surface-2);
    color: var(--text-2);
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .ib:hover {
    color: var(--text-1);
  }
  .body {
    padding: 14px;
    overflow-y: auto;
  }
  .titel {
    width: 100%;
    border: 1px solid transparent;
    background: transparent;
    color: var(--text-1);
    font-size: 17px;
    font-weight: 600;
    font-family: var(--font-display);
    border-radius: var(--r-m);
    padding: 6px 8px;
    margin: 0 0 12px -8px;
  }
  .titel:hover {
    border-color: var(--border);
  }
  .titel:focus {
    border-color: var(--hl-primary);
    background: var(--surface-2);
    outline: none;
  }
  .zeile {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 8px;
  }
  .lbl {
    width: 96px;
    flex: none;
    color: var(--text-3);
    font-size: 12px;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .zeile select,
  .zeile input {
    flex: 1;
    min-width: 0;
    border: 1px solid var(--border);
    background: var(--surface-2);
    color: var(--text-1);
    border-radius: var(--r-m);
    padding: 6px 9px;
    font-size: 12.5px;
  }
  .zeiten {
    display: flex;
    flex-wrap: wrap;
    gap: 14px;
    margin-top: 12px;
    padding: 9px 11px;
    background: var(--surface-2);
    border: 1px solid var(--border);
    border-radius: var(--r-m);
    font-size: 11.5px;
    color: var(--text-2);
  }
  .zeiten span {
    display: inline-flex;
    align-items: center;
    gap: 6px;
  }
  .zeiten .warn {
    color: var(--due-rot-fg);
  }
  .timer {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .tbtn {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    border: 1px solid var(--hl-primary);
    background: var(--hl-primary);
    color: var(--hl-on-primary);
    border-radius: var(--r-m);
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 600;
  }
  .tbtn.an {
    background: var(--surface-2);
    color: var(--hl-primary-text);
  }
  .tbtn.stopp {
    background: var(--surface-1);
    color: var(--text-2);
    border-color: var(--border-2);
  }
  .tbtn.stopp:hover {
    border-color: var(--gefahr);
    color: var(--due-rot-fg);
  }
  .erfasst {
    font-family: var(--font-mono);
    font-size: 18px;
    font-variant-numeric: tabular-nums;
    color: var(--text-1);
  }
  .zcap {
    font-size: 10.5px;
    color: var(--text-3);
    margin: 6px 0 0;
  }
  .tageliste {
    display: flex;
    flex-direction: column;
    gap: 5px;
    margin-top: 8px;
  }
  .tagrow {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .tagrow input[type='date'] {
    border: 1px solid var(--border);
    background: var(--surface-2);
    color: var(--text-1);
    border-radius: var(--r-s);
    padding: 5px 8px;
    font-size: 12.5px;
  }
  .trdauer {
    width: 96px;
    border: 1px solid var(--border);
    background: var(--surface-2);
    color: var(--text-1);
    border-radius: var(--r-s);
    padding: 5px 8px;
    font-size: 12.5px;
    font-variant-numeric: tabular-nums;
  }
  .trauto {
    color: var(--text-3);
    font-size: 11px;
  }
  .plan {
    margin-left: auto;
    font-size: 12px;
    color: var(--text-3);
    display: inline-flex;
    align-items: center;
    gap: 6px;
  }
  .plan input {
    width: 60px;
    border: 1px solid var(--border);
    background: var(--surface-2);
    color: var(--text-1);
    border-radius: var(--r-s);
    padding: 5px 7px;
    font-size: 12.5px;
  }
  .fortschritt {
    height: 7px;
    border-radius: 5px;
    background: var(--border);
    overflow: hidden;
    margin: 10px 0 5px;
  }
  .fortschritt span {
    display: block;
    height: 100%;
    background: var(--hl-primary);
  }
  .fortschritt.ueber span {
    background: var(--gefahr);
  }
  .pinfo {
    font-size: 12px;
    color: var(--text-3);
  }
  .pinfo.ueber {
    color: var(--due-rot-fg);
    font-weight: 600;
  }
  .tagbuchung {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 10px;
  }
  .tagbuchung input[type='date'] {
    border: 1px solid var(--border);
    background: var(--surface-2);
    color: var(--text-1);
    border-radius: var(--r-s);
    padding: 6px 8px;
    font-size: 12.5px;
  }
  .tbdauer {
    flex: 1;
    min-width: 0;
    border: 1px solid var(--border);
    background: var(--surface-2);
    color: var(--text-1);
    border-radius: var(--r-s);
    padding: 6px 8px;
    font-size: 12.5px;
  }
  .taginfo {
    font-size: 10.5px;
    color: var(--text-3);
    margin: 4px 0 0;
  }
  .sec {
    font-family: var(--font-display);
    font-size: 10.5px;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: var(--text-3);
    margin: 18px 0 8px;
  }
  .sec-ki {
    float: right;
    margin-top: -5px;
    text-transform: none;
    letter-spacing: normal;
  }
  .dezent {
    color: var(--text-3);
    text-transform: none;
    letter-spacing: 0;
  }
  .labels {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    align-items: center;
  }
  .lab {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 11.5px;
    padding: 2px 4px 2px 9px;
    border-radius: var(--r-s);
    font-weight: 500;
  }
  .lab button {
    border: none;
    background: transparent;
    color: inherit;
    opacity: 0.7;
    font-size: 10px;
    padding: 0 2px;
  }
  .labinput {
    border: 1px dashed var(--border-2);
    background: transparent;
    color: var(--text-2);
    border-radius: var(--r-s);
    padding: 3px 8px;
    font-size: 12px;
    width: 78px;
  }
  .desc {
    width: 100%;
    border: 1px solid var(--border);
    background: var(--surface-2);
    color: var(--text-1);
    border-radius: var(--r-m);
    padding: 9px 10px;
    font-size: 12.5px;
    line-height: 1.5;
    resize: vertical;
  }
  .chkbar {
    height: 5px;
    border-radius: 4px;
    background: var(--border);
    overflow: hidden;
    margin-bottom: 9px;
  }
  .chkbar span {
    display: block;
    height: 100%;
    background: var(--ok);
  }
  .chk {
    display: flex;
    align-items: center;
    gap: 9px;
    font-size: 12.5px;
    color: var(--text-1);
    padding: 4px 0;
  }
  .chk.done .chktext {
    color: var(--text-3);
    text-decoration: line-through;
  }
  .chk .box {
    border: none;
    background: transparent;
    color: var(--text-2);
    font-size: 15px;
    padding: 0;
  }
  .chk.done .box {
    color: var(--ok);
  }
  .chk .del {
    border: none;
    background: transparent;
    color: var(--text-3);
    font-size: 11px;
    opacity: 0;
  }
  .chk:hover .del {
    opacity: 1;
  }
  .feld {
    width: 100%;
    border: 1px solid var(--border);
    background: var(--surface-2);
    color: var(--text-1);
    border-radius: var(--r-m);
    padding: 7px 9px;
    font-size: 12.5px;
    margin-top: 6px;
  }
  .cmt {
    display: flex;
    gap: 9px;
    margin-bottom: 11px;
  }
  .av {
    width: 24px;
    height: 24px;
    flex: none;
    border-radius: 50%;
    background: var(--hl-primary-weich);
    color: var(--hl-primary-text);
    font-size: 10px;
    font-weight: 600;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .ct {
    font-size: 12.5px;
    color: var(--text-1);
  }
  .ct b {
    font-weight: 500;
  }
  .ct .zeit {
    color: var(--text-3);
    font-size: 10.5px;
    margin-left: 6px;
  }
  .cmt-vor {
    border: none;
    background: transparent;
    color: var(--text-3);
    font-size: 10.5px;
    padding: 0 4px;
    margin-left: 4px;
  }
  .cmt-vor:hover {
    color: var(--hl-primary-text);
  }
  .tlink {
    display: flex;
    align-items: center;
    gap: 9px;
    border: 1px solid var(--border);
    background: var(--surface-2);
    border-radius: var(--r-m);
    padding: 8px 10px;
    font-size: 12.5px;
    color: var(--text-1);
  }
  .tlink .tname {
    flex: 1;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .ttreffer {
    display: flex;
    flex-direction: column;
    gap: 3px;
    margin-top: 5px;
  }
  .ttr {
    display: flex;
    align-items: center;
    gap: 8px;
    text-align: left;
    border: 1px solid var(--border);
    background: var(--surface-2);
    color: var(--text-1);
    border-radius: var(--r-m);
    padding: 7px 10px;
    font-size: 12.5px;
  }
  .ttr span {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .ttr:hover {
    border-color: var(--hl-primary);
  }
  .marke {
    border: 1px solid var(--border);
    background: var(--surface-2);
    border-radius: var(--r-m);
    padding: 9px 10px;
    margin-bottom: 7px;
    display: flex;
    flex-direction: column;
    gap: 7px;
  }
  .mkopf {
    display: flex;
    align-items: center;
    gap: 8px;
    color: var(--text-1);
    font-size: 12.5px;
  }
  .mname {
    flex: 1;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-weight: 500;
  }
  .mzeit {
    font-family: var(--font-mono);
    font-size: 10.5px;
    color: var(--hl-primary-text);
    background: var(--hl-primary-weich);
    padding: 1px 6px;
    border-radius: var(--r-s);
  }
  .mspk {
    font-size: 10.5px;
    color: var(--text-3);
    white-space: nowrap;
  }
  .mseg {
    font-size: 11.5px;
    color: var(--text-2);
    line-height: 1.45;
    background: var(--surface-1);
    border-radius: var(--r-s);
    padding: 5px 8px;
  }
  .mzus {
    width: 100%;
    border: 1px solid var(--border);
    background: var(--surface-1);
    color: var(--text-1);
    border-radius: var(--r-s);
    padding: 6px 8px;
    font-size: 12px;
    line-height: 1.45;
    resize: vertical;
  }
  .mreihe {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .mfehler {
    font-size: 10.5px;
    color: var(--due-rot-fg);
  }
  .kivorschau {
    border: 1px dashed var(--hl-primary);
    background: var(--hl-primary-weich);
    border-radius: var(--r-s);
    padding: 7px 9px;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  .kitext {
    font-size: 12px;
    line-height: 1.5;
    color: var(--text-1);
  }
  .ct .cmt-md {
    margin: 3px 0 0;
    color: var(--text-2);
    line-height: 1.45;
  }
  .cmtinput {
    display: flex;
    gap: 7px;
    margin-top: 4px;
  }
  .cmtinput input {
    flex: 1;
    min-width: 0;
    border: 1px solid var(--border);
    background: var(--surface-2);
    color: var(--text-1);
    border-radius: var(--r-m);
    padding: 8px 10px;
    font-size: 12.5px;
  }
  .btn {
    border: 1px solid var(--border);
    border-radius: var(--r-m);
    padding: 7px 12px;
    font-size: 12.5px;
    white-space: nowrap;
  }
  .btn.primaer {
    background: var(--hl-primary);
    color: var(--hl-on-primary);
    border-color: transparent;
    font-weight: 500;
  }
  .btn.geist {
    background: transparent;
    color: var(--text-2);
  }
  .btn.geist.rot {
    color: var(--gefahr);
  }
  .fuss {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 22px;
    padding-top: 14px;
    border-top: 1px solid var(--border);
  }

  /* -- Markdown-Beschreibung -- */
  .sec-reihe {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
  }
  .md-werkzeuge {
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .gesp {
    font-size: 10.5px;
    color: var(--ok);
  }
  .mini {
    border: 1px solid var(--hl-primary);
    background: var(--hl-primary);
    color: var(--hl-on-primary);
    border-radius: var(--r-s);
    padding: 4px 9px;
    font-size: 11.5px;
    white-space: nowrap;
  }
  .mini.geist {
    background: transparent;
    color: var(--text-2);
    border-color: var(--border-2);
  }
  .md-ansicht {
    display: block;
    width: 100%;
    text-align: left;
    background: var(--surface-2);
    border: 1px solid var(--border);
    border-radius: var(--r-m);
    padding: 10px 11px;
    cursor: text;
  }
  .md-ansicht:hover {
    border-color: var(--border-2);
  }
  .leer-hinweis {
    display: block;
    width: 100%;
    text-align: left;
    background: transparent;
    border: 1px dashed var(--border-2);
    border-radius: var(--r-m);
    padding: 10px 11px;
    color: var(--text-3);
    font-size: 12.5px;
  }
  .md-split {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    margin-bottom: 4px;
  }
  .md-split .desc {
    min-height: 120px;
  }
  .md-vorschau {
    border: 1px solid var(--border);
    background: var(--surface-2);
    border-radius: var(--r-m);
    padding: 9px 10px;
    overflow-y: auto;
    max-height: 320px;
  }
  .cmt-md {
    font-size: 12.5px;
  }

  /* -- Lese-/Bearbeitungsmodus + Vollbild -- */
  .kopf-werkzeuge {
    margin-left: auto;
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .mini.an {
    background: var(--hl-primary-weich);
    color: var(--hl-primary-text);
    border-color: var(--hl-primary);
  }
  .titel-h {
    display: block;
    width: 100%;
    text-align: left;
    border: none;
    background: transparent;
    font-family: var(--font-display);
    font-size: 18px;
    font-weight: 600;
    color: var(--text-1);
    margin: 0 0 12px;
    line-height: 1.3;
    cursor: text;
  }
  .md-ansicht :global(.md-body) {
    font-size: 13px;
  }
  /* Vollbild: ganzes Ticket im Bearbeitungsmodus, breit und ruhig. */
  .drawer.vollbild {
    width: 100vw;
    max-width: 100vw;
    border-left: none;
  }
  .drawer.vollbild .body {
    max-width: 1100px;
    width: 100%;
    margin: 0 auto;
  }
  .drawer.vollbild .md-split {
    grid-template-columns: 1fr 1fr;
  }
  .drawer.vollbild .md-split .desc {
    min-height: 240px;
    font-size: 15px;
    line-height: 1.6;
  }
  .drawer.vollbild .md-vorschau {
    max-height: 360px;
  }

  /* -- Kompaktes, einheitliches Meta-Raster -- */
  .meta {
    margin: 4px 0 12px;
  }
  .wert {
    flex: 1;
    color: var(--text-1);
    font-size: 12.5px;
  }
  .cswatch {
    width: 30px;
    height: 16px;
    border-radius: var(--r-s);
    border: 1px solid var(--border-2);
  }

  /* -- Ideenticket / Zeitgruppe -- */
  .idee-hinweis {
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 10px 0;
    padding: 8px 11px;
    border: 1px solid var(--border-2);
    background: var(--surface-2);
    border-radius: var(--r-m);
    color: var(--text-2);
    font-size: 12px;
  }
  .grpzeit {
    margin: 2px 0 0;
    font-size: 11.5px;
    color: var(--hl-primary-text);
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .vliste {
    display: flex;
    flex-direction: column;
    gap: 4px;
    margin-bottom: 6px;
  }
  .vlink {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    width: 100%;
    text-align: left;
    border: 1px solid var(--border);
    background: var(--surface-2);
    color: var(--text-1);
    border-radius: var(--r-s);
    padding: 6px 9px;
    font-size: 12px;
  }
  .vlink:hover {
    border-color: var(--hl-primary);
  }
  .vkey {
    font-family: var(--font-mono);
    font-size: 10px;
    color: var(--text-3);
  }
  .vtitel {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .grpschalter {
    display: flex;
    align-items: center;
    gap: 7px;
    font-size: 12px;
    color: var(--text-2);
    margin: 2px 0 8px;
  }

  /* -- Checkliste: Inline-Umbenennen -- */
  .chktext {
    flex: 1;
    cursor: text;
    border: none;
    background: transparent;
    color: inherit;
    font: inherit;
    text-align: left;
    padding: 0;
  }
  .chkedit {
    flex: 1;
    border: 1px solid var(--hl-primary);
    background: var(--surface-2);
    color: var(--text-1);
    border-radius: var(--r-s);
    padding: 3px 6px;
    font-size: 12.5px;
  }
</style>
