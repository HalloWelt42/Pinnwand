<script lang="ts">
  import type { Karte, Prioritaet, Spalte } from '../../types'
  import type { KarteAenderung } from '../../api'
  import { labelFarbe } from '../../labels'
  import { theme } from '../../theme/theme.svelte'
  import { timer, timerStarten, timerPausieren, erfassteSekunden, formatDauer, formatPlan } from '../../timer.svelte'
  import Markdown from '../../Markdown.svelte'
  import { tts, vorlesen, stoppeVorlesen } from '../../tts.svelte'

  let {
    karte,
    spalten,
    onSchliessen,
    onAendern,
    onKommentar,
    onLoeschen,
  }: {
    karte: Karte
    spalten: Spalte[]
    onSchliessen: () => void
    onAendern: (daten: KarteAenderung) => void
    onKommentar: (text: string) => void
    onLoeschen: () => void
  } = $props()

  const dunkel = $derived(theme.modus === 'dunkel')

  let beschr = $state('')
  let neuerPunkt = $state('')
  let neuesLabel = $state('')
  let kommentar = $state('')
  let bearbeiten = $state(false)
  let vollbild = $state(false)
  let gespeichert = $state(false)
  let spTimer: ReturnType<typeof setTimeout> | null = null

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
    bearbeiten = false
    vollbild = false
  }
  function vorlesenUmschalten() {
    if (tts.laeuft) stoppeVorlesen()
    else vorlesen(beschr)
  }

  // Beschreibungs-Entwurf folgt der Karte (auch beim ersten Oeffnen).
  let zuletzt = $state<string | null>(null)
  $effect(() => {
    if (karte.id !== zuletzt) {
      zuletzt = karte.id
      beschr = karte.beschreibung ?? ''
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
  function labelHinzufuegen() {
    const l = neuesLabel.trim()
    if (!l || karte.labels.includes(l)) {
      neuesLabel = ''
      return
    }
    onAendern({ labels: [...karte.labels, l] })
    neuesLabel = ''
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
    return iso.replace('T', ' ').slice(0, 16)
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
    if (!iso) return '-'
    const [j, m, t] = iso.slice(0, 10).split('-')
    return `${t}.${m}.${j}`
  }
  const imStatus = $derived(tage(karte.bewegt_am) ?? 0)
  const durchlauf = $derived(tage(karte.erstellt_am) ?? 0)
  const laeuft = $derived(!!karte.laeuft_seit)
  const sek = $derived(laeuft ? erfassteSekunden(karte, timer.jetzt) : (karte.erfasst_sek ?? 0))
  const planMin = $derived(karte.schaetzung_min ?? null)
  const prozent = $derived(planMin && planMin > 0 ? (sek / 60 / planMin) * 100 : null)
</script>

<div class="backdrop" role="presentation" onclick={onSchliessen}></div>
<aside class="drawer" aria-label="Kartendetails">
  <header>
    {#if karte.schluessel}<span class="key">{karte.schluessel}</span>{/if}
    <span class="pfad">{spalten.find((s) => s.id === karte.spalte)?.titel ?? ''}</span>
    <button class="ib" aria-label="Schließen" onclick={onSchliessen}><i class="fa-solid fa-xmark" aria-hidden="true"></i></button>
  </header>

  <div class="body">
    <input class="titel" value={karte.titel} aria-label="Titel" onchange={(e) => onAendern({ titel: e.currentTarget.value })} />

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
      <input class="kurz" placeholder="Kürzel" value={karte.zustaendig ?? ''} onchange={(e) => onAendern({ zustaendig: e.currentTarget.value || null })} />
    </div>

    <div class="zeiten">
      <span class:warn={imStatus >= 8}><i class="fa-solid fa-hourglass-half" aria-hidden="true"></i> Im Status: {imStatus} Tage</span>
      <span><i class="fa-solid fa-stopwatch" aria-hidden="true"></i> Durchlaufzeit: {durchlauf} Tage</span>
      <span><i class="fa-regular fa-calendar-plus" aria-hidden="true"></i> Erstellt: {datum(karte.erstellt_am)}</span>
    </div>

    <p class="sec">Zeiterfassung</p>
    <div class="timer">
      <button class="tbtn" class:an={laeuft} onclick={() => (laeuft ? timerPausieren(karte.id) : timerStarten(karte.id))}>
        <i class="fa-solid {laeuft ? 'fa-pause' : 'fa-play'}" aria-hidden="true"></i> {laeuft ? 'Pause' : 'Start'}
      </button>
      <span class="erfasst">{formatDauer(sek)}</span>
      <label class="plan">Schätzung
        <input type="number" min="0" step="0.25" value={planMin ? planMin / 60 : ''}
          onchange={(e) => { const v = parseFloat(e.currentTarget.value); onAendern({ schaetzung_min: Number.isFinite(v) && v > 0 ? Math.round(v * 60) : null }) }} />
        Std
      </label>
    </div>
    {#if prozent != null}
      <div class="fortschritt" class:ueber={prozent > 100}><span style="width:{Math.min(prozent, 100)}%"></span></div>
      <div class="pinfo" class:ueber={prozent > 100}>{Math.round(prozent)}% von {formatPlan(planMin ?? 0)}{#if prozent > 100} - überschritten{/if}</div>
    {/if}

    <p class="sec">Labels</p>
    <div class="labels">
      {#each karte.labels as l (l)}
        {@const f = labelFarbe(l, dunkel)}
        <span class="lab" style="background:{f.bg};color:{f.fg}">{l}<button aria-label="Label entfernen" onclick={() => labelEntfernen(l)}><i class="fa-solid fa-xmark" aria-hidden="true"></i></button></span>
      {/each}
      <input class="labinput" placeholder="+ Label" bind:value={neuesLabel} onkeydown={(e) => { if (e.key === 'Enter') labelHinzufuegen() }} onblur={labelHinzufuegen} />
    </div>

    <div class="sec-reihe">
      <p class="sec">Beschreibung</p>
      <span class="md-werkzeuge">
        {#if bearbeiten}
          {#if gespeichert}<span class="gesp">gespeichert</span>{/if}
          <button class="mini geist" onclick={() => (vollbild = !vollbild)}><i class="fa-solid {vollbild ? 'fa-compress' : 'fa-expand'}" aria-hidden="true"></i> {vollbild ? 'Verkleinern' : 'Vollbild'}</button>
          <button class="mini" onclick={bearbeitenFertig}>Fertig</button>
        {:else}
          {#if beschr.trim()}
            <button class="mini geist" onclick={vorlesenUmschalten}><i class="fa-solid {tts.laeuft ? 'fa-stop' : 'fa-volume-high'}" aria-hidden="true"></i> {tts.laeuft ? 'Stopp' : 'Vorlesen'}</button>
          {/if}
          <button class="mini geist" onclick={() => (bearbeiten = true)}><i class="fa-solid fa-pen" aria-hidden="true"></i> Bearbeiten</button>
        {/if}
      </span>
    </div>
    {#if bearbeiten}
      <div class="md-editor" class:vollbild>
        {#if vollbild}
          <div class="vb-kopf"><b>Beschreibung bearbeiten</b><button class="mini" onclick={bearbeitenFertig}>Fertig</button></div>
        {/if}
        <div class="md-split">
          <textarea class="desc" placeholder="Markdown ... (Ueberschriften, Listen, Code, Tabellen, $Mathe$, Mermaid)" bind:value={beschr} oninput={autoSpeichern}></textarea>
          <div class="md-vorschau"><Markdown md={beschr || '*Vorschau*'} /></div>
        </div>
      </div>
    {:else if beschr.trim()}
      <button class="md-ansicht" onclick={() => (bearbeiten = true)} title="Zum Bearbeiten klicken"><Markdown md={beschr} /></button>
    {:else}
      <button class="leer-hinweis" onclick={() => (bearbeiten = true)}>Keine Beschreibung. Klicken zum Bearbeiten.</button>
    {/if}

    <p class="sec">Checkliste {#if karte.checkliste.length}<span class="dezent">&middot; {erledigt} von {karte.checkliste.length}</span>{/if}</p>
    {#if karte.checkliste.length}
      <div class="chkbar"><span style="width:{(erledigt / karte.checkliste.length) * 100}%"></span></div>
    {/if}
    {#each karte.checkliste as punkt, i (i)}
      <div class="chk" class:done={punkt.erledigt}>
        <button class="box" aria-label="Umschalten" onclick={() => punktUmschalten(i)}>
          <i class="fa-{punkt.erledigt ? 'solid fa-square-check' : 'regular fa-square'}" aria-hidden="true"></i>
        </button>
        <span>{punkt.text}</span>
        <button class="del" aria-label="Punkt entfernen" onclick={() => punktEntfernen(i)}><i class="fa-solid fa-xmark" aria-hidden="true"></i></button>
      </div>
    {/each}
    <input class="feld" placeholder="+ Punkt hinzufügen" bind:value={neuerPunkt} onkeydown={(e) => { if (e.key === 'Enter') punktHinzufuegen() }} />

    <p class="sec">Aktivität</p>
    {#each karte.kommentare as k (k.zeit + k.autor)}
      <div class="cmt"><span class="av">{initialen(k.autor)}</span><div class="ct"><b>{k.autor}</b> <span class="zeit">{zeitKurz(k.zeit)}</span><div class="cmt-md"><Markdown md={k.text} /></div></div></div>
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
    margin-left: auto;
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
  .zeile input.kurz {
    flex: 0 0 90px;
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
  .erfasst {
    font-family: var(--font-mono);
    font-size: 18px;
    font-variant-numeric: tabular-nums;
    color: var(--text-1);
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
  .sec {
    font-family: var(--font-display);
    font-size: 10.5px;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: var(--text-3);
    margin: 18px 0 8px;
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
  .chk.done span {
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
  .chk span {
    flex: 1;
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
  .md-editor .md-split {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
  }
  .md-editor .desc {
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
  .md-editor.vollbild {
    position: fixed;
    inset: 0;
    z-index: 60;
    background: var(--surface-col);
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  .md-editor.vollbild .md-split {
    flex: 1;
    min-height: 0;
  }
  .md-editor.vollbild .desc,
  .md-editor.vollbild .md-vorschau {
    max-height: none;
    height: 100%;
  }
  /* Im Vollbild komfortabel grosse Schrift in Eingabe und Vorschau. */
  .md-editor.vollbild .desc {
    font-size: 16px;
    line-height: 1.65;
    padding: 18px 20px;
  }
  .md-editor.vollbild .md-vorschau {
    padding: 18px 20px;
  }
  .md-editor.vollbild .md-vorschau :global(.md-body) {
    font-size: 16px;
    line-height: 1.7;
  }
  .vb-kopf {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .cmt-md {
    font-size: 12.5px;
  }
</style>
