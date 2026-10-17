<script lang="ts">
  // Band über der App, solange der Server eine neuere Fassung meldet (lib/fassung.svelte.ts).
  import { fassung, ruhig } from './fassung.svelte'
</script>

{#if fassung.neu}
  <div class="fb" role="status">
    <i class="fa-solid fa-rotate" aria-hidden="true"></i>
    <span class="text">
      <strong>Neue Fassung {fassung.neu} ist da.</strong>
      {ruhig() ? 'Beim nächsten Ortswechsel lädt Pinnwand sie von selbst.' : 'Sie lädt beim nächsten Ortswechsel von selbst, sobald nichts mehr läuft und nichts Ungespeichertes offen ist.'}
    </span>
    <button class="btn" onclick={() => location.reload()}><i class="fa-solid fa-rotate" aria-hidden="true"></i> Jetzt neu laden</button>
  </div>
{/if}

<style>
  .fb {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 7px 16px;
    background: var(--hl-primary-weich);
    border-bottom: 1px solid var(--hl-primary);
    color: var(--text-1);
    font-size: 12.5px;
  }
  .fb > i {
    color: var(--hl-primary-text);
  }
  .text {
    flex: 1;
    min-width: 0;
  }
  .btn {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    border: 1px solid transparent;
    background: var(--hl-primary);
    color: var(--hl-on-primary);
    border-radius: var(--r-m);
    padding: 6px 12px;
    font-size: 12.5px;
    font-weight: 500;
  }
  .btn:hover {
    filter: brightness(1.08);
  }
</style>
