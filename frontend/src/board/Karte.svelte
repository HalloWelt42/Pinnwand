<script lang="ts">
  // Karte im Board: alles, was man ohne Öffnen wissen muss. Die Sanduhr zeigt das Alter im Status nach den Schwellen des
  // Boards (Warnung, Gefahr); in Erledigt-Spalten statt des Alters das Abschlussdatum. Der Timer-Knopf ist der eine Timer
  // der Person: starten, anhalten, fortsetzen; fremde Timer nur zur Ansicht; bei geteilter Zeit zeigt er die Zeit der
  // Gruppe, über der Schätzung rot. Beim Überfahren oder mit dem Fokus erscheinen oben rechts die Kette zum Verknüpfen
  // (nur Arbeit) und der Papierkorb, je nach Recht.
  import { PRIORITAETEN } from "../anzeige";
  import { darf, laufendAuf, timerErlaubt, timerVon, zeitDerGruppe, zeitDerKarte } from "../daten/abfragen";
  import { verknuepfen } from "../daten/anwendung/karten.svelte";
  import { inPapierkorb } from "../daten/anwendung/papierkorb.svelte";
  import { anhalten, fortsetzen, starten } from "../daten/anwendung/timer.svelte";
  import { ICH } from "../daten/ich";
  import { alterTage, datum, dauer, faelligText } from "../daten/format";
  import { frisch, gruppenmitglieder, konto, stand } from "../daten/stand.svelte";
  import type { Board, Karte } from "../modell";
  import { alterung } from "../regeln/board";
  import { markdownText } from "../teile/markdown";
  import { kette, ketteBeenden, ketteBewegen, ketteStarten } from "./kette.svelte";
  import Person from "./Person.svelte";
  import Kennungsknopf from "../teile/Kennungsknopf.svelte";

  let { karte, board, erledigt = false, art = "", oeffnen, aktionen = false }: {
    karte: Karte; board: Board; erledigt?: boolean;
    /** Darstellung: offen (im Detail geöffnet) */
    art?: "" | "offen";
    oeffnen?: (id: string) => void;
    /** Kette und Papierkorb beim Überfahren (im Board, nicht in Vorschauen) */
    aktionen?: boolean;
  } = $props();

  const labels = $derived(karte.labels.map((l) => board.labels.find((x) => x.id === l)).filter((l) => l !== undefined));
  const felder = $derived(board.felder.filter((f) => f.aufKarte && karte.felder[f.id]));
  const erledigtePunkte = $derived(karte.checkliste.filter((p) => p.erledigt).length);
  const vollstaendig = $derived(karte.checkliste.length > 0 && erledigtePunkte === karte.checkliste.length);
  const alter = $derived(alterTage(karte.bewegtAm));
  const alterKlasse = $derived(alterung(alter, board.einstellungen));
  const faellig = $derived(karte.faellig && !erledigt ? faelligText(karte.faellig) : null);
  const prioritaet = $derived(karte.prioritaet === "keine" ? "" : PRIORITAETEN.find(([p]) => p === karte.prioritaet)?.[1] ?? "");
  const auszug = $derived(karte.beschreibung ? markdownText(karte.beschreibung).replace(/\n/g, " ") : "");

  // Gruppe verknüpfter Karten: bei geteilter Zeit zeigt der Zeitknopf die Zeit der ganzen Gruppe (jede Sekunde einmal)
  const andere = $derived(gruppenmitglieder(karte));
  const geteilt = $derived(!!karte.gruppe && !!stand.gruppen.find((g) => g.id === karte.gruppe)?.zeitTeilen);
  const zeit = $derived(geteilt ? zeitDerGruppe(karte) : zeitDerKarte(karte.id));
  const schaetzung = $derived((karte.schaetzungMin ?? 0) * 60);
  const ueber = $derived(schaetzung > 0 && zeit > schaetzung);
  const zeitHinweis = $derived((geteilt ? "; Zeit der Gruppe" : "")
    + (schaetzung ? `; ${dauer(zeit)} von ${dauer(schaetzung)} geschätzt${ueber ? ", über der Schätzung" : ""}` : ""));

  /** wer die Karte gerade geändert hat, wenn es jemand anders war (M-06) */
  const geaendertVon = $derived(frisch[karte.id]);
  const mitZeit = $derived(board.module.zeiterfassung && karte.art === "arbeit");
  const meiner = $derived(timerVon(ICH)?.karte === karte.id ? timerVon(ICH) : undefined);
  const fremd = $derived(laufendAuf(karte.id).find((t) => t.konto !== ICH));

  const kettbar = $derived(aktionen && karte.art === "arbeit" && darf(board, "karten.bearbeiten"));
  const loeschbar = $derived(aktionen && darf(board, "karten.loeschen"));

  function timer(e: MouseEvent): void {
    e.stopPropagation();
    if (meiner?.seit) anhalten();
    else if (meiner) fortsetzen();
    else starten(karte.id);
  }

  // Kette: eigene Zeigergeste; der Griff hält den Zeiger fest und lässt das Ziehen der Karte nicht anlaufen
  function ketteGreifen(e: PointerEvent): void {
    if (e.button !== 0) return;
    e.stopPropagation();
    e.preventDefault();
    (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
    ketteStarten(karte.id, e.clientX, e.clientY);
  }
  function ketteZiehen(e: PointerEvent): void {
    if (kette.quelle === karte.id) ketteBewegen(e.clientX, e.clientY);
  }
  function ketteLoslassen(e: PointerEvent): void {
    if (kette.quelle !== karte.id) return;
    ketteBewegen(e.clientX, e.clientY);
    const ziel = ketteBeenden();
    if (ziel) verknuepfen(karte.id, ziel);
  }
</script>

<div class="pw-karte {art}" class:geaendert={!!geaendertVon} class:idee={karte.art === "idee"} class:kettenquelle={kette.quelle === karte.id} class:kettenziel={kette.ziel === karte.id}
     data-karte={karte.id} role="button" tabindex="0" aria-label="{karte.schluessel} {karte.titel}"
     onclick={() => oeffnen?.(karte.id)} onkeydown={(e) => { if (e.key === "Enter" && e.target === e.currentTarget) oeffnen?.(karte.id); }}>
  {#if geaendertVon}<span class="wer-sonst" title="Gerade von {konto(geaendertVon).name} geändert"><Person id={geaendertVon} /></span>{/if}
  {#if kettbar || loeschbar}
    <span class="pw-karte-aktionen">
      {#if kettbar}
        <button class="pw-karte-aktion pw-kettengriff" aria-label="{karte.schluessel} verknüpfen: Kette auf eine andere Karte ziehen"
                title="Auf eine andere Arbeitskarte ziehen: beide werden verknüpft, ziehen zusammen und teilen ihre Zeit; daneben loslassen bricht ab"
                onpointerdown={ketteGreifen} onpointermove={ketteZiehen} onpointerup={ketteLoslassen}
                onmousedown={(e) => e.stopPropagation()} ontouchstart={(e) => e.stopPropagation()} onclick={(e) => e.stopPropagation()}>
          <i class="fa-solid fa-link"></i></button>
      {/if}
      {#if loeschbar}
        <button class="pw-karte-aktion" aria-label="{karte.schluessel} in den Papierkorb"
                title="In den Papierkorb: mit Rückgängig, wiederherstellbar mit Zeiten, Kommentaren und Anhängen"
                onclick={(e) => { e.stopPropagation(); inPapierkorb([karte.id]); }}><i class="fa-solid fa-trash-can"></i></button>
      {/if}
    </span>
  {/if}
  {#if karte.cover}<div class="cover" data-farbe={karte.cover}></div>{/if}
  {#if labels.length}
    <div class="labels">{#each labels as l (l.id)}<span class="pw-label" data-farbe={l.farbe}>{l.name}</span>{/each}</div>
  {/if}
  {#if karte.blockiert}<div class="blockiert"><i class="fa-solid fa-ban"></i><span>{karte.blockiert}</span></div>{/if}
  <div class="titel">{karte.titel}</div>
  {#if auszug}<p class="pw-karte-auszug">{auszug}</p>{/if}
  {#if felder.length}
    <div class="felder">{#each felder as f (f.id)}<span><b>{f.name}</b> {karte.felder[f.id]}</span>{/each}</div>
  {/if}
  {#if karte.checkliste.length}
    <div class="pw-fortschritt" title="{erledigtePunkte} von {karte.checkliste.length} Punkten erledigt">
      <span style="width: {(100 * erledigtePunkte) / karte.checkliste.length}%"></span></div>
  {/if}
  <div class="unten">
    {#if mitZeit}
      {#if meiner?.seit}
        <button class="pw-timer laeuft" class:ueber title="Dein Timer läuft: anhalten (die Sitzung wird gebucht){zeitHinweis}" onclick={timer}><i class="fa-solid fa-pause"></i>{dauer(zeit, true)}</button>
      {:else if meiner}
        <button class="pw-timer" class:ueber title="Dein Timer ist angehalten: fortsetzen{zeitHinweis}" onclick={timer}><i class="fa-solid fa-play"></i>{dauer(zeit)}</button>
      {:else if fremd}
        <span class="pw-timer fremd" class:ueber title="Timer von {konto(fremd.konto).name} läuft{zeitHinweis}"><i class="fa-solid fa-circle-play"></i>{dauer(zeit)}</span>
      {:else if timerErlaubt(karte)}
        <button class="pw-timer" class:ueber title="{geteilt ? 'Timer starten (Zeit geteilt)' : 'Timer starten'}: dein laufender Timer endet dabei und bucht{zeitHinweis}"
                onclick={timer}><i class="fa-solid fa-play"></i>{zeit ? dauer(zeit) : ""}</button>
      {:else if zeit}
        <span class="pw-angabe" class:gefahr={ueber} title="Gebuchte Zeit{zeitHinweis}"><i class="fa-regular fa-clock"></i>{dauer(zeit)}</span>
      {/if}
    {/if}
    {#if karte.art === "idee"}<span class="pw-angabe pw-idee"><i class="fa-solid fa-lightbulb"></i>Idee</span>{/if}
    {#if karte.gruppe}
      <span class="pw-angabe pw-gruppe" class:geteilt
            title="Verknüpft mit {andere.length} {andere.length === 1 ? 'weiteren Karte' : 'weiteren Karten'}: ziehen zusammen{geteilt ? '; die Zeit ist geteilt und zählt einmal' : ''}">
        <i class="fa-solid fa-link"></i>{andere.length + 1}</span>
    {/if}
    <Kennungsknopf schluessel={karte.schluessel} />
    {#if faellig}<span class="pw-angabe {faellig.klasse}" title="Fällig {datum(karte.faellig!, true)}"><i class="fa-regular fa-calendar"></i>{faellig.text}</span>{/if}
    {#if erledigt && karte.abgeschlossen}
      <span class="pw-angabe gut" title="Abgeschlossen"><i class="fa-solid fa-check"></i>{datum(karte.abgeschlossen, true)}</span>
    {:else}
      <span class="pw-angabe {alterKlasse}" title="Seit {alter} {alter === 1 ? 'Tag' : 'Tagen'} in dieser Spalte"><i class="fa-solid fa-hourglass-half"></i>{alter}</span>
    {/if}
    {#if karte.checkliste.length}
      <span class="pw-angabe" class:gut={vollstaendig} title="{erledigtePunkte} von {karte.checkliste.length} Punkten der Checkliste erledigt{vollstaendig ? ': vollständig' : ''}">
        <i class="fa-regular fa-square-check"></i>{erledigtePunkte}/{karte.checkliste.length}</span>
    {/if}
    {#if karte.kommentare.length}<span class="pw-angabe"><i class="fa-regular fa-comment"></i>{karte.kommentare.length}</span>{/if}
    {#if karte.anhaenge.length}<span class="pw-angabe"><i class="fa-solid fa-paperclip"></i>{karte.anhaenge.length}</span>{/if}
    {#if karte.serie}<span class="pw-angabe" title="Aus einer Serie"><i class="fa-solid fa-repeat"></i></span>{/if}
    <span class="rechts">
      {#if prioritaet}<span class="pw-prio" data-prioritaet={karte.prioritaet} role="img" aria-label="Priorität {prioritaet}" title="Priorität: {prioritaet}"></span>{/if}
      {#if karte.zustaendig.length}
        <span class="pw-personen">{#each karte.zustaendig.slice(0, 3) as p (p)}<Person id={p} />{/each}</span>
      {/if}
    </span>
  </div>
</div>
