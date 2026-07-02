<script lang="ts">
  import type { Aktivitaet, Anhang, Karte, Prioritaet, Spalte } from '../../types'
  import type { KarteAenderung, TranskriptTreffer, Person, KiVorschlag } from '../../api'
  import { transkripteSuche, ladePersonen, ladeKartenAktivitaet, ladeAnhaenge, anhangHochladen, anhangLoeschen, anhangHerunterladen, checklistePunktNeu, checklistePunktAendern, checklistePunktLoeschen } from '../../api'
  import KiAssistent from '../../ki/KiAssistent.svelte'
  import Checkliste from './Checkliste.svelte'
  import TranskriptVerweise from './TranskriptVerweise.svelte'
  import Zeiterfassung from './Zeiterfassung.svelte'
  import VerknuepfteAufgaben from './VerknuepfteAufgaben.svelte'
  import MarkdownFeld from './MarkdownFeld.svelte'
  import { merkeKuerzel } from '../../zuletztKuerzel.svelte'
  import { oeffneTranskript } from '../../navigation.svelte'
  import { labelFarbe } from '../../labels'
  import { theme } from '../../theme/theme.svelte'
  import { isoLang, isoDatumZeit } from '../../zeit'
  import Markdown from '../../Markdown.svelte'
  import FarbWahl from '../../FarbWahl.svelte'
  import DokumentVerwaltung from '../../DokumentVerwaltung.svelte'
  import { tts, vorlesen, stoppeVorlesen } from '../../tts.svelte'

  let {
    karte,
    spalten,
    boardKarten = [],
    onSchliessen,
    onDuplizieren,
    onKarteAktualisiert,
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
    onDuplizieren?: () => void
    onKarteAktualisiert?: (k: Karte) => void
    onAendern: (daten: KarteAenderung) => void | Promise<void>
    onKommentar: (text: string) => void
    onLoeschen: () => void
    onReload?: () => void | Promise<void>
    onOeffneKarte?: (id: string) => void
  } = $props()

  const dunkel = $derived(theme.modus === 'dunkel')

  // Arbeit vs. Idee (Notiz ohne Zeiterfassung).
  const istIdee = $derived(karte.typ === 'idee')
  function typUmschalten(): void { onAendern({ typ: istIdee ? 'arbeit' : 'idee' }) }
  const istBlockiert = $derived(!!karte.blockiert_grund)
  function blockiertUmschalten(): void {
    onAendern({ blockiert_grund: istBlockiert ? null : 'Grund noch offen' })
  }

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

  let neuesLabel = $state('')
  let kommentar = $state('')

  // Checklisten-Einzeloperationen: das Backend schreibt atomar; ein 409
  // (Liste hat sich parallel geaendert) laedt einfach frisch nach.
  async function checklisteOp(p: Promise<Karte>): Promise<void> {
    try {
      onKarteAktualisiert?.(await p)
    } catch {
      await onReload?.()
    }
  }

  // Datei-Anhaenge der Karte.
  let anhaenge = $state<Anhang[]>([])
  let anhangFehler = $state('')
  let anhangLaeuft = $state(false)
  let dateiwahl = $state<HTMLInputElement | null>(null)
  $effect(() => {
    void karte.id
    anhangFehler = ''
    ladeAnhaenge(karte.id).then((a) => (anhaenge = a)).catch(() => (anhaenge = []))
  })
  async function anhaengeHochladen(dateien: FileList | null): Promise<void> {
    if (!dateien?.length) return
    anhangFehler = ''
    anhangLaeuft = true
    try {
      for (const d of Array.from(dateien)) await anhangHochladen(karte.id, d)
      anhaenge = await ladeAnhaenge(karte.id)
    } catch (e) {
      anhangFehler = e instanceof Error ? e.message : 'Hochladen fehlgeschlagen'
    } finally {
      anhangLaeuft = false
      if (dateiwahl) dateiwahl.value = ''
    }
  }
  async function anhangEntfernen(a: Anhang): Promise<void> {
    await anhangLoeschen(a.id)
    anhaenge = anhaenge.filter((x) => x.id !== a.id)
  }
  function groesseText(bytes: number): string {
    if (bytes >= 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`
    if (bytes >= 1024) return `${Math.round(bytes / 1024)} KB`
    return `${bytes} B`
  }

  // Verlauf (Aktivitaetsprotokoll): erst auf Wunsch laden, nicht bei jedem Oeffnen.
  let verlaufOffen = $state(false)
  let verlauf = $state<Aktivitaet[]>([])
  async function verlaufUmschalten(): Promise<void> {
    verlaufOffen = !verlaufOffen
    if (verlaufOffen) {
      try {
        verlauf = await ladeKartenAktivitaet(karte.id)
      } catch {
        verlauf = []
      }
    }
  }
  $effect(() => {
    // Kartenwechsel im offenen Drawer: alten Verlauf nicht stehen lassen.
    void karte.id
    verlaufOffen = false
    verlauf = []
  })
  function verlaufWann(a: Aktivitaet): string {
    return `${a.zeit.slice(8, 10)}.${a.zeit.slice(5, 7)}.${a.zeit.slice(0, 4)} ${a.zeit.slice(11, 16)}`
  }

  // Vorlesen der Beschreibung umschalten (an MarkdownFeld weitergereicht).
  function vorlesenUmschalten(t: string): void {
    if (tts.laeuft) stoppeVorlesen()
    else vorlesen(t)
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

  const imStatus = $derived(tage(karte.bewegt_am) ?? 0)
  const durchlauf = $derived(tage(karte.erstellt_am) ?? 0)
  const spalteTitel = $derived(spalten.find((s) => s.id === karte.spalte)?.titel ?? '')

  // Beim Oeffnen den Fokus in den Drawer holen, damit Tab nicht durch das
  // Board hinter dem Backdrop wandert.
  function fokusBeimOeffnen(el: HTMLElement) {
    el.focus()
  }
</script>

<!-- Escape schliesst den Drawer; steckt der Fokus in einem Eingabefeld, beendet
     der erste Escape nur die Eingabe (blur), der zweite schliesst. -->
<svelte:window onkeydown={(e) => {
  if (e.key !== 'Escape') return
  const ziel = e.target as HTMLElement | null
  if (ziel && (ziel.tagName === 'INPUT' || ziel.tagName === 'TEXTAREA' || ziel.isContentEditable)) {
    ziel.blur()
    return
  }
  onSchliessen()
}} />
<div class="backdrop" role="presentation" onclick={onSchliessen}></div>
<aside class="drawer" aria-label="Kartendetails" tabindex="-1" use:fokusBeimOeffnen>
  <header>
    {#if karte.schluessel}<span class="key">{karte.schluessel}</span>{/if}
    <span class="pfad">{spalteTitel}</span>
    <span class="kopf-werkzeuge">
      <button class="mini geist" class:an={istIdee} title="Zwischen Arbeit und Idee umschalten" onclick={typUmschalten}>
        <i class="fa-{istIdee ? 'regular fa-lightbulb' : 'solid fa-briefcase'}" aria-hidden="true"></i> {istIdee ? 'Idee' : 'Arbeit'}
      </button>
      <button class="mini geist" class:blockiert={istBlockiert} title={istBlockiert ? 'Blockade aufheben' : 'Als blockiert markieren'} onclick={blockiertUmschalten}>
        <i class="fa-solid fa-hand" aria-hidden="true"></i> {istBlockiert ? 'Blockiert' : 'Frei'}
      </button>
      {#if onDuplizieren}
        <button class="mini geist" title="Karte als Kopiervorlage duplizieren (ohne Zeiten, Checkliste zurückgesetzt)" onclick={onDuplizieren}>
          <i class="fa-solid fa-copy" aria-hidden="true"></i>
        </button>
      {/if}
      <button class="ib" aria-label="Schließen" onclick={onSchliessen}><i class="fa-solid fa-xmark" aria-hidden="true"></i></button>
    </span>
  </header>

  <div class="body">
    <input class="titel" value={karte.titel} aria-label="Titel" onchange={(e) => onAendern({ titel: e.currentTarget.value })} />
    {#if istBlockiert}
      <label class="blockiert-grund">
        <i class="fa-solid fa-hand" aria-hidden="true"></i>
        <input value={karte.blockiert_grund ?? ''} placeholder="Warum blockiert?" aria-label="Blockade-Grund"
          onchange={(e) => onAendern({ blockiert_grund: e.currentTarget.value || null })} />
      </label>
    {/if}

    <MarkdownFeld titel="Beschreibung" schluessel={karte.id} text={karte.beschreibung ?? ''} ohneVorschau ohneKnopf
      onSpeichern={(w) => onAendern({ beschreibung: w })}
      platzhalterEditor="Markdown ... (Überschriften, Listen, Code, Tabellen, $Mathe$, Mermaid)"
      platzhalterLeer="Keine Beschreibung. Klicken zum Bearbeiten."
      onVorlesen={vorlesenUmschalten} vorlesenLaeuft={tts.laeuft} />

    <MarkdownFeld titel="Notizen" schluessel={karte.id} text={karte.notizen ?? ''} nurVollbild
      onSpeichern={(w) => onAendern({ notizen: w })}
      platzhalterEditor="Notizen (Markdown) ..."
      platzhalterLeer="Keine Notizen. Klicken zum Bearbeiten." />

    <div class="zeile"><span class="lbl"><i class="fa-solid fa-list-check" aria-hidden="true"></i> Status</span>
      <select value={karte.spalte} onchange={(e) => onAendern({ spalte: e.currentTarget.value })}>
        {#each spalten as s (s.id)}<option value={s.id}>{s.titel}</option>{/each}
      </select>
    </div>
    <div class="zeile"><span class="lbl"><i class="fa-solid fa-flag" aria-hidden="true"></i> Priorität</span>
      <select value={karte.prioritaet ?? ''} onchange={(e) => onAendern({ prioritaet: (e.currentTarget.value || null) as Prioritaet | null })}>
        <option value="">keine</option>
        <option value="hoch">Hoch</option>
        <option value="mittel">Mittel</option>
        <option value="niedrig">Niedrig</option>
      </select>
    </div>
    <div class="zeile"><span class="lbl"><i class="fa-solid fa-play" aria-hidden="true"></i> Start</span>
      <input type="date" value={karte.start ?? ''} onchange={(e) => onAendern({ start: e.currentTarget.value || null })} />
    </div>
    <div class="zeile"><span class="lbl"><i class="fa-solid fa-calendar" aria-hidden="true"></i> Fällig</span>
      <input type="date" value={karte.faellig ?? ''} onchange={(e) => onAendern({ faellig: e.currentTarget.value || null })} />
    </div>
    <div class="zeile"><span class="lbl"><i class="fa-solid fa-user" aria-hidden="true"></i> Zuständig</span>
      <select value={karte.zustaendig ?? ''} onchange={(e) => zustaendigSetzen(e.currentTarget.value)}>
        <option value="">(niemand)</option>
        {#each kuerzelWahl as p (p.id)}<option value={p.kuerzel}>{p.kuerzel} - {p.name}</option>{/each}
      </select>
    </div>
    <div class="zeile"><span class="lbl"><i class="fa-solid fa-palette" aria-hidden="true"></i> Cover</span>
      <FarbWahl value={karte.cover ?? null} onWahl={(c) => onAendern({ cover: c })} />
    </div>

    <div class="zeiten">
      <span class:warn={imStatus >= 8}><i class="fa-solid fa-hourglass-half" aria-hidden="true"></i> Im Status: {imStatus} Tage</span>
      <span><i class="fa-solid fa-stopwatch" aria-hidden="true"></i> Durchlaufzeit: {durchlauf} Tage</span>
      <span><i class="fa-regular fa-calendar-plus" aria-hidden="true"></i> Erstellt: {datum(karte.erstellt_am)}</span>
    </div>

    {#if istIdee}
      <p class="idee-hinweis"><i class="fa-regular fa-lightbulb" aria-hidden="true"></i> Ideenticket - keine Zeiterfassung. Auf "Arbeit" umschalten, um Zeit zu buchen.</p>
    {:else}
      <Zeiterfassung {karte} {onAendern} />
      <VerknuepfteAufgaben {karte} {boardKarten} {onReload} {onOeffneKarte} />
    {/if}

    <p class="sec">Labels <span class="sec-ki"><KiAssistent typ="labels" titel="Labels vorschlagen" platzhalter="Worauf achten? (optional)" uebernehmenText="Hinzufuegen" kontext={kiLabelKontext} onUebernehmen={kiLabelUebernehmen} /></span></p>
    <div class="labels">
      {#each karte.labels as l (l)}
        {@const f = labelFarbe(l, dunkel)}
        <span class="lab" style="background:{f.bg};color:{f.fg}">{l}<button aria-label="Label entfernen" onclick={() => labelEntfernen(l)}><i class="fa-solid fa-xmark" aria-hidden="true"></i></button></span>
      {/each}
      <input class="labinput" placeholder="+ Label" bind:value={neuesLabel} onkeydown={(e) => { if (e.key === 'Enter') labelHinzufuegen() }} onblur={labelHinzufuegen} />
    </div>

    <Checkliste
      punkte={karte.checkliste}
      onPunktNeu={(text) => checklisteOp(checklistePunktNeu(karte.id, text))}
      onPunktAendern={(i, daten) => checklisteOp(checklistePunktAendern(karte.id, i, daten))}
      onPunktEntfernen={(i) => checklisteOp(checklistePunktLoeschen(karte.id, i))}
    />

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

    <TranskriptVerweise karteId={karte.id} />

    <p class="sec">Anhänge</p>
    {#if anhaenge.length}
      <ul class="anhaenge">
        {#each anhaenge as a (a.id)}
          <li>
            <button class="adatei" title="Herunterladen" onclick={() => anhangHerunterladen(a).catch(() => (anhangFehler = 'Download fehlgeschlagen'))}>
              <i class="fa-solid fa-paperclip" aria-hidden="true"></i>
              <span class="aname">{a.name}</span>
              <span class="agroesse">{groesseText(a.groesse)}</span>
            </button>
            <button class="aloeschen" aria-label="Anhang {a.name} löschen" title="Anhang löschen" onclick={() => anhangEntfernen(a)}>
              <i class="fa-solid fa-xmark" aria-hidden="true"></i>
            </button>
          </li>
        {/each}
      </ul>
    {/if}
    <input class="afile" type="file" multiple bind:this={dateiwahl} onchange={(e) => anhaengeHochladen(e.currentTarget.files)} />
    <button class="btn geist aknopf" disabled={anhangLaeuft} onclick={() => dateiwahl?.click()}>
      <i class="fa-solid {anhangLaeuft ? 'fa-spinner fa-spin' : 'fa-paperclip'}" aria-hidden="true"></i>
      {anhangLaeuft ? 'Lädt hoch ...' : 'Datei anhängen'}
    </button>
    {#if anhangFehler}<p class="afehler">{anhangFehler}</p>{/if}

    <p class="sec">Aktivität</p>
    {#each karte.kommentare as k (k.zeit + k.autor)}
      <div class="cmt"><span class="av">{initialen(k.autor)}</span><div class="ct"><b>{k.autor}</b> <span class="zeit">{zeitKurz(k.zeit)}</span><button class="cmt-vor" aria-label="Kommentar vorlesen" title="Vorlesen" onclick={() => vorlesen(k.text)}><i class="fa-solid fa-volume-high" aria-hidden="true"></i></button><div class="cmt-md"><Markdown md={k.text} /></div></div></div>
    {/each}
    <div class="cmtinput">
      <input placeholder="Kommentar schreiben ..." bind:value={kommentar} onkeydown={(e) => { if (e.key === 'Enter') kommentarSenden() }} />
      <button class="btn primaer" onclick={kommentarSenden}>Senden</button>
    </div>

    <button class="verlauf-kopf" onclick={verlaufUmschalten}>
      <i class="fa-solid {verlaufOffen ? 'fa-chevron-down' : 'fa-chevron-right'}" aria-hidden="true"></i>
      Verlauf
    </button>
    {#if verlaufOffen}
      {#if verlauf.length}
        <ul class="verlauf">
          {#each verlauf as a (a.id)}
            <li>
              <span class="vzeit">{verlaufWann(a)}</span>
              <span class="vtext">{#if a.kuerzel}<b>{a.kuerzel}</b>{' · '}{/if}{a.text}</span>
            </li>
          {/each}
        </ul>
      {:else}
        <p class="vleer">Noch kein Verlauf.</p>
      {/if}
    {/if}

    <div class="fuss">
      <button class="btn geist rot" onclick={onLoeschen}><i class="fa-solid fa-trash" aria-hidden="true"></i> Karte löschen</button>
    </div>
  </div>
</aside>

<style>
  .anhaenge { list-style: none; margin: 0 0 8px; padding: 0; display: flex; flex-direction: column; gap: 4px; }
  .anhaenge li { display: flex; align-items: center; gap: 4px; }
  .adatei {
    flex: 1; min-width: 0; display: flex; align-items: center; gap: 8px; text-align: left;
    background: var(--surface-2); border: 1px solid transparent; border-radius: var(--r-s);
    padding: 7px 9px; color: var(--text-1); font-size: 12px;
  }
  .adatei:hover { border-color: var(--border-2); background: var(--surface-3); }
  .adatei .fa-paperclip { color: var(--text-3); font-size: 11px; }
  .aname { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .agroesse { flex: none; color: var(--text-3); font-size: 10.5px; font-variant-numeric: tabular-nums; }
  .aloeschen { border: none; background: transparent; color: var(--text-3); font-size: 12px; padding: 6px; }
  .aloeschen:hover { color: var(--gefahr); }
  .afile { display: none; }
  .aknopf { font-size: 12px; }
  .afehler { color: var(--gefahr); font-size: 11.5px; margin: 6px 0 0; }
  .verlauf-kopf {
    display: inline-flex; align-items: center; gap: 7px; margin-top: 14px;
    border: none; background: transparent; color: var(--text-3); font-size: 12px;
    font-family: var(--font-display); padding: 0;
  }
  .verlauf-kopf:hover { color: var(--text-1); }
  .verlauf { list-style: none; margin: 8px 0 0; padding: 0; display: flex; flex-direction: column; gap: 3px; }
  .verlauf li { display: flex; align-items: baseline; gap: 9px; font-size: 11.5px; padding: 3px 0; border-bottom: 1px dashed var(--border); }
  .verlauf li:last-child { border-bottom: none; }
  .vzeit { flex: none; color: var(--text-3); font-variant-numeric: tabular-nums; font-size: 10.5px; }
  .vtext { color: var(--text-2); }
  .vtext b { color: var(--hl-primary-text); }
  .vleer { color: var(--text-3); font-size: 11.5px; margin: 6px 0 0; }
  .mini.blockiert { background: var(--gefahr); color: #fff; border-color: transparent; }
  .blockiert-grund { display: flex; align-items: center; gap: 8px; margin: 8px 0 0; padding: 7px 10px; border-radius: var(--r-m); background: color-mix(in srgb, var(--gefahr) 10%, transparent); color: var(--gefahr); font-size: 12px; }
  .blockiert-grund input { flex: 1; border: none; background: transparent; color: var(--text-1); font-size: 12.5px; outline: none; }
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
  .cmt-md {
    font-size: 12.5px;
  }
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
</style>
