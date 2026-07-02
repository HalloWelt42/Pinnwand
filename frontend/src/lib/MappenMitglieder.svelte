<script lang="ts">
  import type { Person } from './types'
  import { ladeMappenMitglieder, setzeMappenMitglied, entferneMappenMitglied } from './api'
  import Modal from './Modal.svelte'

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

<Modal ariaLabel="Projekt-Mitglieder" breite="min(420px, 100%)" maxHoehe="min(75vh, 620px)" {onSchliessen}>
  <header>
    <div class="kopf"><i class="fa-solid fa-users" aria-hidden="true"></i> Mitglieder - {titel}</div>
    <button class="x" aria-label="Schliessen" onclick={onSchliessen}><i class="fa-solid fa-xmark" aria-hidden="true"></i></button>
  </header>
  <p class="hint">
    Nur Mitglieder sehen dieses Projekt und seine Boards. Ohne Mitglieder ist das Projekt
    für alle sichtbar (geteilt). Admins sehen immer alle Projekte; Mitglieder können
    die Mitgliederliste ihres Projekts selbst pflegen.
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
</Modal>

<style>
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
