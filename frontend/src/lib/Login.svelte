<script lang="ts">
  // Echte Anmeldung mit Name (oder Kuerzel) + Passwort. Erscheint als Vollbild-Sperre,
  // wenn die Anmeldung erforderlich ist und noch keine Sitzung besteht. Nach Erfolg
  // wird die App neu geladen, damit alle Anfragen die Sitzung mitschicken.
  import { auth } from './auth.svelte'
  import { anmelden } from './api'
  import { VERSION } from './version'

  let kennung = $state('')
  let passwort = $state('')
  let fehler = $state('')
  let laeuft = $state(false)

  const sichtbar = $derived(auth.geladen && auth.erforderlich && !auth.angemeldet)

  async function los(): Promise<void> {
    if (!kennung.trim() || !passwort) {
      fehler = 'Bitte Name und Passwort eingeben.'
      return
    }
    laeuft = true
    fehler = ''
    try {
      if (await anmelden(kennung.trim(), passwort)) {
        location.reload()
      } else {
        fehler = 'Name oder Passwort ist falsch.'
        passwort = ''
      }
    } catch {
      fehler = 'Anmeldung nicht möglich.'
    } finally {
      laeuft = false
    }
  }
</script>

{#if sichtbar}
  <div class="tor" role="dialog" aria-label="Anmeldung" aria-modal="true">
    <div class="box">
      <div class="marke"><i class="fa-solid fa-thumbtack" aria-hidden="true"></i> Pinnwand</div>
      <h2><i class="fa-solid fa-right-to-bracket" aria-hidden="true"></i> Anmelden</h2>
      <p class="hint">Bitte mit Name oder Kürzel und Passwort anmelden.</p>
      <input
        class="feld"
        placeholder="Name oder Kürzel"
        autocomplete="username"
        bind:value={kennung}
        onkeydown={(e) => { if (e.key === 'Enter') los() }}
      />
      <input
        class="feld"
        class:fehler={!!fehler}
        type="password"
        placeholder="Passwort"
        autocomplete="current-password"
        bind:value={passwort}
        onkeydown={(e) => { if (e.key === 'Enter') los() }}
      />
      {#if fehler}<p class="meld">{fehler}</p>{/if}
      <button class="btn" onclick={los} disabled={laeuft}>
        {laeuft ? 'Anmelden ...' : 'Anmelden'}
      </button>
      <div class="fuss">v{VERSION}</div>
    </div>
  </div>
{/if}

<style>
  .tor {
    position: fixed;
    inset: 0;
    z-index: 300;
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
    gap: 11px;
  }
  .marke {
    font-family: var(--font-display);
    font-size: 13px;
    color: var(--hl-primary-text, var(--hl-primary));
    display: flex;
    align-items: center;
    gap: 8px;
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
  .hint { margin: 0; font-size: 12.5px; color: var(--text-2); line-height: 1.5; }
  .feld {
    border: 1px solid var(--border-2);
    background: var(--surface-2);
    color: var(--text-1);
    border-radius: var(--r-m);
    padding: 10px 12px;
    font-size: 13px;
  }
  .feld.fehler { border-color: var(--gefahr); }
  .meld { margin: 0; font-size: 12px; color: var(--gefahr, #e5484d); }
  .btn {
    border: 1px solid transparent;
    background: var(--hl-primary);
    color: var(--hl-on-primary);
    border-radius: var(--r-m);
    padding: 10px 16px;
    font-size: 13px;
    font-weight: 600;
  }
  .btn:disabled { opacity: 0.6; }
  .fuss { text-align: center; font-size: 10.5px; color: var(--text-3); }
</style>
