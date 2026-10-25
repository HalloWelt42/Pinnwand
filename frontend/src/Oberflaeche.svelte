<script lang="ts">
  // Die Pinnwand nach der Anmeldung: Zustand aus dem Server und Ereignisstrom, Uhr, Weg, Verbindungen des Gerüsts,
  // Mitteilungen dieses Geräts (ein Tippen führt an ihr Ziel). Jeder Pfad zeigt die Ansicht aus
  // der Wegetabelle (routen.ts), am Rechner in der Schale, am Telefon in der eigenen Ansicht. "/" führt zu Heute.
  import { geraet, pushStarten, verbindungenVerfolgen } from "appkern-oberflaeche";
  import { onMount, untrack } from "svelte";
  import { timerVon } from "./daten/abfragen";
  import { melden } from "./daten/anwendung/meldung.svelte";
  import { stand, verbinden } from "./daten/stand.svelte";
  import { sekundentakt, uhrStarten } from "./daten/uhr.svelte";
  import { finden } from "./routen";
  import Schale from "./schale/Schale.svelte";
  import { gehe, weg, wegStarten } from "./weg.svelte";

  onMount(() => {
    void pushStarten();
    const enden = [verbinden(), uhrStarten(), wegStarten(), verbindungenVerfolgen()];
    return () => enden.forEach((ende) => ende());
  });

  // solange dein Timer läuft, zählt die Uhr sekundengenau (M-85)
  $effect(() => sekundentakt(!!timerVon()?.seit));

  // "/" führt zu Heute; das Kürzel eines Boards steht im Pfad klein (/board/HAUS/12 wird /board/haus/12)
  $effect(() => {
    if (weg.pfad === "/") gehe("/heute", true);
    const gross = weg.pfad.match(/^\/board\/([^/]*[A-Z][^/]*)(.*)$/);
    if (gross) gehe(`/board/${gross[1].toLowerCase()}${gross[2]}${weg.suche}`, true);
  });

  const geraetArt = $derived(geraet.mobil ? "telefon" : "rechner");
  // die Wegesuche liest Boards und Karten, hängt aber nur am Pfad, am Gerät und an der Menge der Boards: Änderungen an
  // Karten richten die Ansicht nicht neu ein
  const treffer = $derived.by(() => {
    const p = weg.pfad, g = geraetArt, n = stand.boards.length;
    return stand.geladen && n >= 0 ? untrack(() => finden(p, g)) : null;
  });
  // die Werte der Ansicht bleiben lesbar, auch wenn der Weg gerade wegfällt (eine Antwort kommt noch an)
  const werte = $derived(treffer?.werte ?? {});

  // ein Board im Pfad, das es für dich nicht (mehr) gibt (gelöscht, nicht mehr Mitglied, vertippt): zu Heute
  $effect(() => {
    const b = weg.pfad.match(/^\/board\/([^/]+)/);
    if (stand.geladen && b && !treffer) {
      melden(`Das Board ${b[1].toUpperCase()} gibt es für dich nicht (mehr)`);
      gehe("/heute", true);
    }
  });
</script>

{#if !stand.geladen}
  <div class="anmeldung pw-laedt"><span>Lädt die Boards ...</span></div>
{:else if treffer && geraetArt === "telefon"}
  <div class="pw-telefon-app"><treffer.komponente {...werte} /></div>
{:else if treffer}
  <Schale aktiv={treffer.navi}><treffer.komponente {...werte} /></Schale>
{:else}
  <Schale aktiv=""><div class="rollfeld"><div class="hinweis warnung"><i class="fa-solid fa-triangle-exclamation"></i>
    <div>Diesen Weg gibt es nicht: {weg.pfad}. <a href="/heute">Zu Heute</a></div></div></div></Schale>
{/if}
