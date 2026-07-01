<script lang="ts">
  import {
    ladeDokumente, erstelleDokument, aktualisiereDokument, loescheDokument,
    type Dokument, type DokumentKontext,
  } from './api'
  import { isoDatumZeit } from './zeit'
  import Markdown from './Markdown.svelte'

  let { kontext, kontextId }: { kontext: DokumentKontext; kontextId: string } = $props()

  let dokumente = $state<Dokument[]>([])
  let aktiv = $state<Dokument | null>(null)
  let inhalt = $state('')
  let neuTitel = $state('')
  let neuOffen = $state(false)
  let loeschId = $state<string | null>(null)
  let vollbild = $state(false)
  let gespeichert = $state(false)
  let speicherfehler = $state(false)
  let spTimer: ReturnType<typeof setTimeout> | null = null

  // Dokumentliste laedt neu, sobald sich der Kontext (Karte/Mappe) aendert.
  let zuletzt = $state<string | null>(null)
  $effect(() => {
    if (kontextId && kontextId !== zuletzt) {
      zuletzt = kontextId
      aktiv = null
      void laden()
    }
  })

  async function laden() {
    dokumente = await ladeDokumente(kontext, kontextId)
  }
  async function neuAnlegen() {
    const t = neuTitel.trim()
    if (!t) return
    const d = await erstelleDokument(kontext, kontextId, t)
    neuTitel = ''
    neuOffen = false
    await laden()
    oeffne(d)
  }
  function oeffne(d: Dokument) {
    aktiv = d
    inhalt = d.inhalt
    gespeichert = false
  }
  function inhaltGeaendert() {
    if (!aktiv) return
    if (spTimer) clearTimeout(spTimer)
    gespeichert = false
    const id = aktiv.id
    spTimer = setTimeout(async () => {
      // Speicherfehler NICHT verschlucken: der Text bleibt im Editor, der Zustand
      // wird deutlich rot markiert; der naechste Tastendruck versucht es erneut.
      try {
        await aktualisiereDokument(id, { inhalt })
        if (aktiv && aktiv.id === id) aktiv.inhalt = inhalt
        gespeichert = true
        speicherfehler = false
      } catch {
        speicherfehler = true
      }
    }, 600)
  }
  async function titelSpeichern() {
    if (!aktiv) return
    const t = (aktiv.titel || '').trim()
    if (!t) return
    await aktualisiereDokument(aktiv.id, { titel: t })
    await laden()
  }
  async function loeschenBestaetigt(id: string) {
    await loescheDokument(id)
    loeschId = null
    if (aktiv && aktiv.id === id) aktiv = null
    await laden()
  }
</script>

<div class="dok">
  {#if aktiv}
    <div class="kopf">
      <button class="zurueck" onclick={() => (aktiv = null)}><i class="fa-solid fa-chevron-left" aria-hidden="true"></i> Liste</button>
      {#if speicherfehler}<span class="gesp nicht">nicht gespeichert - Text bleibt im Editor</span>{:else if gespeichert}<span class="gesp">gespeichert</span>{/if}
      <button class="ic" aria-label={vollbild ? 'Verkleinern' : 'Vollbild'} onclick={() => (vollbild = !vollbild)}><i class="fa-solid {vollbild ? 'fa-compress' : 'fa-expand'}" aria-hidden="true"></i></button>
    </div>
    <input class="dtitel" bind:value={aktiv.titel} aria-label="Dokumenttitel" onblur={titelSpeichern} onkeydown={(e) => { if (e.key === 'Enter') (e.currentTarget as HTMLInputElement).blur() }} />
    <div class="editor" class:vollbild>
      {#if vollbild}
        <div class="vbkopf"><b>{aktiv.titel}</b><button class="mini" onclick={() => (vollbild = false)}>Fertig</button></div>
      {/if}
      <div class="split">
        <textarea class="ta" placeholder="Markdown ... (Überschriften, Listen, Code, Tabellen, $Mathe$, Mermaid)" bind:value={inhalt} oninput={inhaltGeaendert}></textarea>
        <div class="vorschau"><Markdown md={inhalt || '*Vorschau*'} /></div>
      </div>
    </div>
  {:else}
    {#if dokumente.length}
      <ul class="liste">
        {#each dokumente as d (d.id)}
          {#if loeschId === d.id}
            <li class="confirm"><span>"{d.titel}" löschen?</span><span class="cbtn"><button class="mini rot" onclick={() => loeschenBestaetigt(d.id)}>Löschen</button><button class="mini geist" onclick={() => (loeschId = null)}>Abbrechen</button></span></li>
          {:else}
            <li>
              <button class="oeffnen" onclick={() => oeffne(d)}>
                <i class="fa-regular fa-file-lines" aria-hidden="true"></i>
                <span class="dt">{d.titel}</span>
                {#if d.bewegt_am}<span class="dz">{isoDatumZeit(d.bewegt_am)}</span>{/if}
              </button>
              <button class="ic" aria-label="Dokument löschen" onclick={() => (loeschId = d.id)}><i class="fa-solid fa-trash" aria-hidden="true"></i></button>
            </li>
          {/if}
        {/each}
      </ul>
    {:else}
      <p class="leer">Noch keine Dokumente.</p>
    {/if}
    {#if neuOffen}
      <!-- svelte-ignore a11y_autofocus -->
      <input class="neu" placeholder="Titel des Dokuments" bind:value={neuTitel} autofocus
        onkeydown={(e) => { if (e.key === 'Enter') neuAnlegen(); if (e.key === 'Escape') { neuOffen = false; neuTitel = '' } }}
        onblur={() => { if (!neuTitel.trim()) neuOffen = false }} />
    {:else}
      <button class="add" onclick={() => (neuOffen = true)}><i class="fa-solid fa-plus" aria-hidden="true"></i> Dokument</button>
    {/if}
  {/if}
</div>

<style>
  .dok { display: flex; flex-direction: column; gap: 7px; }
  .liste { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 3px; }
  .liste li { display: flex; align-items: center; gap: 4px; }
  .oeffnen {
    flex: 1; min-width: 0; display: flex; align-items: center; gap: 9px;
    border: 1px solid var(--border); background: var(--surface-2); color: var(--text-1);
    border-radius: var(--r-m); padding: 8px 10px; font-size: 12.5px; text-align: left;
  }
  .oeffnen:hover { border-color: var(--hl-primary); }
  .oeffnen .dt { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .oeffnen .dz { color: var(--text-3); font-size: 10.5px; flex: none; }
  .ic {
    border: none; background: transparent; color: var(--text-3);
    width: 28px; height: 28px; border-radius: var(--r-s); font-size: 12px; flex: none;
  }
  .ic:hover { background: var(--surface-3); color: var(--hl-primary-text); }
  .add {
    display: flex; align-items: center; gap: 9px; border: 1px dashed var(--border-2);
    background: transparent; color: var(--text-3); font-size: 12.5px; padding: 7px 10px; border-radius: var(--r-m);
  }
  .add:hover { color: var(--hl-primary-text); border-color: var(--hl-primary); }
  .neu {
    width: 100%; border: 1px solid var(--border); background: var(--surface-2); color: var(--text-1);
    border-radius: var(--r-m); padding: 7px 9px; font-size: 12.5px;
  }
  .leer { color: var(--text-3); font-size: 12.5px; margin: 0; }
  .confirm {
    display: flex; align-items: center; justify-content: space-between; gap: 8px;
    border: 1px solid var(--border); border-radius: var(--r-m); padding: 7px 10px; font-size: 12px; color: var(--text-2);
  }
  .cbtn { display: flex; gap: 6px; flex: none; }
  .mini {
    border: 1px solid var(--hl-primary); background: var(--hl-primary); color: var(--hl-on-primary);
    border-radius: var(--r-s); padding: 4px 9px; font-size: 11.5px; white-space: nowrap;
  }
  .mini.geist { background: transparent; color: var(--text-2); border-color: var(--border-2); }
  .mini.rot { background: transparent; color: var(--gefahr); border-color: var(--gefahr); }
  .kopf { display: flex; align-items: center; gap: 8px; }
  .zurueck {
    border: 1px solid var(--border-2); background: transparent; color: var(--text-2);
    border-radius: var(--r-s); padding: 4px 9px; font-size: 11.5px; display: inline-flex; align-items: center; gap: 6px;
  }
  .zurueck:hover { color: var(--text-1); }
  .gesp.nicht { color: var(--gefahr); font-weight: 600; }
  .gesp { font-size: 10.5px; color: var(--ok); margin-left: auto; }
  .kopf .ic { margin-left: auto; }
  .kopf .gesp + .ic { margin-left: 0; }
  .dtitel {
    width: 100%; border: 1px solid var(--border); background: var(--surface-2); color: var(--text-1);
    border-radius: var(--r-m); padding: 7px 9px; font-size: 14px; font-weight: 600; font-family: var(--font-display);
  }
  .split { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
  .ta {
    width: 100%; min-height: 160px; border: 1px solid var(--border); background: var(--surface-2);
    color: var(--text-1); border-radius: var(--r-m); padding: 9px 10px; font-size: 12.5px; line-height: 1.5; resize: vertical;
  }
  .vorschau {
    border: 1px solid var(--border); background: var(--surface-2); border-radius: var(--r-m);
    padding: 9px 10px; overflow-y: auto; max-height: 360px;
  }
  .editor.vollbild {
    position: fixed; inset: 0; z-index: 60; background: var(--surface-col);
    padding: 16px; display: flex; flex-direction: column; gap: 12px;
  }
  .editor.vollbild .split { flex: 1; min-height: 0; }
  .editor.vollbild .ta, .editor.vollbild .vorschau { max-height: none; height: 100%; font-size: 16px; line-height: 1.65; padding: 18px 20px; }
  .vbkopf { display: flex; align-items: center; justify-content: space-between; }
</style>
