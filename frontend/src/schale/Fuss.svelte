<script lang="ts">
  // Fußleiste: Verbindung zum Ereignisstrom (Änderungen anderer erscheinen sofort; getrennt bleibt der letzte Stand
  // sichtbar und Schreibendes ist gesperrt), die Verbindungen des Gerüsts (Kellerwolke, Leitstelle) und die Fassung.
  import { verbindungen } from "appkern-oberflaeche";
  import { stand } from "../daten/stand.svelte";
</script>

{#if stand.verbindung === "verbunden"}
  <span title="Änderungen anderer erscheinen sofort"><span class="punkt lebt"></span>Live verbunden</span>
{:else}
  <span title="Letzter Stand sichtbar, Änderungen gesperrt; verbindet sich von selbst neu"><span class="punkt gefahr"></span>Getrennt, verbinde neu</span>
{/if}
{#each verbindungen.liste as v (v.name)}
  <span title={v.ok ? v.adresse : v.meldung}><span class="punkt" class:gefahr={!v.ok}></span>{v.name}</span>
{/each}
<span class="rechts"><span>Pinnwand {__APP_FASSUNG__}</span></span>
