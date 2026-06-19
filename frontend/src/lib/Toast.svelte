<script lang="ts">
  import { toasts, entferne } from './toaster.svelte'
  import type { ToastEintrag } from './toaster.svelte'

  async function rueckgaengig(t: ToastEintrag) {
    const u = t.undo
    entferne(t.id)
    if (u) await u()
  }
</script>

<div class="wrap">
  {#each toasts as t (t.id)}
    <div class="toast">
      <span class="txt">{t.text}</span>
      {#if t.undo}<button class="undo" onclick={() => rueckgaengig(t)}>Rückgängig</button>{/if}
      <button class="zu" aria-label="Schließen" onclick={() => entferne(t.id)}><i class="fa-solid fa-xmark" aria-hidden="true"></i></button>
    </div>
  {/each}
</div>

<style>
  .wrap {
    position: fixed;
    left: 50%;
    bottom: 22px;
    transform: translateX(-50%);
    z-index: 60;
    display: flex;
    flex-direction: column;
    gap: 8px;
    align-items: center;
  }
  .toast {
    display: flex;
    align-items: center;
    gap: 14px;
    background: var(--surface-3);
    border: 1px solid var(--border-2);
    border-radius: var(--r-l);
    padding: 10px 12px 10px 15px;
    box-shadow: var(--schatten-pop);
    color: var(--text-1);
    font-size: 13px;
  }
  .undo {
    border: none;
    background: transparent;
    color: var(--hl-primary-text);
    font-weight: 600;
    font-size: 13px;
  }
  .zu {
    border: none;
    background: transparent;
    color: var(--text-3);
    font-size: 13px;
  }
</style>
