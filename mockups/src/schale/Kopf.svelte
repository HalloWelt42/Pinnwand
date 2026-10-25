<script lang="ts">
  // Kopf: Marke, Suche über alle Boards, Stunden von heute und der Woche (Modul Arbeitszeit), der laufende Timer mit
  // Stopp, Hinweise und das Konto aus der Kellerwolke.
  import { HINWEISE, ICH } from "../beispiel/daten";
  import { dauer, laufendSek } from "../beispiel/format";
  import { konto, stand } from "../beispiel/stand.svelte";
  import Person from "../board/Person.svelte";

  const laufend = $derived(stand.karten.find((k) => k.laeuft?.konto === ICH));
  const ungelesen = HINWEISE.filter((h) => !h.gelesen).length;
  const heuteSek = 3 * 3600 + 5 * 60;
</script>

<div class="marke"><span class="pw-marke-symbol"><i class="fa-solid fa-thumbtack"></i></span><span class="marke-name">Pinnwand</span></div>
<label class="suche"><i class="fa-solid fa-magnifying-glass"></i><input placeholder="Karten in allen Boards suchen" /></label>
<div class="kopf-aktionen">
  <div class="pw-stunden" title="Gebucht und Soll aus deinem Zeitkonto">
    <span class="wert"><span>Heute</span><b>{dauer(heuteSek + (laufend ? laufendSek(laufend.laeuft!.seit) : 0))} <small>/ 8:00</small></b></span>
    <span class="wert"><span>Woche</span><b>11:47 <small>/ 40:00</small></b></span>
  </div>
  {#if laufend}
    <div class="pw-laeuft" title="Dein Timer läuft (eine Karte zur Zeit)">
      <i class="fa-solid fa-circle-play pw-akzent"></i>
      <span class="titel"><span class="pw-schluessel">{laufend.schluessel}</span> {laufend.titel}</span>
      <span class="zeit">{dauer(laufend.erfasstSek + laufendSek(laufend.laeuft!.seit), true)}</span>
      <button class="pw-timer laeuft" title="Timer anhalten und buchen"><i class="fa-solid fa-stop"></i></button>
    </div>
  {/if}
  <a class="knopf symbol pw-glocke" href="/hinweise" title="Hinweise"><i class="fa-solid fa-bell"></i>
    {#if ungelesen}<span class="zaehler pille gefahr">{ungelesen}</span>{/if}</a>
  <button class="knopf ohne" title="{konto(ICH).name}, angemeldet mit dem Kellerwolke-Konto"><Person id={ICH} /></button>
</div>
