<script lang="ts">
  // Kopf: Marke, Suche über alle Boards, deine Stunden von heute und der Woche (aus deinen Zeiteinträgen und deinem
  // Zeitkonto), dein Timer mit Anhalten, Fortsetzen und Stopp, Hinweise und das Konto aus der Kellerwolke.
  import { istAm, sitzungSek, sollTag, timerVon, ungelesen, zeitDerKarte } from "../beispiel/abfragen";
  import { anhalten, fortsetzen, stoppen } from "../beispiel/anwendung/timer.svelte";
  import { HEUTE, ICH } from "../beispiel/daten";
  import { dauer } from "../beispiel/format";
  import { karte, konto } from "../beispiel/stand.svelte";
  import Person from "../board/Person.svelte";
  import { plusTage, montagVon } from "../regeln/tage";

  const timer = $derived(timerVon(ICH));
  const timerKarte = $derived(timer ? karte(timer.karte) : undefined);
  const woche = $derived(Array.from({ length: 7 }, (_, i) => plusTage(montagVon(HEUTE), i)));
  const heuteIst = $derived(istAm(ICH, HEUTE));
  const heuteSoll = $derived(sollTag(ICH, HEUTE)?.sollSek ?? 0);
  const wocheIst = $derived(woche.filter((t) => t <= HEUTE).reduce((s, t) => s + istAm(ICH, t), 0));
  const wocheSoll = $derived(woche.reduce((s, t) => s + (sollTag(ICH, t)?.sollSek ?? 0), 0));
  const zahl = $derived(ungelesen());
</script>

<div class="marke"><span class="pw-marke-symbol"><i class="fa-solid fa-thumbtack"></i></span><span class="marke-name">Pinnwand</span></div>
<label class="suche"><i class="fa-solid fa-magnifying-glass"></i><input placeholder="Karten in allen Boards suchen" /></label>
<div class="kopf-aktionen">
  <a class="pw-stunden" href="/zeiten" title="Gebucht und Soll aus deinem Zeitkonto; zum Stundenzettel">
    <span class="wert"><span>Heute</span><b>{dauer(heuteIst)} <small>/ {dauer(heuteSoll)}</small></b></span>
    <span class="wert"><span>Woche</span><b>{dauer(wocheIst)} <small>/ {dauer(wocheSoll)}</small></b></span>
  </a>
  {#if timer && timerKarte}
    <div class="pw-laeuft" class:angehalten={!timer.seit} title={timer.seit ? "Dein Timer läuft (eine Karte zur Zeit)" : "Dein Timer ist angehalten"}>
      <i class="fa-solid {timer.seit ? 'fa-circle-play pw-akzent' : 'fa-circle-pause'}"></i>
      <span class="titel"><span class="pw-schluessel">{timerKarte.schluessel}</span> {timerKarte.titel}</span>
      <span class="zeit">{dauer(zeitDerKarte(timerKarte.id), true)}</span>
      {#if timer.seit}
        <button class="pw-timer laeuft" title="Anhalten: die Sitzung wird gebucht, fortsetzen geht später" onclick={anhalten}><i class="fa-solid fa-pause"></i></button>
      {:else}
        <button class="pw-timer" title="Fortsetzen" onclick={fortsetzen}><i class="fa-solid fa-play"></i></button>
      {/if}
      <button class="pw-timer" title="Stoppen und buchen{timer.seit ? ` (${dauer(sitzungSek(timer))})` : ''}" onclick={stoppen}><i class="fa-solid fa-stop"></i></button>
    </div>
  {/if}
  <a class="knopf symbol pw-glocke" href="/hinweise" title="Hinweise"><i class="fa-solid fa-bell"></i>
    {#if zahl}<span class="zaehler pille gefahr">{zahl}</span>{/if}</a>
  <a class="knopf ohne" href="/einstellungen/konto" title="{konto(ICH).name}, angemeldet mit dem Kellerwolke-Konto"><Person id={ICH} /></a>
</div>
