<script lang="ts">
  // Identitaet: einmalige Erstwahl "Wer bist du?". Die gewaehlte Person treibt die
  // Personen-Sicht (Stunden, Tab-Titel) und ist die Grundlage fuer eigene Daten.
  // Erscheint nur, wenn Personen angelegt sind und noch keine Wahl getroffen wurde.
  import { onMount } from 'svelte'
  import { ladePersonen, type Person } from './api'
  import { setzePersonSicht, identitaetGewaehlt, merkeIdentitaetGewaehlt } from './personSicht.svelte'

  let personen = $state<Person[]>([])
  let sichtbar = $state(false)

  onMount(async () => {
    if (identitaetGewaehlt()) return
    try {
      personen = (await ladePersonen()).filter((p) => p.aktiv)
    } catch {
      return
    }
    if (personen.length) sichtbar = true
    else merkeIdentitaetGewaehlt() // ohne Personen nichts zu wählen
  })

  function waehle(id: string): void {
    setzePersonSicht(id)
    merkeIdentitaetGewaehlt()
    sichtbar = false
  }
</script>

{#if sichtbar}
  <div class="tor" role="dialog" aria-label="Wer bist du?">
    <div class="box">
      <h2><i class="fa-solid fa-user" aria-hidden="true"></i> Wer bist du?</h2>
      <p class="hint">Wähle deine Person - dann zeigen die Stunden-Leiste und der Tab-Titel deine eigenen Werte. Du kannst das jederzeit oben in der Stunden-Leiste umstellen.</p>
      <div class="liste">
        {#each personen as p (p.id)}
          <button class="wahl" onclick={() => waehle(p.id)}>
            <span class="k">{p.kuerzel ?? ''}</span> {p.name}
          </button>
        {/each}
        <button class="wahl team" onclick={() => waehle('')}>
          <i class="fa-solid fa-users" aria-hidden="true"></i> Team-Gesamt (alle)
        </button>
      </div>
    </div>
  </div>
{/if}

<style>
  .tor {
    position: fixed;
    inset: 0;
    z-index: 150;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .box {
    width: 380px;
    max-width: 92vw;
    background: var(--surface-1);
    border: 1px solid var(--border-2);
    border-radius: var(--r-xl);
    padding: 22px;
    box-shadow: var(--schatten-pop);
  }
  h2 {
    margin: 0 0 6px;
    font-family: var(--font-display);
    font-size: 18px;
    color: var(--text-1);
    display: flex;
    align-items: center;
    gap: 9px;
  }
  .hint {
    margin: 0 0 14px;
    font-size: 12.5px;
    color: var(--text-2);
    line-height: 1.5;
  }
  .liste {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  .wahl {
    text-align: left;
    border: 1px solid var(--border-2);
    background: var(--surface-2);
    color: var(--text-1);
    border-radius: var(--r-m);
    padding: 10px 12px;
    font-size: 13px;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .wahl:hover {
    border-color: var(--hl-primary);
    color: var(--hl-primary-text);
  }
  .wahl .k {
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--text-3);
  }
  .wahl.team {
    color: var(--text-2);
    margin-top: 4px;
  }
</style>
