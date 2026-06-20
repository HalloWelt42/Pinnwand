<script lang="ts">
  import { tts, pauseVorlesen, weiterVorlesen, stoppeVorlesen, setzeTempo } from './tts.svelte'

  const TEMPI = [0.75, 1, 1.25, 1.5, 1.75, 2]
  const fortschritt = $derived(tts.anzahl ? ((tts.index + 1) / tts.anzahl) * 100 : 0)
</script>

{#if tts.laeuft}
  <div class="vl" role="status" aria-live="polite">
    <button class="rund" aria-label={tts.pausiert ? 'Weiter' : 'Pause'} onclick={() => (tts.pausiert ? weiterVorlesen() : pauseVorlesen())}>
      <i class="fa-solid {tts.pausiert ? 'fa-play' : 'fa-pause'}" aria-hidden="true"></i>
    </button>
    <button class="rund" aria-label="Vorlesen stoppen" onclick={stoppeVorlesen}>
      <i class="fa-solid fa-stop" aria-hidden="true"></i>
    </button>
    <div class="mitte">
      <div class="satz" class:pause={tts.pausiert}>{tts.satz}</div>
      <div class="bar"><span style="width:{fortschritt}%"></span></div>
    </div>
    <span class="zaehler">Satz {tts.index + 1}/{tts.anzahl}</span>
    <label class="tempo">Tempo
      <select value={tts.tempo} onchange={(e) => setzeTempo(parseFloat(e.currentTarget.value))}>
        {#each TEMPI as t (t)}<option value={t}>{t}x</option>{/each}
      </select>
    </label>
  </div>
{/if}

<style>
  .vl {
    position: fixed;
    left: 50%;
    bottom: 18px;
    transform: translateX(-50%);
    z-index: 50;
    display: flex;
    align-items: center;
    gap: 12px;
    width: min(680px, 92vw);
    padding: 9px 12px;
    background: var(--surface-col);
    border: 1px solid var(--border-2);
    border-radius: var(--r-l, 12px);
    box-shadow: var(--schatten-pop);
  }
  .rund {
    flex: none;
    width: 34px;
    height: 34px;
    border-radius: 50%;
    border: 1px solid var(--hl-primary);
    background: var(--hl-primary);
    color: var(--hl-on-primary);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 13px;
  }
  .rund:hover {
    filter: brightness(1.08);
  }
  .mitte {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 5px;
  }
  .satz {
    font-size: 12.5px;
    color: var(--text-1);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .satz.pause {
    color: var(--text-3);
  }
  .bar {
    height: 4px;
    border-radius: 3px;
    background: var(--border);
    overflow: hidden;
  }
  .bar span {
    display: block;
    height: 100%;
    background: var(--hl-primary);
    transition: width 0.2s;
  }
  .zaehler {
    flex: none;
    font-size: 11px;
    color: var(--text-3);
    font-variant-numeric: tabular-nums;
  }
  .tempo {
    flex: none;
    font-size: 11px;
    color: var(--text-3);
    display: inline-flex;
    align-items: center;
    gap: 5px;
  }
  .tempo select {
    border: 1px solid var(--border);
    background: var(--surface-2);
    color: var(--text-1);
    border-radius: var(--r-s);
    padding: 3px 5px;
    font-size: 11.5px;
  }
</style>
