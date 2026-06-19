<script lang="ts">
  import { timer, timerStarten, timerPausieren, timerStoppen, erfassteSekunden, formatDauer, formatPlan } from './timer.svelte'

  const k = $derived(timer.aktiv)
  const laeuft = $derived(!!k?.laeuft_seit)
  const sek = $derived(k ? erfassteSekunden(k, timer.jetzt) : 0)
  const planMin = $derived(k?.schaetzung_min ?? null)
  const prozent = $derived(planMin && planMin > 0 ? (sek / 60 / planMin) * 100 : null)
  const ueber = $derived(prozent != null && prozent > 100)

  const UMFANG = 2 * Math.PI * 15
  const offset = $derived(UMFANG * (1 - Math.min(prozent ?? 0, 100) / 100))
</script>

{#if k}
  <div class="leiste" class:ueber>
    <span class="puls" class:an={laeuft} aria-hidden="true"></span>
    <span class="label">{laeuft ? 'Läuft' : 'Pausiert'}</span>
    {#if k.schluessel}<span class="key">{k.schluessel}</span>{/if}
    <span class="titel">{k.titel}</span>

    <span class="uhr">{formatDauer(sek)}</span>

    {#if prozent != null}
      <span class="ring" title="{Math.round(prozent)}% von {formatPlan(planMin ?? 0)}">
        <svg viewBox="0 0 36 36" width="36" height="36">
          <circle cx="18" cy="18" r="15" fill="none" stroke="var(--border-2)" stroke-width="3" />
          <circle
            cx="18" cy="18" r="15" fill="none"
            stroke={ueber ? 'var(--gefahr)' : 'var(--hl-primary)'}
            stroke-width="3" stroke-linecap="round"
            stroke-dasharray={UMFANG} stroke-dashoffset={offset}
            transform="rotate(-90 18 18)"
          />
        </svg>
        <span class="pz">{Math.round(prozent)}%</span>
      </span>
      <span class="plan">von {formatPlan(planMin ?? 0)}{#if ueber}<span class="ueberschritten">überschritten</span>{/if}</span>
    {/if}

    <div class="aktionen">
      {#if laeuft}
        <button class="btn" onclick={() => timerPausieren(k.id)}><i class="fa-solid fa-pause" aria-hidden="true"></i> Pause</button>
      {:else}
        <button class="btn play" onclick={() => timerStarten(k.id)}><i class="fa-solid fa-play" aria-hidden="true"></i> Fortsetzen</button>
      {/if}
      <button class="btn stopp" onclick={() => timerStoppen(k.id)}><i class="fa-solid fa-stop" aria-hidden="true"></i> Stopp</button>
    </div>
  </div>
{/if}

<style>
  .leiste {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 8px 16px;
    background: var(--surface-3);
    border-bottom: 1px solid var(--hl-primary);
    color: var(--text-1);
  }
  .leiste.ueber {
    border-bottom-color: var(--gefahr);
  }
  .puls {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: var(--text-3);
    flex: none;
  }
  .puls.an {
    background: var(--hl-primary);
    animation: puls 1.4s ease-in-out infinite;
  }
  .leiste.ueber .puls.an {
    background: var(--gefahr);
  }
  @keyframes puls {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.35; transform: scale(0.7); }
  }
  .label {
    font-family: var(--font-display);
    font-size: 11px;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: var(--hl-primary-text);
    font-weight: 600;
  }
  .key {
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--text-3);
  }
  .titel {
    font-weight: 500;
    font-size: 14px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    max-width: 32vw;
  }
  .uhr {
    margin-left: auto;
    font-family: var(--font-mono);
    font-size: 20px;
    font-weight: 500;
    font-variant-numeric: tabular-nums;
    color: var(--text-1);
  }
  .ring {
    position: relative;
    width: 36px;
    height: 36px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }
  .ring .pz {
    position: absolute;
    font-size: 9px;
    font-weight: 600;
    color: var(--text-2);
  }
  .plan {
    font-size: 12px;
    color: var(--text-3);
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .ueberschritten {
    background: var(--due-rot-bg);
    color: var(--due-rot-fg);
    font-weight: 600;
    padding: 2px 8px;
    border-radius: var(--r-s);
  }
  .aktionen {
    display: flex;
    gap: 7px;
  }
  .btn {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    border: 1px solid var(--border-2);
    background: var(--surface-1);
    color: var(--text-1);
    border-radius: var(--r-m);
    padding: 7px 13px;
    font-size: 12.5px;
    font-weight: 500;
  }
  .btn:hover {
    border-color: var(--hl-primary);
    color: var(--hl-primary-text);
  }
  .btn.play {
    background: var(--hl-primary);
    color: var(--hl-on-primary);
    border-color: transparent;
  }
  .btn.stopp:hover {
    border-color: var(--gefahr);
    color: var(--due-rot-fg);
  }
</style>
