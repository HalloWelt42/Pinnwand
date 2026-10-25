<script lang="ts">
  // Kopf: Marke, Suche über alle Boards (Sprung zur Karte über ihren Pfad), deine Stunden von heute und der Woche (aus
  // deinen Zeiteinträgen und deinem Zeitkonto), dein Timer mit Anhalten, Fortsetzen und Stopp, Hinweise und das Konto.
  import { istAm, kartenNummer, passt, sitzungSek, sollTag, timerVon, ungelesen, zeitDerKarte } from "../daten/abfragen";
  import { anhalten, fortsetzen, stoppen } from "../daten/anwendung/timer.svelte";
  import { uhr } from "../daten/uhr.svelte";
  import { ICH } from "../daten/ich";
  import { dauer } from "../daten/format";
  import { karte, konto, stand } from "../daten/stand.svelte";
  import Person from "../board/Person.svelte";
  import { plusTage, montagVon } from "../regeln/tage";
  import { boardPfad, gehe } from "../weg.svelte";

  const timer = $derived(timerVon(ICH));
  const timerKarte = $derived(timer ? karte(timer.karte) : undefined);
  const woche = $derived(Array.from({ length: 7 }, (_, i) => plusTage(montagVon(uhr.heute), i)));
  const heuteIst = $derived(istAm(ICH, uhr.heute));
  const heuteSoll = $derived(sollTag(ICH, uhr.heute)?.sollSek ?? 0);
  const wocheIst = $derived(woche.filter((t) => t <= uhr.heute).reduce((s, t) => s + istAm(ICH, t), 0));
  const wocheSoll = $derived(woche.reduce((s, t) => s + (sollTag(ICH, t)?.sollSek ?? 0), 0));
  const zahl = $derived(ungelesen());

  /** Suche über alle Boards, in denen du Mitglied bist: höchstens acht Treffer, Enter öffnet den ersten */
  let suche = $state("");
  const treffer = $derived.by(() => {
    if (suche.trim().length < 2) return [];
    const boards = stand.boards.filter((b) => b.mitglieder.some((m) => m.konto === ICH));
    return stand.karten.flatMap((k) => {
      const b = boards.find((x) => x.id === k.board);
      return b && passt(k, b, suche) ? [{ k, b }] : [];
    }).slice(0, 8);
  });
  function oeffnen(i = 0): void {
    const t = treffer[i];
    if (!t) return;
    suche = "";
    gehe(boardPfad(t.b.kuerzel, kartenNummer(t.k)));
  }
</script>

<div class="marke"><span class="pw-marke-symbol"><i class="fa-solid fa-thumbtack"></i></span><span class="marke-name">Pinnwand</span></div>
<div class="pw-kopfsuche">
  <label class="suche"><i class="fa-solid fa-magnifying-glass"></i><input placeholder="Karten in allen Boards suchen" bind:value={suche}
    aria-label="Karten in allen Boards suchen" autocomplete="off"
    onkeydown={(e) => { if (e.key === "Enter") oeffnen(); if (e.key === "Escape") suche = ""; }} /></label>
  {#if suche.trim().length >= 2}
    <div class="pw-kopfsuche-treffer" role="listbox" aria-label="Treffer">
      {#each treffer as t, i (t.k.id)}
        <button type="button" role="option" aria-selected={i === 0} onclick={() => oeffnen(i)}>
          <span class="pw-farbpunkt" data-farbe={t.b.farbe}></span><span class="pw-schluessel">{t.k.schluessel}</span>
          <span class="titel">{t.k.titel}</span><span class="board">{t.b.name}</span></button>
      {:else}
        <div class="leer-zeile">Keine Karte passt zu "{suche.trim()}".</div>
      {/each}
    </div>
  {/if}
</div>
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
