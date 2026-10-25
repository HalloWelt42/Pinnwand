<script lang="ts">
  // Fußleiste: Verbindung zum Ereignisstrom (Änderungen anderer erscheinen sofort; getrennt bleibt der letzte Stand
  // sichtbar und Schreibendes ist gesperrt), Kellerwolke, Fassung.
  import { stand } from "../daten/stand.svelte";
</script>

{#if stand.verbindung === "verbunden"}
  <span title="Änderungen anderer erscheinen sofort"><span class="punkt lebt"></span>Live verbunden</span>
{:else}
  <span title="Letzter Stand sichtbar, Änderungen gesperrt; verbindet sich von selbst neu"><span class="punkt gefahr"></span>Getrennt, verbinde neu</span>
{/if}
<span><span class="punkt"></span>Kellerwolke</span>
<span class="rechts"><span class="schwach">Entwurf</span><span>Pinnwand 1.0</span></span>
