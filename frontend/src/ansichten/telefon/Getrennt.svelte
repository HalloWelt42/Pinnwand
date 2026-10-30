<script lang="ts">
  // Band am Telefon, solange die Verbindung zum Server fehlt: Ändern ist dann gesperrt, also sagt es die Ansicht vorher
  // und nicht erst nach einem Tippen. Es erscheint erst nach einer kurzen Frist, damit ein schnelles Neuverbinden (nach
  // dem Aufwachen des Telefons) nicht aufblitzt; die Frist zählt ab dem Abriss, nicht je Ansicht. "Neu verbinden"
  // versucht es sofort.
  import { getrenntSeit, neuVerbinden, stand } from "../../daten/stand.svelte";

  const FRIST_MS = 2000;
  let zeigen = $state(false);

  $effect(() => {
    if (stand.verbindung !== "getrennt") {
      zeigen = false;
      return;
    }
    const uhr = setTimeout(() => (zeigen = true), Math.max(0, FRIST_MS - getrenntSeit()));
    return () => clearTimeout(uhr);
  });
</script>

{#if zeigen}
  <div class="hinweis warnung pw-tel-getrennt" role="status">
    <i class="fa-solid fa-plug-circle-xmark"></i>
    <div><b>Keine Verbindung.</b> Ändern geht wieder, sobald sie steht.</div>
    <button class="knopf klein" onclick={neuVerbinden}><i class="fa-solid fa-rotate"></i>Neu verbinden</button>
  </div>
{/if}
