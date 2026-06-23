<script lang="ts">
  import { onMount } from 'svelte'
  import { ki, ladeKiStatus } from '../ki.svelte'
  import { kiAufgabe, type KiVorschlag } from '../api'

  // Wiederverwendbarer KI-Knopf fuer datenreiche Stellen. Die KI ist immer die
  // zweite Option: sie schlaegt vor, der Mensch korrigiert per Checkliste und
  // entscheidet mit "Uebernehmen". Angewendet wird nichts von allein.
  let {
    typ,
    kontext,
    onUebernehmen,
    titel = 'KI-Vorschlag',
    platzhalter = 'Was soll die KI auswaehlen? (optional)',
    knopfText = '',
    uebernehmenText = 'Uebernehmen',
  }: {
    typ: string
    kontext: () => Record<string, unknown>
    onUebernehmen: (ausgewaehlte: KiVorschlag[]) => void | Promise<void>
    titel?: string
    platzhalter?: string
    knopfText?: string
    uebernehmenText?: string
  } = $props()

  let offen = $state(false)
  let laedt = $state(false)
  let anweisung = $state('')
  let vorschlaege = $state<KiVorschlag[]>([])
  let auswahl = $state<Record<string, boolean>>({})
  let meldung = $state('')
  let gefragt = $state(false)

  onMount(() => {
    if (!ki.geprueft) void ladeKiStatus()
  })

  const anzahlGewaehlt = $derived(vorschlaege.filter((v) => auswahl[v.id]).length)

  function umschalten(): void {
    offen = !offen
    if (offen && !ki.geprueft) void ladeKiStatus()
  }

  function schliessen(): void {
    offen = false
  }

  async function vorschlagen(): Promise<void> {
    laedt = true
    meldung = ''
    vorschlaege = []
    gefragt = true
    try {
      const antwort = await kiAufgabe(typ, kontext(), anweisung)
      if (!antwort.ok) {
        meldung = 'Das KI-Modell ist gerade nicht erreichbar. Bitte manuell auswaehlen.'
      } else if (!antwort.vorschlaege.length) {
        meldung = 'Die KI hat keinen passenden Vorschlag gefunden.'
      } else {
        vorschlaege = antwort.vorschlaege
        const start: Record<string, boolean> = {}
        for (const v of antwort.vorschlaege) start[v.id] = v.vorgewaehlt
        auswahl = start
      }
    } catch {
      meldung = 'KI-Anfrage fehlgeschlagen. Bitte manuell auswaehlen.'
    } finally {
      laedt = false
    }
  }

  async function uebernehmen(): Promise<void> {
    const gewaehlt = vorschlaege.filter((v) => auswahl[v.id])
    if (!gewaehlt.length) return
    await onUebernehmen(gewaehlt)
    zuruecksetzen()
    offen = false
  }

  function zuruecksetzen(): void {
    vorschlaege = []
    auswahl = {}
    meldung = ''
    gefragt = false
  }
</script>

{#if ki.verfuegbar}
  <span class="ki-wrap">
    <button
      type="button"
      class="ki-knopf"
      class:aktiv={offen}
      title={`${titel}${ki.modell ? ' - ' + ki.modell : ''}`}
      aria-label={titel}
      onclick={umschalten}
    >
      <i class="fa-solid fa-wand-magic-sparkles" aria-hidden="true"></i>{#if knopfText}<span class="kt">{knopfText}</span>{/if}
    </button>

    {#if offen}
      <!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
      <div class="ki-backdrop" role="presentation" onclick={schliessen}></div>
      <div class="ki-panel" role="dialog" aria-label={titel}>
        <div class="ki-kopf">
          <span class="ki-titel"><i class="fa-solid fa-wand-magic-sparkles" aria-hidden="true"></i> {titel}</span>
          <button type="button" class="ki-x" aria-label="Schliessen" onclick={schliessen}><i class="fa-solid fa-xmark" aria-hidden="true"></i></button>
        </div>

        <textarea
          class="ki-anweisung"
          rows="2"
          placeholder={platzhalter}
          bind:value={anweisung}
          onkeydown={(e) => { if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) { e.preventDefault(); void vorschlagen() } }}
        ></textarea>

        <div class="ki-aktionen">
          <button type="button" class="ki-vorschlag" onclick={vorschlagen} disabled={laedt}>
            {#if laedt}<i class="fa-solid fa-spinner fa-spin" aria-hidden="true"></i> Denkt nach...{:else}<i class="fa-solid fa-lightbulb" aria-hidden="true"></i> Vorschlagen{/if}
          </button>
          <span class="ki-hinweis">KI schlaegt nur vor - du entscheidest.</span>
        </div>

        {#if meldung}
          <p class="ki-meldung">{meldung}</p>
        {/if}

        {#if vorschlaege.length}
          <ul class="ki-liste">
            {#each vorschlaege as v (v.id)}
              <li class="ki-zeile">
                <label class="ki-label">
                  <input type="checkbox" checked={auswahl[v.id]} onchange={(e) => (auswahl[v.id] = e.currentTarget.checked)} />
                  <span class="ki-text">
                    <span class="ki-haupt">{v.text}</span>
                    {#if v.begruendung}<span class="ki-grund">{v.begruendung}</span>{/if}
                  </span>
                </label>
              </li>
            {/each}
          </ul>
          <div class="ki-fuss">
            <button type="button" class="ki-text-knopf" onclick={zuruecksetzen}>Verwerfen</button>
            <button type="button" class="ki-primaer" onclick={uebernehmen} disabled={!anzahlGewaehlt}>
              {uebernehmenText}{anzahlGewaehlt ? ` (${anzahlGewaehlt})` : ''}
            </button>
          </div>
        {:else if gefragt && !laedt && !meldung}
          <p class="ki-meldung">Kein Vorschlag.</p>
        {/if}
      </div>
    {/if}
  </span>
{/if}

<style>
  .ki-wrap { position: relative; display: inline-flex; }
  .ki-knopf {
    display: inline-flex; align-items: center; gap: 6px;
    border: 1px solid var(--border-2); background: var(--surface-2); color: var(--hl-primary);
    border-radius: var(--r-s); padding: 5px 9px; font-size: 12px; cursor: pointer;
  }
  .ki-knopf:hover { border-color: var(--hl-primary); }
  .ki-knopf.aktiv { border-color: var(--hl-primary); background: var(--surface-3, var(--surface-2)); }
  .ki-knopf .kt { font-size: 12px; }

  .ki-backdrop { position: fixed; inset: 0; z-index: 90; }
  .ki-panel {
    position: absolute; z-index: 91; top: calc(100% + 6px); right: 0;
    width: 340px; max-width: 88vw; max-height: 70vh; overflow-y: auto;
    background: var(--surface-col); border: 1px solid var(--border-2); border-radius: var(--r-l, var(--r-m));
    padding: 12px; box-shadow: var(--schatten-pop);
  }
  .ki-kopf { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
  .ki-titel { font-family: var(--font-display); font-size: 13px; color: var(--text-1); display: flex; align-items: center; gap: 7px; }
  .ki-titel i { color: var(--hl-primary); }
  .ki-x { border: none; background: transparent; color: var(--text-3); cursor: pointer; font-size: 13px; padding: 2px 4px; }
  .ki-x:hover { color: var(--text-1); }

  .ki-anweisung {
    width: 100%; box-sizing: border-box; resize: vertical;
    border: 1px solid var(--border); background: var(--surface-2); color: var(--text-1);
    border-radius: var(--r-s); padding: 7px 8px; font-size: 12.5px; font-family: inherit;
  }
  .ki-aktionen { display: flex; align-items: center; gap: 9px; margin: 8px 0; }
  .ki-vorschlag {
    display: inline-flex; align-items: center; gap: 6px;
    border: 1px solid var(--hl-primary); background: var(--hl-primary); color: var(--hl-on-primary);
    border-radius: var(--r-s); padding: 6px 11px; font-size: 12px; cursor: pointer;
  }
  .ki-vorschlag:disabled { opacity: 0.6; cursor: default; }
  .ki-hinweis { font-size: 10.5px; color: var(--text-3); line-height: 1.3; }

  .ki-meldung { margin: 6px 0; font-size: 12px; color: var(--text-2); }

  .ki-liste { list-style: none; margin: 4px 0 0; padding: 0; display: flex; flex-direction: column; gap: 2px; }
  .ki-zeile { border-bottom: 1px solid var(--border); }
  .ki-zeile:last-child { border-bottom: none; }
  .ki-label { display: flex; align-items: flex-start; gap: 8px; padding: 7px 2px; cursor: pointer; }
  .ki-label input { margin-top: 2px; flex: 0 0 auto; }
  .ki-text { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
  .ki-haupt { font-size: 12.5px; color: var(--text-1); }
  .ki-grund { font-size: 11px; color: var(--text-3); line-height: 1.35; }

  .ki-fuss { display: flex; align-items: center; justify-content: space-between; margin-top: 10px; }
  .ki-text-knopf { border: none; background: transparent; color: var(--text-3); font-size: 12px; cursor: pointer; padding: 6px 4px; }
  .ki-text-knopf:hover { color: var(--text-1); }
  .ki-primaer {
    border: 1px solid transparent; background: var(--hl-primary); color: var(--hl-on-primary);
    font-weight: 500; border-radius: var(--r-s); padding: 7px 13px; font-size: 12px; cursor: pointer;
  }
  .ki-primaer:disabled { opacity: 0.5; cursor: default; }
</style>
