<script lang="ts">
  import { dndzone, dragHandle, SHADOW_PLACEHOLDER_ITEM_ID } from 'svelte-dnd-action'
  import { flip } from 'svelte/animate'
  import type { Karte, Spalte } from '../../types'
  import Card from './Card.svelte'

  let {
    spalte,
    karten,
    dragDisabled,
    zeitfilter,
    onZeitfilter,
    akzent,
    eingeklappt,
    istErste,
    istLetzte,
    einzige,
    onCardsConsider,
    onCardsFinalize,
    onOeffnen,
    onLoeschenKarte,
    onVerknuepfen,
    onKarteAnlegen,
    onToggleEinklappen,
    onSpalteUmbenennen,
    onSpalteVerschieben,
    onSpalteLoeschen,
    onSpalteErledigt,
    fertigMehr = false,
    fertigLaden = false,
    fertigGesamt = 0,
    onNachladen,
  }: {
    spalte: Spalte
    karten: Karte[]
    dragDisabled: boolean
    zeitfilter: string
    onZeitfilter: (zeitraum: string) => void
    akzent: string
    eingeklappt: boolean
    istErste: boolean
    istLetzte: boolean
    einzige: boolean
    onCardsConsider: (items: Karte[]) => void
    onCardsFinalize: (items: Karte[], info: { id: string }) => void
    onOeffnen: (id: string) => void
    onLoeschenKarte: (id: string) => void
    onVerknuepfen?: (quelleId: string, zielId: string) => void
    onKarteAnlegen: (titel: string, typ?: 'arbeit' | 'idee') => void | Promise<void>
    onToggleEinklappen: () => void
    onSpalteUmbenennen: (daten: { titel: string; wip_limit: number | null }) => void
    onSpalteVerschieben: (richtung: -1 | 1) => void
    onSpalteLoeschen: () => void
    onSpalteErledigt: () => void
    // Erledigt-Spalten: gefenstertes Nachladen beim Scrollen.
    fertigMehr?: boolean
    fertigLaden?: boolean
    fertigGesamt?: number
    onNachladen?: () => void
  } = $props()

  // Beim Scrollen ans Ende einer Erledigt-Spalte die naechste Seite nachladen.
  function aufScroll(e: Event): void {
    if (!spalte.erledigt || !fertigMehr || fertigLaden || !onNachladen) return
    const el = e.currentTarget as HTMLElement
    if (el.scrollTop + el.clientHeight >= el.scrollHeight - 80) onNachladen()
  }

  let modus = $state<'normal' | 'edit'>('normal')
  let menuOffen = $state(false)
  let titelEntwurf = $state('')
  // Das WIP-Feld ist ein type=number-Input: Svelte bindet hier eine Zahl bzw. null, keinen String.
  let wipEntwurf = $state<number | null>(null)
  let neueKarte = $state(false)
  let karteTitel = $state('')
  let alsIdee = $state(false)

  const anzahl = $derived(karten.filter((k) => k.id !== SHADOW_PLACEHOLDER_ITEM_ID).length)
  const wipVoll = $derived(spalte.wip_limit != null && anzahl >= spalte.wip_limit)
  // Ueber dem Limit (echte Ueberschreitung) - deutlicher als nur "voll" (genau am Limit).
  const wipUeber = $derived(spalte.wip_limit != null && anzahl > spalte.wip_limit)
  const fuellung = $derived(spalte.wip_limit ? Math.min(100, (anzahl / spalte.wip_limit) * 100) : 0)

  function bearbeiten() {
    titelEntwurf = spalte.titel
    wipEntwurf = spalte.wip_limit ?? null
    menuOffen = false
    modus = 'edit'
  }
  function speichern() {
    const titel = titelEntwurf.trim()
    if (!titel) return
    const wip = wipEntwurf == null || Number.isNaN(wipEntwurf) ? null : Math.max(1, Math.floor(wipEntwurf))
    onSpalteUmbenennen({ titel, wip_limit: wip })
    modus = 'normal'
  }
  async function karteAbschicken() {
    const titel = karteTitel.trim()
    if (!titel) return
    // Eingabe erst nach Server-Erfolg leeren - bei Fehlern bleibt der Titel erhalten.
    await onKarteAnlegen(titel, alsIdee ? 'idee' : 'arbeit')
    karteTitel = ''
    alsIdee = false
  }
</script>

{#if eingeklappt}
  <section class="zu">
    <div class="zukopf" role="button" tabindex="0" title="Ausklappen"
      onclick={onToggleEinklappen}
      onkeydown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onToggleEinklappen() } }}>
      <span class="griffzu" use:dragHandle title="Zum Umsortieren ziehen" aria-label="Spalte umsortieren"><i class="fa-solid fa-grip-vertical" aria-hidden="true"></i></span>
      <i class="fa-solid fa-angles-right" aria-hidden="true"></i>
      <span class="dot" style="background:{akzent}"></span>
      <span class="vtitel">{spalte.titel}</span>
      <span class="vzahl">{anzahl}</span>
    </div>
    <div
      class="zuliste"
      use:dndzone={{ items: karten, type: 'karte', dragDisabled, flipDurationMs: 160, dropTargetStyle: {} }}
      onconsider={(e) => onCardsConsider(e.detail.items)}
      onfinalize={(e) => onCardsFinalize(e.detail.items, e.detail.info)}
    >
      {#each karten as karte (karte.id)}
        <div animate:flip={{ duration: 160 }}>
          {#if karte.id === SHADOW_PLACEHOLDER_ITEM_ID}
            <div class="slim ph"></div>
          {:else}
            <div class="slim" style="background:{akzent}" title={karte.titel}></div>
          {/if}
        </div>
      {/each}
    </div>
  </section>
{:else}
  <section class="col">
    {#if modus === 'edit'}
      <div class="bearbeiten">
        <!-- svelte-ignore a11y_autofocus -->
        <input class="feld" bind:value={titelEntwurf} aria-label="Spaltentitel" autofocus
          onkeydown={(e) => { if (e.key === 'Enter') speichern(); if (e.key === 'Escape') (modus = 'normal') }} />
        <input class="feld" type="number" min="1" placeholder="WIP-Limit (leer = keins)" bind:value={wipEntwurf} aria-label="WIP-Limit" />
        <div class="reihe">
          <button class="btn primaer" onclick={speichern}>Speichern</button>
          <button class="btn geist" onclick={() => (modus = 'normal')}>Abbrechen</button>
        </div>
      </div>
    {:else}
      <header>
        <div class="zieh" title="Zum Umsortieren ziehen" use:dragHandle aria-label="Spalte umsortieren">
          <span class="griff"><i class="fa-solid fa-grip-vertical" aria-hidden="true"></i></span>
          <span class="punkt" style="background:{akzent}"></span>
          <span class="titel">{spalte.titel}</span>
          <span class="zaehler" class:warn={wipVoll} class:ueber={wipUeber} title={spalte.wip_limit != null ? `${anzahl} Karten / WIP-Limit ${spalte.wip_limit} (Hoechstzahl gleichzeitiger Karten; amber am Limit, rot darueber)` : `${anzahl} Karten`}>{anzahl}{#if spalte.wip_limit != null}/{spalte.wip_limit}{/if}</span>
        </div>
        {#if spalte.erledigt}
          <select class="zeitfilter" value={zeitfilter} onchange={(e) => onZeitfilter(e.currentTarget.value)} title="Zeitraum (fertiggestellt)" aria-label="Zeitraum-Filter">
            <option value="heute">Heute</option>
            <option value="gestern">Gestern</option>
            <option value="woche">Woche</option>
            <option value="monat">Monat</option>
            <option value="jahr">Jahr</option>
            <option value="alle">Alle</option>
          </select>
        {/if}
        <button class="hbtn" aria-label="Spalte einklappen" title="Einklappen" onclick={onToggleEinklappen}><i class="fa-solid fa-angles-left" aria-hidden="true"></i></button>
        <button class="hbtn" class:aktiv={menuOffen} aria-label="Spaltenmenü" onclick={() => (menuOffen = !menuOffen)}><i class="fa-solid fa-ellipsis" aria-hidden="true"></i></button>
        {#if menuOffen}
          <div class="menu">
            <button onclick={bearbeiten}><i class="fa-solid fa-pen" aria-hidden="true"></i> Umbenennen / WIP</button>
            {#if !spalte.erledigt}
              <button onclick={() => { onSpalteErledigt(); menuOffen = false }}><i class="fa-solid fa-circle-check" aria-hidden="true"></i> Als Erledigt-Spalte</button>
            {/if}
            <button onclick={() => { onToggleEinklappen(); menuOffen = false }}><i class="fa-solid fa-angles-left" aria-hidden="true"></i> Einklappen</button>
            <button disabled={istErste} onclick={() => { onSpalteVerschieben(-1); menuOffen = false }}><i class="fa-solid fa-arrow-left" aria-hidden="true"></i> Nach links</button>
            <button disabled={istLetzte} onclick={() => { onSpalteVerschieben(1); menuOffen = false }}><i class="fa-solid fa-arrow-right" aria-hidden="true"></i> Nach rechts</button>
            <div class="trenner"></div>
            <button class="rot" disabled={einzige} onclick={() => { menuOffen = false; onSpalteLoeschen() }}><i class="fa-solid fa-trash" aria-hidden="true"></i> Löschen</button>
          </div>
        {/if}
      </header>
      {#if spalte.wip_limit != null}
        <div class="wip"><span style="width:{fuellung}%;background:{wipUeber ? 'var(--gefahr, #e5484d)' : wipVoll ? 'var(--prio-mittel)' : akzent}"></span></div>
      {/if}
    {/if}

    <div
      class="liste"
      use:dndzone={{ items: karten, type: 'karte', dragDisabled, flipDurationMs: 160, dropTargetStyle: {} }}
      onconsider={(e) => onCardsConsider(e.detail.items)}
      onfinalize={(e) => onCardsFinalize(e.detail.items, e.detail.info)}
      onscroll={aufScroll}
    >
      {#each karten as karte (karte.id)}
        <div animate:flip={{ duration: 160 }}>
          {#if karte.id === SHADOW_PLACEHOLDER_ITEM_ID}
            <div class="platzhalter"></div>
          {:else}
            <Card {karte} {onOeffnen} onLoeschen={onLoeschenKarte} {onVerknuepfen} />
          {/if}
        </div>
      {/each}
    </div>

    {#if spalte.erledigt && (fertigMehr || fertigGesamt > 0)}
      <div class="fertiginfo">
        <span>{karten.filter((k) => k.id !== SHADOW_PLACEHOLDER_ITEM_ID).length} von {fertigGesamt}</span>
        {#if fertigMehr}
          <button class="mehr" onclick={() => onNachladen?.()} disabled={fertigLaden}>
            {fertigLaden ? 'Lädt ...' : 'Mehr laden'}
          </button>
        {/if}
      </div>
    {/if}

    {#if neueKarte}
      <div class="composer">
        <!-- svelte-ignore a11y_autofocus -->
        <textarea class="feld" rows="2" placeholder="Titel der Karte ..." bind:value={karteTitel} aria-label="Neue Karte" autofocus
          onkeydown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); karteAbschicken() } if (e.key === 'Escape') { neueKarte = false; karteTitel = '' } }}></textarea>
        <label class="ideewahl"><input type="checkbox" bind:checked={alsIdee} /> Ideenticket (Notiz, ohne Zeiten)</label>
        <div class="reihe">
          <button class="btn primaer" onclick={karteAbschicken}>Hinzufügen</button>
          <button class="btn geist" onclick={() => { neueKarte = false; karteTitel = ''; alsIdee = false }}>Abbrechen</button>
        </div>
      </div>
    {:else}
      <button class="add" onclick={() => (neueKarte = true)}><i class="fa-solid fa-plus" aria-hidden="true"></i> Karte</button>
    {/if}
  </section>
{/if}

<style>
  .col {
    flex: 0 0 286px;
    width: 286px;
    height: 100%;
    background: var(--surface-col);
    border: 1px solid var(--border);
    border-radius: var(--r-xl);
    padding: 9px;
    display: flex;
    flex-direction: column;
    position: relative;
  }
  .zu {
    flex: 0 0 46px;
    width: 46px;
    height: 100%;
    background: var(--surface-col);
    border: 1px solid var(--border);
    border-radius: var(--r-xl);
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 10px 0 8px;
  }
  .zukopf {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 10px;
    color: var(--text-2);
    cursor: grab;
    padding-bottom: 10px;
  }
  .zukopf:active {
    cursor: grabbing;
  }
  .zukopf:hover {
    color: var(--text-1);
  }
  .griffzu {
    font-size: 12px;
    color: var(--text-3);
    line-height: 1;
  }
  .zukopf:hover .griffzu {
    color: var(--hl-primary-text);
  }
  .zukopf .dot {
    width: 8px;
    height: 8px;
    border-radius: 3px;
  }
  .vtitel {
    writing-mode: vertical-rl;
    font-family: var(--font-display);
    font-size: 12.5px;
    font-weight: 600;
    color: var(--text-1);
    letter-spacing: 0.02em;
  }
  .vzahl {
    font-size: 11px;
    color: var(--text-3);
  }
  .zuliste {
    flex: 1;
    min-height: 20px;
    width: 100%;
    overflow-y: auto;
    overflow-x: hidden;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 5px;
    padding: 4px 0;
  }
  .slim {
    width: 22px;
    height: 6px;
    border-radius: 3px;
    opacity: 0.7;
  }
  .slim.ph {
    width: 28px;
    height: 18px;
    background: var(--hl-primary-weich);
    border: 1.5px dashed var(--hl-primary);
    opacity: 1;
  }
  .zuliste > div {
    width: 100%;
    display: flex;
    justify-content: center;
  }
  header {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 2px 2px 8px;
    position: relative;
  }
  /* Ganze linke Kopfzeile ist der Zieh-Griff: grosses, klares Ziel zum Umsortieren. */
  .zieh {
    flex: 1;
    min-width: 0;
    display: flex;
    align-items: center;
    gap: 6px;
    cursor: grab;
    padding: 2px 0;
    border-radius: var(--r-s);
  }
  .zieh:hover {
    background: var(--surface-3);
  }
  .zieh:active {
    cursor: grabbing;
  }
  .griff {
    color: var(--text-3);
    font-size: 13px;
    flex: none;
  }
  .zieh:hover .griff {
    color: var(--hl-primary-text);
  }
  .punkt {
    width: 8px;
    height: 8px;
    border-radius: 3px;
    flex: none;
  }
  .titel {
    font-family: var(--font-display);
    font-size: 13px;
    font-weight: 600;
    flex: 1;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: var(--text-1);
  }
  .zaehler {
    font-size: 11px;
    color: var(--text-3);
    font-variant-numeric: tabular-nums;
  }
  .zaehler.warn {
    color: var(--prio-mittel);
    font-weight: 600;
  }
  .zaehler.ueber {
    color: var(--gefahr, #e5484d);
    font-weight: 700;
  }
  .zeitfilter {
    border: 1px solid var(--border-2);
    background: var(--surface-2);
    color: var(--text-2);
    border-radius: var(--r-s);
    font-size: 10.5px;
    padding: 2px 4px;
    max-width: 74px;
  }
  .zeitfilter:hover {
    color: var(--text-1);
    border-color: var(--hl-primary);
  }
  .hbtn {
    border: none;
    background: transparent;
    color: var(--text-3);
    width: 22px;
    height: 22px;
    border-radius: var(--r-s);
    font-size: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .hbtn:hover,
  .hbtn.aktiv {
    background: var(--surface-3);
    color: var(--text-1);
  }
  .menu {
    position: absolute;
    top: 28px;
    right: 0;
    z-index: 20;
    background: var(--surface-3);
    border: 1px solid var(--border-2);
    border-radius: var(--r-l);
    padding: 5px;
    width: 184px;
    box-shadow: var(--schatten-pop);
  }
  .menu button {
    display: flex;
    align-items: center;
    gap: 10px;
    width: 100%;
    border: none;
    background: transparent;
    color: var(--text-2);
    font-size: 12.5px;
    padding: 7px 8px;
    border-radius: var(--r-s);
    text-align: left;
  }
  .menu button:hover:not(:disabled) {
    background: var(--surface-1);
    color: var(--text-1);
  }
  .menu button:disabled {
    opacity: 0.35;
    cursor: default;
  }
  .menu button.rot {
    color: var(--gefahr);
  }
  .menu .trenner {
    height: 1px;
    background: var(--border);
    margin: 4px 2px;
  }
  .wip {
    height: 3px;
    border-radius: 3px;
    background: var(--border);
    margin: 0 2px 9px;
    overflow: hidden;
  }
  .wip span {
    display: block;
    height: 100%;
    border-radius: 3px;
  }
  .liste {
    flex: 1;
    min-height: 10px;
    overflow-y: auto;
    overflow-x: hidden;
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding: 2px;
    margin: 0 -2px;
  }
  .fertiginfo {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    padding: 6px 2px 2px;
    font-size: 11px;
    color: var(--text-3);
  }
  .fertiginfo .mehr {
    border: 1px solid var(--border);
    background: var(--surface-1, transparent);
    color: var(--text-2);
    border-radius: var(--r-m, 6px);
    padding: 3px 10px;
    font: inherit;
    cursor: pointer;
  }
  .fertiginfo .mehr:hover:not(:disabled) {
    color: var(--hl-primary-text);
    border-color: var(--hl-primary);
  }
  .fertiginfo .mehr:disabled {
    opacity: 0.6;
    cursor: default;
  }
  .platzhalter {
    border: 2px dashed var(--hl-primary);
    background: var(--hl-primary-weich);
    border-radius: var(--r-l);
    height: 58px;
    flex: none;
  }

  /* Drop-Vorschau (svelte-dnd-action): das an Ort und Stelle gehaltene Original haelt die
     Bibliothek per Inline-Stil auf visibility:hidden - dadurch bleibt der Platz reserviert
     und die echte Karte verborgen. Statt diesen Inline-Stil zu ueberschreiben (was nur mit
     !important ginge), wird die Stichlinie als eigenes ::before gezeichnet: dessen
     visibility setzen wir per Regel auf visible (ein Pseudo-Element hat keinen
     konkurrierenden Inline-Stil), sodass nur die abgerundete gestrichelte Vorschau
     erscheint - passend zum Kartenradius, kein eckiger Rahmen. */
  .liste :global([data-is-dnd-shadow-item-internal]) {
    position: relative;
  }
  .liste :global([data-is-dnd-shadow-item-internal]::before) {
    content: '';
    position: absolute;
    inset: 0;
    visibility: visible;
    border: 2px dashed var(--hl-primary);
    border-radius: var(--r-l);
    background: var(--hl-primary-weich);
    pointer-events: none;
  }
  .zuliste :global([data-is-dnd-shadow-item-internal]) {
    position: relative;
  }
  .zuliste :global([data-is-dnd-shadow-item-internal]::before) {
    content: '';
    position: absolute;
    inset: 0;
    visibility: visible;
    border: 1.5px dashed var(--hl-primary);
    border-radius: var(--r-s);
    background: var(--hl-primary-weich);
    pointer-events: none;
  }
  .add {
    margin-top: 8px;
    display: flex;
    align-items: center;
    gap: 7px;
    width: 100%;
    border: none;
    background: transparent;
    color: var(--text-3);
    font-size: 12.5px;
    padding: 8px;
    border-radius: var(--r-m);
  }
  .add:hover {
    background: var(--surface-3);
    color: var(--text-1);
  }
  .composer {
    margin-top: 8px;
    display: flex;
    flex-direction: column;
    gap: 7px;
  }
  .bearbeiten {
    display: flex;
    flex-direction: column;
    gap: 7px;
    padding: 2px 2px 9px;
  }
  .feld {
    width: 100%;
    border: 1px solid var(--border-2);
    background: var(--surface-2);
    color: var(--text-1);
    border-radius: var(--r-m);
    padding: 8px 9px;
    font-size: 13px;
    resize: vertical;
  }
  .reihe {
    display: flex;
    gap: 7px;
  }
  .ideewahl {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 11.5px;
    color: var(--text-3);
    margin: 6px 0;
  }
  .btn {
    border: 1px solid var(--border);
    border-radius: var(--r-m);
    padding: 6px 12px;
    font-size: 12.5px;
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
</style>
