<script lang="ts">
  // Wiederverwendbares Markdown-Textfeld: gerendert lesen, zum Bearbeiten klicken
  // (Editor mit optionaler Live-Vorschau), optional Vollbild und Vorlesen.
  // nurVollbild=true: Bearbeitung laeuft immer im Vollbild (z.B. Notizen).
  // ohneVorschau=true: Editor ist einspaltig (kein Vorschau-Bereich, z.B. Beschreibung).
  // ohneKnopf=true: kein eigener Bearbeiten-Knopf - der gerenderte Text ist anklickbar.
  import Markdown from '../../Markdown.svelte'

  let {
    titel,
    text,
    schluessel,
    onSpeichern,
    nurVollbild = false,
    ohneVorschau = false,
    ohneKnopf = false,
    platzhalterEditor = 'Markdown ...',
    platzhalterLeer = 'Leer. Klicken zum Bearbeiten.',
    onVorlesen,
    vorlesenLaeuft = false,
  }: {
    titel: string
    text: string
    schluessel: string // wechselt bei Kartenwechsel -> Entwurf neu laden
    onSpeichern: (wert: string | null) => void | Promise<void>
    nurVollbild?: boolean
    ohneVorschau?: boolean
    ohneKnopf?: boolean
    platzhalterEditor?: string
    platzhalterLeer?: string
    onVorlesen?: (text: string) => void
    vorlesenLaeuft?: boolean
  } = $props()

  let wert = $state('')
  let bearbeiten = $state(false)
  let vollbild = $state(false)
  let gespeichert = $state(false)
  let fehler = $state(false)
  let timer: ReturnType<typeof setTimeout> | null = null

  // Entwurf folgt der Karte (Wechsel ueber schluessel), nicht jeder Tasteneingabe.
  let zuletzt: string | null = null
  $effect(() => {
    if (schluessel !== zuletzt) {
      zuletzt = schluessel
      wert = text ?? ''
      bearbeiten = false
      vollbild = false
      gespeichert = false
    }
  })

  function auto(): void {
    if (timer) clearTimeout(timer)
    gespeichert = false
    timer = setTimeout(() => {
      // "gespeichert" erst, wenn der Server bestaetigt hat - nie rein zeitgesteuert.
      Promise.resolve(onSpeichern(wert || null)).then(
        () => { gespeichert = true; fehler = false },
        () => { fehler = true },
      )
    }, 600)
  }
  async function fertig(): Promise<void> {
    if (timer) clearTimeout(timer)
    try {
      await onSpeichern(wert || null)
      fehler = false
      bearbeiten = false
      vollbild = false
    } catch {
      // Editor offen lassen, damit der Text nicht verloren geht.
      fehler = true
    }
  }
  function oeffneEdit(): void {
    bearbeiten = true
    vollbild = nurVollbild
  }
</script>

<div class="sec-reihe">
  <p class="sec">{titel}</p>
  <span class="md-werkzeuge">
    {#if fehler}<span class="gesp nicht">nicht gespeichert</span>{:else if gespeichert}<span class="gesp">gespeichert</span>{/if}
    {#if bearbeiten}
      {#if !nurVollbild}
        <button class="mini geist" onclick={() => (vollbild = !vollbild)}><i class="fa-solid {vollbild ? 'fa-compress' : 'fa-expand'}" aria-hidden="true"></i> {vollbild ? 'Verkleinern' : 'Vollbild'}</button>
      {/if}
      <button class="mini" onclick={fertig}>Fertig</button>
    {:else}
      {#if onVorlesen && wert.trim()}
        <button class="mini geist" onclick={() => onVorlesen?.(wert)}><i class="fa-solid {vorlesenLaeuft ? 'fa-stop' : 'fa-volume-high'}" aria-hidden="true"></i> {vorlesenLaeuft ? 'Stopp' : 'Vorlesen'}</button>
      {/if}
      {#if nurVollbild}
        {#if wert.trim()}<button class="mini geist" onclick={oeffneEdit}><i class="fa-solid fa-expand" aria-hidden="true"></i> Vollbild</button>{/if}
      {:else if !ohneKnopf}
        <button class="mini geist" onclick={oeffneEdit}><i class="fa-solid fa-pen" aria-hidden="true"></i> Bearbeiten</button>
      {/if}
    {/if}
  </span>
</div>
{#if bearbeiten}
  <div class="md-editor" class:vollbild>
    {#if vollbild}
      <div class="vb-kopf"><b>{titel} bearbeiten</b><button class="mini" onclick={fertig}>Fertig</button></div>
    {/if}
    <div class="md-split" class:einzeln={ohneVorschau}>
      <!-- svelte-ignore a11y_autofocus -->
      <textarea class="desc" placeholder={platzhalterEditor} bind:value={wert} oninput={auto} autofocus></textarea>
      {#if !ohneVorschau}<div class="md-vorschau"><Markdown md={wert || '*Vorschau*'} /></div>{/if}
    </div>
  </div>
{:else if wert.trim()}
  <button class="md-ansicht" onclick={oeffneEdit} title="Zum Bearbeiten klicken"><Markdown md={wert} /></button>
{:else}
  <button class="leer-hinweis" onclick={oeffneEdit}>{platzhalterLeer}</button>
{/if}

<style>
  .sec { font-family: var(--font-display); font-size: 10.5px; letter-spacing: 0.04em; text-transform: uppercase; color: var(--text-3); margin: 18px 0 8px; }
  .sec-reihe { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
  .md-werkzeuge { display: flex; align-items: center; gap: 6px; }
  .gesp { font-size: 10.5px; color: var(--ok); }
  .gesp.nicht { color: var(--gefahr); font-weight: 600; }
  .mini { border: 1px solid var(--hl-primary); background: var(--hl-primary); color: var(--hl-on-primary); border-radius: var(--r-s); padding: 4px 9px; font-size: 11.5px; white-space: nowrap; cursor: pointer; }
  .mini.geist { background: transparent; color: var(--text-2); border-color: var(--border-2); }
  .desc { width: 100%; box-sizing: border-box; border: 1px solid var(--border); background: var(--surface-2); color: var(--text-1); border-radius: var(--r-m); padding: 9px 10px; font-size: 12.5px; line-height: 1.5; resize: vertical; }
  .md-ansicht { display: block; width: 100%; text-align: left; background: var(--surface-2); border: 1px solid var(--border); border-radius: var(--r-m); padding: 10px 11px; cursor: text; }
  .md-ansicht:hover { border-color: var(--border-2); }
  .leer-hinweis { display: block; width: 100%; text-align: left; background: transparent; border: 1px dashed var(--border-2); border-radius: var(--r-m); padding: 10px 11px; color: var(--text-3); font-size: 12.5px; cursor: text; }
  .md-editor .md-split { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
  .md-editor .md-split.einzeln { grid-template-columns: 1fr; }
  .md-editor .desc { min-height: 120px; }
  .md-vorschau { border: 1px solid var(--border); background: var(--surface-2); border-radius: var(--r-m); padding: 9px 10px; overflow-y: auto; max-height: 320px; }
  /* Vollbild: nur dieses Feld gross, fokussiert (Eingabe links, Vorschau rechts). */
  .md-editor.vollbild { position: fixed; inset: 0; z-index: 60; background: var(--surface-col); padding: 16px; display: flex; flex-direction: column; gap: 12px; }
  .md-editor.vollbild .md-split { flex: 1; min-height: 0; }
  .md-editor.vollbild .desc,
  .md-editor.vollbild .md-vorschau { max-height: none; height: 100%; }
  .md-editor.vollbild .desc { font-size: 16px; line-height: 1.65; padding: 18px 20px; }
  .md-editor.vollbild .md-vorschau { padding: 18px 20px; }
  .md-editor.vollbild .md-vorschau :global(.md-body) { font-size: 16px; line-height: 1.7; }
  .vb-kopf { display: flex; align-items: center; justify-content: space-between; }
</style>
