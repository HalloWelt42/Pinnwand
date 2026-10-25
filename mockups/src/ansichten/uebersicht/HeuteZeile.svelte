<script lang="ts">
  // Eine Karte in Heute: abhaken (in die Erledigt-Spalte ihres Boards), über ihren Pfad öffnen, Timer starten oder
  // anhalten. Liegengeblieben und Blockiert stehen als Marke an der Karte, damit jede Karte in Heute genau einmal steht.
  import { ICH } from "../../beispiel/daten";
  import { alterTage, dauer, faelligText, laufendSek } from "../../beispiel/format";
  import { konto } from "../../beispiel/stand.svelte";
  import Person from "../../board/Person.svelte";
  import { boardPfad } from "../../weg.svelte";
  import { erledigen, timerAnhalten, timerStarten } from "./aktionen.svelte";
  import BoardMarke from "./BoardMarke.svelte";
  import { ALTER_GEFAHR, ALTER_WARNUNG } from "./heute";
  import type { HeuteEintrag } from "./modell";

  let { eintrag, gesperrt = false, fehler = "", uhrzeit = "" }: {
    eintrag: HeuteEintrag;
    /** ohne Verbindung: nichts tun, was scheinbar gespeichert wäre */
    gesperrt?: boolean;
    /** eine Änderung an dieser Karte ist nicht gespeichert (Grund) */
    fehler?: string;
    /** Uhrzeit einer Serienkarte statt der Fälligkeit */
    uhrzeit?: string;
  } = $props();

  const k = $derived(eintrag.karte);
  const b = $derived(eintrag.board);
  const pfad = $derived(boardPfad(b.kuerzel, k.schluessel.split("-")[1]));
  const ziel = $derived(b.spalten.find((s) => s.erledigt)?.name ?? "Erledigt");
  const faellig = $derived(k.faellig && !uhrzeit ? faelligText(k.faellig) : null);
  const alter = $derived(alterTage(k.bewegtAm));
  const punkte = $derived(k.checkliste.filter((p) => p.erledigt).length);
  const andere = $derived(k.zustaendig.filter((p) => p !== ICH));
  const mitZeit = $derived(b.module.zeiterfassung && k.art === "arbeit");
  const zeit = $derived(k.erfasstSek + (k.laeuft ? laufendSek(k.laeuft.seit) : 0));
</script>

<div class="pw-uebersicht-zeile" class:laeuft={k.laeuft?.konto === ICH}>
  <button class="pw-uebersicht-haken" disabled={gesperrt} title="Erledigt: nach {ziel} in {b.name}" aria-label="{k.schluessel} erledigen"
          onclick={() => erledigen(k.id)}><i class="fa-solid fa-check"></i></button>
  <div class="inhalt">
    <a class="titel" href={pfad}><span class="pw-schluessel">{k.schluessel}</span> {k.titel}</a>
    <div class="angaben">
      <BoardMarke board={b} />
      {#if uhrzeit}<span class="pw-angabe"><i class="fa-regular fa-clock"></i>{uhrzeit}</span>{/if}
      {#if faellig}<span class="pw-angabe {faellig.klasse}" title="Fällig"><i class="fa-regular fa-calendar"></i>{faellig.text}</span>{/if}
      {#if k.blockiert}<span class="pw-angabe gefahr" title={k.blockiert}><i class="fa-solid fa-ban"></i>Blockiert</span>{/if}
      {#if alter >= ALTER_WARNUNG}
        <span class="pw-angabe {alter >= ALTER_GEFAHR ? 'gefahr' : 'warnung'}" title="Seit {alter} Tagen nicht bewegt">
          <i class="fa-solid fa-hourglass-half"></i>liegt {alter} Tage</span>
      {/if}
      {#if k.checkliste.length}<span class="pw-angabe" title="Checkliste"><i class="fa-regular fa-square-check"></i>{punkte}/{k.checkliste.length}</span>{/if}
      {#if andere.length}
        <span class="pw-personen" title="Auch zuständig: {andere.map((p) => konto(p).name).join(', ')}">{#each andere as p (p)}<Person id={p} />{/each}</span>
      {/if}
      {#if fehler}<span class="zustand fehler"><i class="fa-solid fa-circle-exclamation"></i>{fehler}</span>{/if}
    </div>
  </div>
  <div class="rechts">
    {#if mitZeit}
      {#if k.laeuft?.konto === ICH}
        <button class="pw-timer laeuft" disabled={gesperrt} title="Dein Timer läuft: anhalten und buchen" onclick={() => timerAnhalten(k.id)}>
          <i class="fa-solid fa-pause"></i>{dauer(zeit, true)}</button>
      {:else if k.laeuft}
        <span class="pw-timer fremd" title="Timer von {konto(k.laeuft.konto).name} läuft"><i class="fa-solid fa-circle-play"></i>{dauer(zeit)}</span>
      {:else}
        <button class="pw-timer" disabled={gesperrt} title="Timer starten (dein laufender hält dabei an und bucht)" onclick={() => timerStarten(k.id)}>
          <i class="fa-solid fa-play"></i>{zeit ? dauer(zeit) : "Start"}</button>
      {/if}
    {:else if k.art === "idee"}
      <span class="pw-angabe pw-uebersicht-idee"><i class="fa-solid fa-lightbulb"></i>Idee</span>
    {/if}
  </div>
</div>
