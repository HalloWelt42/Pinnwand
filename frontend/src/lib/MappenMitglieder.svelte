<script lang="ts">
  import type { Person } from './types'
  import { ladeMappenMitglieder, setzeMappenMitglied, entferneMappenMitglied } from './api'

  let { mappeId, titel, personen, onSchliessen }: {
    mappeId: string
    titel: string
    personen: Person[]
    onSchliessen: () => void
  } = $props()

  let mitglieder = $state<Set<string>>(new Set())
  let laedt = $state(true)

  $effect(() => {
    void mappeId
    laedt = true
    ladeMappenMitglieder(mappeId)
      .then((ids) => { mitglieder = new Set(ids) })
      .catch(() => { mitglieder = new Set() })
      .finally(() => (laedt = false))
  })

  async function umschalten(pid: string): Promise<void> {
    if (mitglieder.has(pid)) {
      await entferneMappenMitglied(mappeId, pid)
      mitglieder.delete(pid)
    } else {
      await setzeMappenMitglied(mappeId, pid)
      mitglieder.add(pid)
    }
    mitglieder = new Set(mitglieder)
  }
</script>

<div class="huelle" role="button" tabindex="-1" onclick={onSchliessen} onkeydown={(e) => { if (e.key === 'Escape') onSchliessen() }}>
  <div class="fenster" role="dialog" aria-label="Projekt-Mitglieder" tabindex="-1" onclick={(e) => e.stopPropagation()} onkeydown={() => {}}>
    <header>
      <div class="kopf"><i class="fa-solid fa-users" aria-hidden="true"></i> Mitglieder - {titel}</div>
      <button class="x" aria-label="Schliessen" onclick={onSchliessen}><i class="fa-solid fa-xmark" aria-hidden="true"></i></button>
    </header>
    <p class="hint">
      Nur Mitglieder sehen dieses Projekt und seine Boards. Ohne Mitglieder ist das Projekt
      für alle sichtbar (geteilt). Admins sehen immer alle Projekte.
    </p>
    {#if laedt}
      <p class="leer">Lädt ...</p>
    {:else}
      <div class="liste">
        {#each personen as p (p.id)}
          <label class="zeile">
            <input type="checkbox" checked={mitglieder.has(p.id)} onchange={() => umschalten(p.id)} />
            <span class="nam">{p.name}</span>
            {#if p.kuerzel}<span class="krz">{p.kuerzel}</span>{/if}
          </label>
        {/each}
        {#if personen.length === 0}<p class="leer">Keine Personen vorhanden.</p>{/if}
      </div>
      {#if mitglieder.size === 0}<p class="geteilt">Aktuell für alle sichtbar (keine Mitglieder).</p>{/if}
    {/if}
  </div>
</div>

<style>
  .huelle {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.45);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 60;
    padding: 24px;
  }
  .fenster {
    width: min(420px, 100%);
    max-height: min(75vh, 620px);
    background: var(--surface-1, #1b1b1f);
    border: 1px solid var(--border);
    border-radius: var(--r-xl, 14px);
    box-shadow: var(--schatten-lift, 0 12px 40px rgba(0, 0, 0, 0.4));
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }
  header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 14px;
    border-bottom: 1px solid var(--border);
  }
  .kopf {
    display: flex;
    align-items: center;
    gap: 8px;
    color: var(--text-1);
    font-weight: 600;
  }
  .x {
    border: none;
    background: transparent;
    color: var(--text-3);
    cursor: pointer;
    font-size: 16px;
    padding: 4px 6px;
  }
  .x:hover { color: var(--text-1); }
  .hint {
    font-size: 12px;
    color: var(--text-3);
    line-height: 1.5;
    margin: 10px 14px 4px;
  }
  .liste {
    overflow-y: auto;
    padding: 6px 10px 10px;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }
  .zeile {
    display: flex;
    align-items: center;
    gap: 9px;
    padding: 7px 8px;
    border-radius: var(--r-m, 6px);
    cursor: pointer;
    color: var(--text-1);
  }
  .zeile:hover { background: var(--surface-col, transparent); }
  .zeile .krz {
    margin-left: auto;
    font-size: 11px;
    color: var(--text-3);
    font-variant-numeric: tabular-nums;
  }
  .leer { color: var(--text-3); font-size: 13px; padding: 12px 14px; }
  .geteilt { color: var(--text-3); font-size: 11.5px; padding: 4px 14px 12px; font-style: italic; }
</style>
