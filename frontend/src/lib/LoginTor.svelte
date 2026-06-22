<script lang="ts">
  // Erscheint nur, wenn das Backend ein UI-Token verlangt (401). Nach Eingabe wird
  // das Token gemerkt und die App neu geladen, damit alle Anfragen es mitschicken.
  import { uiAuth, setzeUiToken } from './uiAuth.svelte'

  let token = $state('')
  let fehler = $state(false)

  function anmelden(): void {
    const t = token.trim()
    if (!t) {
      fehler = true
      return
    }
    setzeUiToken(t)
    location.reload()
  }
</script>

{#if uiAuth.noetig}
  <div class="tor" role="dialog" aria-label="Anmeldung">
    <div class="box">
      <h2><i class="fa-solid fa-lock" aria-hidden="true"></i> Anmeldung</h2>
      <p class="hint">Diese Pinnwand ist mit einem Zugangs-Token geschützt. Bitte das Token eingeben.</p>
      <input
        class="feld"
        class:fehler
        type="password"
        placeholder="Zugangs-Token"
        bind:value={token}
        onkeydown={(e) => { if (e.key === 'Enter') anmelden() }}
      />
      <button class="btn" onclick={anmelden}>Anmelden</button>
    </div>
  </div>
{/if}

<style>
  .tor {
    position: fixed;
    inset: 0;
    z-index: 200;
    background: var(--surface-col);
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .box {
    width: 360px;
    max-width: 90vw;
    background: var(--surface-1);
    border: 1px solid var(--border-2);
    border-radius: var(--r-xl);
    padding: 24px;
    box-shadow: var(--schatten-pop);
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  h2 {
    margin: 0;
    font-family: var(--font-display);
    font-size: 18px;
    color: var(--text-1);
    display: flex;
    align-items: center;
    gap: 9px;
  }
  .hint {
    margin: 0;
    font-size: 12.5px;
    color: var(--text-2);
    line-height: 1.5;
  }
  .feld {
    border: 1px solid var(--border-2);
    background: var(--surface-2);
    color: var(--text-1);
    border-radius: var(--r-m);
    padding: 10px 12px;
    font-size: 13px;
  }
  .feld.fehler {
    border-color: var(--gefahr);
  }
  .btn {
    border: 1px solid transparent;
    background: var(--hl-primary);
    color: var(--hl-on-primary);
    border-radius: var(--r-m);
    padding: 10px 16px;
    font-size: 13px;
    font-weight: 600;
  }
</style>
