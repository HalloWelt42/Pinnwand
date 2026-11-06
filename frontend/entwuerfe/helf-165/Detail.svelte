<script lang="ts">
  // Kartendetail im Entwurf: Kopf und Angaben wie in der App (detail/Karteninhalt.svelte), Status und Priorität heute
  // als Klappliste oder neu als Knopfleiste. Jede Leiste hält ihren Stand für sich, damit sich alles anklicken lässt.
  import type { Prioritaet } from "../../src/modell";
  import { prioritaetsStufen, spaltenStufen, type EntwurfSpalte } from "./daten";
  import { Stufenwahl } from "appkern-oberflaeche";

  let { spalten, art, anzeige = "symbol", gesperrt = false, start = 1, prio = "hoch" }: {
    spalten: EntwurfSpalte[];
    art: "heute" | "neu";
    anzeige?: "symbol" | "gewaehlt";
    gesperrt?: boolean;
    start?: number;
    prio?: Prioritaet;
  } = $props();

  // svelte-ignore state_referenced_locally
  let spalte = $state(spalten[start].id);
  // svelte-ignore state_referenced_locally
  let prioritaet = $state<Prioritaet>(prio);
  const jetzt = $derived(spalten.find((s) => s.id === spalte)!);
</script>

<div class="ent-leiste">
  <div class="pw-detail-kopf">
    <button type="button" class="pw-schluessel pw-kennung pw-detail-schluessel" title="HELF-165 kopieren">HELF-165</button>
    <span class="zustand" data-farbe={jetzt.farbe}><span class="pw-farbpunkt"></span>{jetzt.name}</span>
    <span class="pw-umschalter" title="Arbeit hat Zeiterfassung, eine Idee nicht">
      <button class="an"><i class="fa-solid fa-briefcase"></i>Arbeit</button>
      <button class="idee"><i class="fa-solid fa-lightbulb"></i>Idee</button>
    </span>
    <span class="rechts">
      <button class="knopf ohne symbol klein" title="Karte vorlesen"><i class="fa-solid fa-volume-high"></i></button>
      <button class="knopf ohne symbol klein" title="Verweis kopieren"><i class="fa-solid fa-link"></i></button>
      <button class="knopf ohne symbol klein" title="Schließen (Escape)"><i class="fa-solid fa-xmark"></i></button>
    </span>
  </div>
  <div class="pw-detail-inhalt">
    <input class="pw-detail-titel" value="Pinnwand: Status und Priorität als Knopfleiste" aria-label="Titel" />
    <section class="pw-abschnitt">
      <div class="etikett">Angaben</div>
      <div class="pw-felder">
        <span class="name"><i class="fa-solid fa-table-columns"></i>Status</span>
        <span class="wert">
          {#if art === "heute"}
            <select class="eingabe" bind:value={spalte} disabled={gesperrt} aria-label="Status">
              {#each spalten as s (s.id)}<option value={s.id}>{s.name}</option>{/each}</select>
          {:else}
            <Stufenwahl wert={spalte} optionen={spaltenStufen(spalten)} beschriftung="Status" {anzeige} {gesperrt} onwahl={(w) => (spalte = w)} />
          {/if}
        </span>
        <span class="name"><i class="fa-solid fa-flag"></i>Priorität</span>
        <span class="wert">
          {#if art === "heute"}
            <select class="eingabe" bind:value={prioritaet} disabled={gesperrt} aria-label="Priorität">
              {#each prioritaetsStufen() as p (p.wert)}<option value={p.wert}>{p.titel}</option>{/each}</select>
          {:else}
            <Stufenwahl wert={prioritaet} optionen={prioritaetsStufen()} beschriftung="Priorität" {anzeige} {gesperrt} onwahl={(w) => (prioritaet = w)} />
          {/if}
        </span>
        <span class="name"><i class="fa-solid fa-play"></i>Start</span>
        <span class="wert"><input class="eingabe" value="06.11.2026" aria-label="Start" disabled={gesperrt} /></span>
        <span class="name"><i class="fa-regular fa-calendar"></i>Fällig</span>
        <span class="wert"><input class="eingabe" value="" placeholder="" aria-label="Fällig" disabled={gesperrt} /></span>
        <span class="name"><i class="fa-solid fa-user"></i>Zuständig</span>
        <span class="wert pw-detail-personen"><span class="chip">Helfer</span></span>
        <span class="name"><i class="fa-solid fa-tag"></i>Labels</span>
        <span class="wert pw-labelwahl">
          <button class="pw-label" data-farbe="himmel" aria-pressed="true" disabled={gesperrt}>Oberfläche</button>
          <button class="pw-label aus" data-farbe="koralle" aria-pressed="false" disabled={gesperrt}>Fehler</button>
          <button class="pw-label aus" data-farbe="minze" aria-pressed="false" disabled={gesperrt}>Komfort</button>
        </span>
      </div>
    </section>
  </div>
</div>
