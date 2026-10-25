<script lang="ts">
  // Persönliche Einstellungen (/einstellungen/<reiter>): Darstellung auf diesem Gerät, Hinweise je Art und Weg, das
  // Konto aus der Kellerwolke und die Gestaltung aus dem Appkern. Einstellungen eines Boards stehen im Board, das
  // Zeitkonto unter Arbeitszeit; hier steht nur, was dir allein gehört.
  import type { Component } from "svelte";
  import Gestaltung from "appkern-oberflaeche/gestaltung";
  import { PERSON_REITER } from "./daten";
  import Darstellung from "./person/Darstellung.svelte";
  import Hinweise from "./person/Hinweise.svelte";
  import Konto from "./person/Konto.svelte";

  let { reiter = "darstellung" }: { reiter?: string; entwurf?: string } = $props();

  const SEITEN: Record<string, Component<any>> = { darstellung: Darstellung, hinweise: Hinweise, konto: Konto };
  const Seite = $derived(SEITEN[reiter]);
</script>

<div class="rahmen-kopf">
  <div class="seitenkopf">
    <h1>Einstellungen</h1>
    <div class="unterzeile">Was nur dich betrifft. Einstellungen eines Boards findest du im Board, dein Zeitkonto unter
      <a href="/arbeitszeit">Arbeitszeit</a>.</div>
  </div>
  <nav class="reiter pw-verwaltung-reiter" aria-label="Persönliche Einstellungen">
    {#each PERSON_REITER as r (r.id)}
      <a href="/einstellungen/{r.id}" class:aktiv={r.id === reiter} aria-current={r.id === reiter ? "page" : undefined}>
        <i class="fa-solid {r.symbol}"></i>{r.name}</a>
    {/each}
  </nav>
</div>
{#if Seite}
  <Seite />
{:else}
  <div class="rollfeld"><Gestaltung familie="leitstand" /></div>
{/if}
