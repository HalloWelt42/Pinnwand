<script lang="ts">
  import { sucheInhalte, type SuchTreffer } from '../../api'
  import { oeffneKarte } from '../../navigation.svelte'
  import { kopfSuche } from '../../suchkopf.svelte'

  // Suche ist global; boardId wird hier nicht benötigt (Pflichtprop der Ansichts-Schnittstelle).
  let { boardId }: { boardId: string } = $props()
  $effect(() => void boardId)

  let treffer = $state<SuchTreffer[]>([])
  let modus = $state('stichwort')
  let laeuft = $state(false)

  // Der Suchbegriff (und die Spracheingabe) kommen zentral aus dem Kopf der App.
  const frage = $derived(kopfSuche.q)
  $effect(() => {
    kopfSuche.stand // bei jeder neuen Kopf-Anfrage erneut suchen
    starteSuche(kopfSuche.q)
  })

  async function starteSuche(q: string): Promise<void> {
    if (!q.trim()) {
      treffer = []
      return
    }
    laeuft = true
    try {
      const e = await sucheInhalte(q, 20)
      treffer = e.treffer
      modus = e.modus
    } catch {
      treffer = []
    } finally {
      laeuft = false
    }
  }

  function oeffne(t: SuchTreffer): void {
    if (t.board_id) oeffneKarte(t.board_id, t.karte_id)
  }
</script>

<div class="suche">
  {#if frage.trim()}
    <div class="zeile-info">
      <span class="begriff">Suche: <b>{frage}</b></span>
      <span class="modus" title="Suchmodus">
        <i class="fa-solid {modus === 'hybrid' ? 'fa-wand-magic-sparkles' : 'fa-font'}" aria-hidden="true"></i>
        {modus === 'hybrid' ? 'Semantisch + Stichwort' : 'Stichwort'}
      </span>
      {#if laeuft}<span class="lade">sucht ...</span>{/if}
    </div>
  {:else}
    <p class="hinweis"><i class="fa-solid fa-magnifying-glass" aria-hidden="true"></i> Tippe oben im Kopf in die Suche - oder nutze das Mikrofon fuer Spracheingabe.</p>
  {/if}

  {#if frage.trim() && !treffer.length && !laeuft}
    <p class="leer">Keine Treffer.</p>
  {/if}

  <ul class="liste">
    {#each treffer as t (t.karte_id)}
      <li>
        <button class="treffer" onclick={() => oeffne(t)}>
          <span class="key">{t.schluessel ?? ''}</span>
          <span class="titel">{t.titel}</span>
          <span class="badges">
            {#if t.quelle === 'semantisch'}
              <span class="badge sem">semantisch{#if t.score} {Math.round(t.score * 100)}%{/if}</span>
            {:else}
              <span class="badge stw">Stichwort</span>
            {/if}
          </span>
        </button>
      </li>
    {/each}
  </ul>
</div>

<style>
  .suche {
    height: 100%;
    overflow-y: auto;
    padding: 18px;
    max-width: 820px;
    margin: 0 auto;
    width: 100%;
  }
  .hinweis {
    display: flex;
    align-items: center;
    gap: 9px;
    color: var(--text-3);
    font-size: 13px;
    padding: 10px 12px;
    border: 1px dashed var(--border-2);
    border-radius: var(--r-m);
  }
  .zeile-info {
    display: flex;
    align-items: center;
    gap: 14px;
    margin: 2px 4px 10px;
    font-size: 11.5px;
    color: var(--text-3);
  }
  .begriff {
    color: var(--text-2);
  }
  .modus {
    display: inline-flex;
    align-items: center;
    gap: 6px;
  }
  .leer {
    color: var(--text-3);
    font-size: 13px;
    padding: 8px 4px;
  }
  .liste {
    list-style: none;
    margin: 6px 0 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
  .treffer {
    width: 100%;
    display: flex;
    align-items: center;
    gap: 12px;
    text-align: left;
    border: 1px solid var(--border);
    background: var(--surface-col);
    border-radius: var(--r-m);
    padding: 11px 13px;
    color: var(--text-1);
    cursor: pointer;
  }
  .treffer:hover {
    background: var(--surface-3);
    border-color: var(--border-2);
  }
  .key {
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--text-3);
    flex: none;
    min-width: 56px;
  }
  .titel {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .badges {
    flex: none;
  }
  .badge {
    font-size: 10.5px;
    padding: 2px 8px;
    border-radius: 999px;
  }
  .badge.sem {
    background: var(--hl-primary-weich);
    color: var(--hl-primary-text);
  }
  .badge.stw {
    background: var(--surface-2);
    color: var(--text-3);
  }
</style>
