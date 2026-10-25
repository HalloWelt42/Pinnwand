<script lang="ts">
  // Karte in den Listen des Telefons (Heute, Board): groß und lesbar, ein Tippen öffnet sie. Links auf Wunsch der Ring
  // zum Erledigen (Halten), rechts der Timer für Karten, auf denen einer laufen darf (ein Start beendet deinen Timer auf
  // einer anderen Karte und bucht ihn). Zeit, Timer und Alterung kommen aus der gemeinsamen Schicht.
  import { kartenNummer, laufendAuf, timerErlaubt, timerVon, zeitDerKarte } from "../../daten/abfragen";
  import { erledigen } from "../../daten/anwendung/karten.svelte";
  import { anhalten, fortsetzen, starten } from "../../daten/anwendung/timer.svelte";
  import { ICH } from "../../daten/ich";
  import { alterTage, datum, dauer, faelligText } from "../../daten/format";
  import { board, konto, stand } from "../../daten/stand.svelte";
  import Person from "../../board/Person.svelte";
  import type { Karte } from "../../modell";
  import { alterung } from "../../regeln/board";
  import { boardPfad } from "../../weg.svelte";
  import HaltKnopf from "./HaltKnopf.svelte";
  import { telPfad } from "./weg";

  let { karte: k, halten = false, ort = false, von = "" }: {
    karte: Karte;
    /** Ring zum Erledigen per Halten */
    halten?: boolean;
    /** Board und Spalte zeigen (Listen über alle Boards) */
    ort?: boolean;
    /** woher der Weg ins Detail kommt (für Zurück) */
    von?: string;
  } = $props();

  const b = $derived(board(k.board));
  const spalte = $derived(b.spalten.find((s) => s.id === k.spalte));
  const erledigt = $derived(spalte?.erledigt ?? false);
  const kannErledigen = $derived(halten && !erledigt && b.spalten.some((s) => s.erledigt));
  const faellig = $derived(k.faellig && !erledigt ? faelligText(k.faellig) : null);
  /** Uhrzeit einer Serienkarte bei der Fälligkeit, solange sie nicht überfällig ist und nicht schon im Titel steht */
  const uhrzeit = $derived.by(() => {
    const u = k.serie ? stand.serien.find((s) => s.id === k.serie)?.uhrzeit : undefined;
    return u && faellig?.klasse !== "gefahr" && !k.titel.startsWith(u) ? u : undefined;
  });
  const alter = $derived(alterTage(k.bewegtAm));
  const punkte = $derived(k.checkliste.filter((p) => p.erledigt).length);
  const mitZeit = $derived(timerErlaubt(k));
  const zeit = $derived(zeitDerKarte(k.id));
  const meiner = $derived(timerVon(ICH)?.karte === k.id ? timerVon(ICH) : undefined);
  const fremd = $derived(laufendAuf(k.id).find((t) => t.konto !== ICH));
  const andere = $derived(ort ? k.zustaendig.filter((p) => p !== ICH) : k.zustaendig);
  const pfad = $derived(telPfad(boardPfad(b.kuerzel, kartenNummer(k)), von ? { von } : {}));
  let fortschritt = $state(0);
  let hinweis = $state(false);
</script>

<div class="pw-tel-karte" class:haelt={fortschritt > 0} class:idee={k.art === "idee"}>
  {#if kannErledigen}
    <HaltKnopf beschriftung="{k.schluessel} erledigen" aktion={() => erledigen(k.id)} bind:fortschritt bind:hinweis />
  {:else if erledigt}
    <span class="pw-tel-erledigt" title="Erledigt"><i class="fa-solid fa-check"></i></span>
  {/if}
  <a class="inhalt" href={pfad}>
    {#if ort}
      <span class="ort" data-farbe={b.farbe}><span class="pw-farbpunkt"></span><span class="pw-schluessel">{k.schluessel}</span>
        <span class="spalte">{spalte?.name}</span></span>
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
          <span class="pw-angabe {alterung(alter, b.einstellungen)}" title="Seit {alter} {alter === 1 ? 'Tag' : 'Tagen'} in dieser Spalte">
            <i class="fa-solid fa-hourglass-half"></i>{alter}</span>
        {/if}
        {#if k.checkliste.length}<span class="pw-angabe" title="Checkliste"><i class="fa-regular fa-square-check"></i>{punkte}/{k.checkliste.length}</span>{/if}
        {#if k.kommentare.length}<span class="pw-angabe" title="Kommentare"><i class="fa-regular fa-comment"></i>{k.kommentare.length}</span>{/if}
        {#if andere.length}<span class="pw-personen">{#each andere.slice(0, 3) as p (p)}<Person id={p} />{/each}</span>{/if}
      </span>
    {/if}
  </a>
  {#if meiner?.seit}
    <button class="pw-tel-timer laeuft" title="Dein Timer läuft: anhalten, die Sitzung wird gebucht" aria-label="Timer anhalten" onclick={anhalten}>
      <i class="fa-solid fa-pause"></i><span class="zahl">{dauer(zeit)}</span></button>
  {:else if meiner}
    <button class="pw-tel-timer angehalten" title="Dein Timer ist angehalten: fortsetzen" aria-label="Timer fortsetzen" onclick={fortsetzen}>
      <i class="fa-solid fa-play"></i><span class="zahl">{dauer(zeit)}</span></button>
  {:else if fremd}
    <span class="pw-tel-timer fremd" title="Timer von {konto(fremd.konto).name} läuft">
      <i class="fa-solid fa-circle-play"></i><span class="zahl">{konto(fremd.konto).kuerzel}</span></span>
  {:else if mitZeit}
    <button class="pw-tel-timer" title="Timer starten; dein Timer auf einer anderen Karte endet dabei und bucht" aria-label="Timer starten"
            onclick={() => starten(k.id)}><i class="fa-solid fa-play"></i>{#if zeit}<span class="zahl">{dauer(zeit)}</span>{/if}</button>
  {/if}
</div>
