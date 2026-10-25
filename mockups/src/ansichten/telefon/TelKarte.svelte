<script lang="ts">
  // Karte in den Listen des Telefons (Heute, Board): groß und lesbar, ein Tippen öffnet sie. Links auf Wunsch der Ring
  // zum Erledigen (Halten), rechts der Timer für Arbeit in Boards mit Zeiterfassung (ein Start hält einen laufenden an
  // und bucht ihn). Alter im Status ab 4 Tagen als Warnung, ab 8 als Gefahr wie im Board.
  import { ICH, SERIEN } from "../../beispiel/daten";
  import { alterTage, datum, dauer, faelligText } from "../../beispiel/format";
  import { board, konto } from "../../beispiel/stand.svelte";
  import Person from "../../board/Person.svelte";
  import type { Karte } from "../../modell";
  import { boardPfad } from "../../weg.svelte";
  import { anhalten, erledigen, kartenzeit, starten } from "./aktionen.svelte";
  import HaltKnopf from "./HaltKnopf.svelte";
  import { telPfad } from "./weg";

  let { karte: k, halten = false, vorfuehren = 0, ort = false, von = "" }: {
    karte: Karte;
    /** Ring zum Erledigen per Halten */
    halten?: boolean;
    /** Entwurf: Ring steht gerade auf diesem Anteil */
    vorfuehren?: number;
    /** Board und Spalte zeigen (Listen über alle Boards) */
    ort?: boolean;
    /** woher der Weg ins Detail kommt (für Zurück) */
    von?: string;
  } = $props();

  const b = $derived(board(k.board));
  const spalte = $derived(b.spalten.find((s) => s.id === k.spalte)!);
  const erledigt = $derived(spalte.erledigt);
  const kannErledigen = $derived(halten && !erledigt && b.spalten.some((s) => s.erledigt));
  const uhrzeit = $derived(k.serie ? SERIEN.find((s) => s.id === k.serie)?.uhrzeit : undefined);
  const faellig = $derived(k.faellig && !erledigt ? faelligText(k.faellig) : null);
  const alter = $derived(alterTage(k.bewegtAm));
  const punkte = $derived(k.checkliste.filter((p) => p.erledigt).length);
  const mitZeit = $derived(b.module.zeiterfassung && k.art === "arbeit" && !erledigt);
  const andere = $derived(ort ? k.zustaendig.filter((p) => p !== ICH) : k.zustaendig);
  const pfad = $derived(telPfad(boardPfad(b.kuerzel, k.schluessel.split("-")[1]), von ? { von } : {}));
  let fortschritt = $state(0);
  let hinweis = $state(false);
</script>

<div class="pw-tel-karte" class:haelt={fortschritt > 0} class:idee={k.art === "idee"}>
  {#if kannErledigen}
    <HaltKnopf beschriftung="{k.schluessel} erledigen" {vorfuehren} aktion={() => erledigen(k.id)} bind:fortschritt bind:hinweis />
  {:else if erledigt}
    <span class="pw-tel-erledigt" title="Erledigt"><i class="fa-solid fa-check"></i></span>
  {/if}
  <a class="inhalt" href={pfad}>
    {#if ort}
      <span class="ort" data-farbe={b.farbe}><span class="pw-farbpunkt"></span><span class="pw-schluessel">{k.schluessel}</span>
        <span class="spalte">{spalte.name}</span></span>
    {/if}
    <span class="titel">{k.titel}</span>
    {#if fortschritt > 0}
      <span class="haltetext"><i class="fa-solid fa-hand-pointer"></i>Weiter halten: erledigt, wenn der Ring voll ist</span>
    {:else if hinweis}
      <span class="haltetext"><i class="fa-solid fa-hand-pointer"></i>Zum Erledigen den Ring gedrückt halten</span>
    {:else}
      <span class="angaben">
        {#if !ort}<span class="pw-schluessel">{k.schluessel}</span>{/if}
        {#if k.art === "idee"}<span class="pw-angabe pw-tel-idee"><i class="fa-solid fa-lightbulb"></i>Idee</span>{/if}
        {#if faellig}
          <span class="pw-angabe {faellig.klasse}" title="Fällig {datum(k.faellig!, true)}"><i class="fa-regular fa-calendar"></i>{faellig.text}{uhrzeit ? ` ${uhrzeit}` : ""}</span>
        {/if}
        {#if k.serie}<span class="pw-angabe" title="Aus einer Serie"><i class="fa-solid fa-repeat"></i>Serie</span>{/if}
        {#if k.blockiert}<span class="pw-angabe gefahr" title={k.blockiert}><i class="fa-solid fa-ban"></i>blockiert</span>{/if}
        {#if erledigt && k.abgeschlossen}
          <span class="pw-angabe gut"><i class="fa-solid fa-check"></i>{datum(k.abgeschlossen, true)}</span>
        {:else if !ort}
          <span class="pw-angabe {alter >= 8 ? 'gefahr' : alter >= 4 ? 'warnung' : 'flaeche'}" title="Seit {alter} {alter === 1 ? 'Tag' : 'Tagen'} in dieser Spalte">
            <i class="fa-solid fa-hourglass-half"></i>{alter}</span>
        {/if}
        {#if k.checkliste.length}<span class="pw-angabe" title="Checkliste"><i class="fa-regular fa-square-check"></i>{punkte}/{k.checkliste.length}</span>{/if}
        {#if k.kommentare.length}<span class="pw-angabe" title="Kommentare"><i class="fa-regular fa-comment"></i>{k.kommentare.length}</span>{/if}
        {#if andere.length}<span class="pw-personen">{#each andere.slice(0, 3) as p (p)}<Person id={p} />{/each}</span>{/if}
      </span>
    {/if}
  </a>
  {#if mitZeit}
    {#if k.laeuft?.konto === ICH}
      <button class="pw-tel-timer laeuft" title="Dein Timer läuft: anhalten und buchen" aria-label="Timer anhalten" onclick={anhalten}>
        <i class="fa-solid fa-pause"></i><span class="zahl">{dauer(kartenzeit(k))}</span></button>
    {:else if k.laeuft}
      <span class="pw-tel-timer fremd" title="Timer von {konto(k.laeuft.konto).name} läuft">
        <i class="fa-solid fa-circle-play"></i><span class="zahl">{konto(k.laeuft.konto).kuerzel}</span></span>
    {:else}
      <button class="pw-tel-timer" title="Timer starten; ein laufender hält dabei an und bucht" aria-label="Timer starten" onclick={() => starten(k.id)}>
        <i class="fa-solid fa-play"></i>{#if k.erfasstSek}<span class="zahl">{dauer(k.erfasstSek)}</span>{/if}</button>
    {/if}
  {/if}
</div>
