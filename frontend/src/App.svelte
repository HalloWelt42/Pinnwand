<script lang="ts">
  // Wurzel der Oberfläche: Sitzung, Fassung, Weg und Gerät kommen aus dem Appkern; vor der Anmeldung seine Seiten für
  // Einrichtung, Anmeldung und "Pinnwand antwortet nicht", danach die Pinnwand selbst (Oberflaeche.svelte).
  import { AppWeg, Anmeldung, Einrichtung, fassungVerfolgen, geraetStarten, navigationStarten, sitzung, sitzungStarten } from "appkern-oberflaeche";
  import { onMount } from "svelte";
  import { darstellungAnwenden } from "./darstellung.svelte";
  import Oberflaeche from "./Oberflaeche.svelte";

  onMount(() => {
    darstellungAnwenden();
    geraetStarten();
    const fassungEnde = fassungVerfolgen(__APP_FASSUNG__);
    const wegEnde = navigationStarten();
    void sitzungStarten();
    return () => {
      fassungEnde();
      wegEnde();
    };
  });
</script>

{#if !sitzung.geladen}
  <div class="anmeldung pw-laedt"><span>Lädt ...</span></div>
{:else if !sitzung.app}
  <AppWeg ganz nochmal={sitzungStarten} />
{:else if sitzung.app.einrichtung_noetig}
  <Einrichtung />
{:else if !sitzung.angemeldet}
  <Anmeldung />
{:else}
  <Oberflaeche />
{/if}
