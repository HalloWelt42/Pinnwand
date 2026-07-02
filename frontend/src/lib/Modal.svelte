<script lang="ts">
  // Gemeinsame Huelle fuer zentrierte Overlay-Dialoge: Abdunkelung (Klick
  // schliesst), Escape schliesst, Fokus wandert beim Oeffnen ins Fenster.
  // Sichtbarkeit steuert der Aufrufer per {#if}; Inhalts-Markup und -Styles
  // bleiben beim Aufrufer (children-Snippet).
  import type { Snippet } from 'svelte'

  let {
    ariaLabel,
    onSchliessen,
    breite = 'min(440px, 100%)',
    maxHoehe,
    optik = 'lift',
    z = 60,
    abdunkelung = 'rgba(0, 0, 0, 0.45)',
    polster = '24px',
    children,
  }: {
    // Zugaenglicher Name des Dialogs.
    ariaLabel: string
    // Wird bei Backdrop-Klick und Escape gerufen; der Aufrufer blendet aus.
    onSchliessen: () => void
    // Fensterbreite als CSS-Wert, z. B. 'min(680px, 100%)'.
    breite?: string
    // Optionale Hoehenbegrenzung des Fensters als CSS-Wert.
    maxHoehe?: string
    // Fenster-Flaeche: 'lift' (surface-1, schatten-lift) oder 'pop' (surface-col, schatten-pop).
    optik?: 'lift' | 'pop'
    // Stapelordnung der Huelle.
    z?: number
    // Farbe der Abdunkelung hinter dem Fenster.
    abdunkelung?: string
    // Innenabstand der Huelle (Mindestabstand des Fensters zum Rand).
    polster?: string
    children: Snippet
  } = $props()

  let fenster = $state<HTMLDivElement | null>(null)

  // Fokus beim Oeffnen ins Fenster, damit Escape und Tab dort starten.
  $effect(() => {
    fenster?.focus()
  })
</script>

<svelte:window onkeydown={(e) => { if (e.key === 'Escape') onSchliessen() }} />
<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
<div
  class="huelle"
  role="presentation"
  style:z-index={z}
  style:background={abdunkelung}
  style:padding={polster}
  onclick={onSchliessen}
>
  <!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions a11y_no_noninteractive_element_interactions -->
  <div
    class="fenster"
    class:pop={optik === 'pop'}
    role="dialog"
    aria-label={ariaLabel}
    tabindex="-1"
    bind:this={fenster}
    style:width={breite}
    style:max-height={maxHoehe}
    onclick={(e) => e.stopPropagation()}
  >
    {@render children()}
  </div>
</div>

<style>
  .huelle {
    position: fixed;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .fenster {
    display: flex;
    flex-direction: column;
    overflow: hidden;
    background: var(--surface-1, #1b1b1f);
    border: 1px solid var(--border);
    border-radius: var(--r-xl, 14px);
    box-shadow: var(--schatten-lift, 0 12px 40px rgba(0, 0, 0, 0.4));
    outline: none;
  }
  .fenster.pop {
    background: var(--surface-col);
    border-color: var(--border-2);
    box-shadow: var(--schatten-pop);
  }
</style>
