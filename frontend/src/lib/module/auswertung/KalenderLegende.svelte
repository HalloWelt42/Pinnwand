<script lang="ts">
  import type { AbwesenheitTyp } from '../../api'
  import type { Ebenen } from './kalenderfarben'

  let { typen, ebenen }: { typen: AbwesenheitTyp[]; ebenen: Ebenen } = $props()
</script>

<div class="legende">
  {#if ebenen.anwesenheit}
    {#each typen as t (t.code)}
      <span class="eintrag"><span class="punkt" style="background:{t.farbe}"></span>{t.name}</span>
    {/each}
  {/if}
  {#if ebenen.feiertage}
    <span class="eintrag"><span class="punkt" style="background:var(--due-rot-bg)"></span>Feiertag</span>
  {/if}
  {#if ebenen.stunden}
    <span class="eintrag"><span class="punkt" style="background:color-mix(in srgb, var(--hl-primary) 70%, transparent)"></span>geleistete Stunden</span>
  {/if}
  {#if ebenen.auslastung}
    <span class="eintrag"><span class="punkt" style="background:color-mix(in srgb, var(--ok) 42%, transparent)"></span>im Soll</span>
    <span class="eintrag"><span class="punkt" style="background:color-mix(in srgb, var(--gefahr) 38%, transparent)"></span>über Soll</span>
  {/if}
  <span class="eintrag"><span class="punkt" style="background:var(--surface-2)"></span>frei/Wochenende</span>
</div>

<style>
  .legende { display: flex; flex-wrap: wrap; gap: 12px; padding: 8px 14px; font-size: 11px; color: var(--text-3); border-top: 1px solid var(--border); }
  .eintrag { display: inline-flex; align-items: center; gap: 5px; }
  .punkt { width: 11px; height: 11px; border-radius: 3px; display: inline-block; border: 1px solid var(--border); }
</style>
