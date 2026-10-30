<script lang="ts">
  // Eine Karte in Heute: abhaken (in die Erledigt-Spalte ihres Boards), über ihren Pfad öffnen, Timer starten,
  // anhalten oder fortsetzen. Liegengeblieben und Blockiert stehen zusätzlich als Marke an der Karte, auch wenn sie
  // wegen ihrer Fälligkeit in einem anderen Abschnitt steht; die Schwellen sind die Alterung des Boards.
  import { kartenNummer, laufendAuf, timerErlaubt, timerVon, zeitDerKarte } from "../../daten/abfragen";
  import { erledigen } from "../../daten/anwendung/karten.svelte";
  import { anhalten, fortsetzen, starten } from "../../daten/anwendung/timer.svelte";
  import { ICH } from "../../daten/ich";
  import { alterTage, dauer, faelligText } from "../../daten/format";
  import { konto } from "../../daten/stand.svelte";
  import Person from "../../board/Person.svelte";
  import { alterung, liegengeblieben } from "../../regeln/board";
  import { boardPfad } from "../../weg.svelte";
  import BoardMarke from "./BoardMarke.svelte";
  import type { TagEintrag } from "../../daten/abfragen";

  let { eintrag, gesperrt = false, uhrzeit = "" }: {
    eintrag: TagEintrag;
    /** ohne Verbindung: nichts anbieten, was scheinbar gespeichert wäre */
    gesperrt?: boolean;
    /** Uhrzeit einer Serienkarte statt der Fälligkeit */
    uhrzeit?: string;
  } = $props();

  const k = $derived(eintrag.karte);
  const b = $derived(eintrag.board);
  const pfad = $derived(boardPfad(b.kuerzel, kartenNummer(k)));
  const ziel = $derived(b.spalten.find((s) => s.erledigt)?.name ?? "Erledigt");
  const faellig = $derived(k.faellig && !uhrzeit ? faelligText(k.faellig) : null);
  const alter = $derived(alterTage(k.bewegtAm));
  const stufe = $derived(alterung(alter, b.einstellungen));
  const punkte = $derived(k.checkliste.filter((p) => p.erledigt).length);
  const andere = $derived(k.zustaendig.filter((p) => p !== ICH));
  const mein = $derived(timerVon(ICH)?.karte === k.id ? timerVon(ICH) : undefined);
  const fremd = $derived(laufendAuf(k.id).filter((t) => t.konto !== ICH));
  const zeit = $derived(zeitDerKarte(k.id));
</script>

<div class="pw-uebersicht-zeile" class:laeuft={!!mein?.seit}>
  <button class="pw-uebersicht-haken" disabled={gesperrt} title="Erledigt: nach {ziel} in {b.name}" aria-label="{k.schluessel} erledigen"
          onclick={() => erledigen(k.id)}><i class="fa-solid fa-check"></i></button>
  <div class="inhalt">
    <a class="titel" href={pfad}><span class="pw-schluessel">{k.schluessel}</span> {k.titel}</a>
    <div class="angaben">
      <BoardMarke board={b} />
      {#if uhrzeit}<span class="pw-angabe"><i class="fa-regular fa-clock"></i>{uhrzeit}</span>{/if}
      {#if faellig}<span class="pw-angabe {faellig.klasse}" title="Fällig"><i class="fa-regular fa-calendar"></i>{faellig.text}</span>{/if}
      {#if k.blockiert}<span class="pw-angabe gefahr" title={k.blockiert}><i class="fa-solid fa-ban"></i>Blockiert</span>{/if}
      {#if stufe !== "flaeche"}
        <span class="pw-angabe {stufe}" title="Seit {alter} Tagen nicht bewegt{liegengeblieben(alter, b.einstellungen) ? '; liegengeblieben' : ''}">
          <i class="fa-solid fa-hourglass-half"></i>liegt {alter} Tage</span>
      {/if}
      {#if k.checkliste.length}<span class="pw-angabe" title="Checkliste"><i class="fa-regular fa-square-check"></i>{punkte}/{k.checkliste.length}</span>{/if}
      {#if andere.length}
        <span class="pw-personen" title="Auch zuständig: {andere.map((p) => konto(p).name).join(', ')}">{#each andere as p (p)}<Person id={p} />{/each}</span>
      {/if}
    </div>
  </div>
  <div class="rechts">
    {#if mein?.seit}
      <button class="pw-timer laeuft" disabled={gesperrt} title="Dein Timer läuft: anhalten und buchen" onclick={anhalten}>
        <i class="fa-solid fa-pause"></i>{dauer(zeit, true)}</button>
    {:else if mein}
      <button class="pw-timer" disabled={gesperrt} title="Dein Timer ist angehalten: fortsetzen" onclick={fortsetzen}>
        <i class="fa-solid fa-play"></i>{dauer(zeit)}</button>
    {:else if fremd.length}
      <span class="pw-timer fremd" title="Timer von {fremd.map((t) => konto(t.konto).name).join(', ')} läuft"><i class="fa-solid fa-circle-play"></i>{dauer(zeit)}</span>
    {:else if timerErlaubt(k)}
      <button class="pw-timer" disabled={gesperrt} title="Timer starten (dein laufender pausiert und bucht)" onclick={() => starten(k.id)}>
        <i class="fa-solid fa-play"></i>{zeit ? dauer(zeit) : "Start"}</button>
    {:else if k.art === "idee"}
      <span class="pw-angabe pw-uebersicht-idee"><i class="fa-solid fa-lightbulb"></i>Idee</span>
    {/if}
  </div>
</div>
