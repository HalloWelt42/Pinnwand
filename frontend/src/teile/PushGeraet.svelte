<script lang="ts">
  // Mitteilungen auf diesem Gerät: ob es sie bekommen kann (sichere Adresse, auf dem iPhone vom Home-Bildschirm, nicht
  // verboten), und wenn ja, erlauben oder ausschalten. Erlauben muss im Tippen geschehen (die Frage des Geräts kommt
  // sofort). Die Logik liegt im Appkern (pushEinschalten und Co.), hier steht nur die Bedienung.
  import { push, pushAusschalten, pushEinschalten, pushLage } from "appkern-oberflaeche";
  import { melden } from "../daten/anwendung/meldung.svelte";

  let { nachher }: { nachher?: () => void } = $props();
  const lage = pushLage();
  let unterwegs = $state(false);

  const GRUND: Record<string, string> = {
    unsicher: "Mitteilungen gehen nur über die sichere Adresse der Pinnwand (https).",
    heimbildschirm: "Füge die Pinnwand zuerst zum Home-Bildschirm hinzu und öffne sie von dort; dann lassen sich Mitteilungen erlauben.",
    "nicht-unterstuetzt": "Dieser Browser kann keine Mitteilungen bekommen.",
    verweigert: "Mitteilungen der Pinnwand sind in den Einstellungen dieses Geräts verboten; dort lassen sie sich wieder erlauben.",
  };

  async function erlauben(): Promise<void> {
    unterwegs = true;
    const ergebnis = await pushEinschalten();
    unterwegs = false;
    if (ergebnis === "ok") melden("Dieses Gerät bekommt jetzt Mitteilungen");
    else melden(ergebnis === "verweigert" ? "Das Gerät hat Mitteilungen nicht erlaubt" : "Mitteilungen ließen sich nicht einschalten");
    nachher?.();
  }

  async function ausschalten(): Promise<void> {
    unterwegs = true;
    await pushAusschalten();
    unterwegs = false;
    melden("Dieses Gerät bekommt keine Mitteilungen mehr");
    nachher?.();
  }
</script>

<div class="pw-push-geraet">
  {#if lage !== "geht"}
    <i class="fa-solid fa-circle-info"></i><span>{GRUND[lage]}</span>
  {:else if push.an}
    <i class="fa-solid fa-bell"></i><span>Dieses Gerät bekommt Mitteilungen.</span>
    <button class="knopf klein" disabled={unterwegs} onclick={ausschalten}><i class="fa-solid fa-bell-slash"></i>Ausschalten</button>
  {:else}
    <i class="fa-solid fa-bell"></i><span>Auf diesem Gerät kommen Hinweise noch nicht als Mitteilung an.</span>
    <button class="knopf haupt klein" disabled={unterwegs || push.an === null} onclick={erlauben}><i class="fa-solid fa-bell"></i>Mitteilungen erlauben</button>
  {/if}
</div>
