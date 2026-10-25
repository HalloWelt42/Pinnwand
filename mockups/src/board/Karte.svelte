<script lang="ts">
  // Karte im Board: alles, was man ohne Öffnen wissen muss. Alter im Status ab 4 Tagen als Warnung, ab 8 als Gefahr
  // (Einstellung des Boards, wie bisher); in Erledigt-Spalten statt des Alters das Abschlussdatum.
  import { ICH } from "../beispiel/daten";
  import { alterTage, datum, dauer, faelligText, laufendSek } from "../beispiel/format";
  import { konto } from "../beispiel/stand.svelte";
  import type { Board, Karte } from "../modell";
  import Person from "./Person.svelte";

  let { karte, board, erledigt = false, art = "", oeffnen }: {
    karte: Karte; board: Board; erledigt?: boolean;
    /** Darstellung im Entwurf: gezogen, mitgezogen, offen (Detail offen), geaendert (gerade von jemand anderem) */
    art?: "" | "gezogen" | "mitgezogen" | "offen" | "geaendert";
    oeffnen?: (id: string) => void;
  } = $props();

  const labels = $derived(karte.labels.map((l) => board.labels.find((x) => x.id === l)).filter((l) => l !== undefined));
  const felder = $derived(board.felder.filter((f) => f.aufKarte && karte.felder[f.id]));
  const erledigtePunkte = $derived(karte.checkliste.filter((p) => p.erledigt).length);
  const alter = $derived(alterTage(karte.bewegtAm));
  const alterKlasse = $derived(alter >= 8 ? "gefahr" : alter >= 4 ? "warnung" : "flaeche");
  const faellig = $derived(karte.faellig && !erledigt ? faelligText(karte.faellig) : null);
  const zeit = $derived(karte.erfasstSek + (karte.laeuft ? laufendSek(karte.laeuft.seit) : 0));
  const mitZeit = $derived(board.module.zeiterfassung && karte.art === "arbeit");
</script>

<div class="pw-karte {art}" class:idee={karte.art === "idee"} role="button" tabindex="0" aria-label="{karte.schluessel} {karte.titel}"
     onclick={() => oeffnen?.(karte.id)} onkeydown={(e) => { if (e.key === "Enter") oeffnen?.(karte.id); }}>
  {#if art === "geaendert"}<span class="wer-sonst" title="Gerade von Anna Berger geändert"><Person id="k-anna" /></span>{/if}
  {#if karte.cover}<div class="cover" data-farbe={karte.cover}></div>{/if}
  {#if labels.length}
    <div class="labels">{#each labels as l (l.id)}<span class="pw-label" data-farbe={l.farbe}>{l.name}</span>{/each}</div>
  {/if}
  {#if karte.blockiert}<div class="blockiert"><i class="fa-solid fa-ban"></i><span>{karte.blockiert}</span></div>{/if}
  <div class="titel">{karte.titel}</div>
  {#if felder.length}
    <div class="felder">{#each felder as f (f.id)}<span><b>{f.name}</b> {karte.felder[f.id]}</span>{/each}</div>
  {/if}
  {#if karte.checkliste.length}
    <div class="pw-fortschritt" title="{erledigtePunkte} von {karte.checkliste.length} Punkten erledigt">
      <span style="width: {(100 * erledigtePunkte) / karte.checkliste.length}%"></span></div>
  {/if}
  <div class="unten">
    {#if mitZeit}
      {#if karte.laeuft?.konto === ICH}
        <button class="pw-timer laeuft" title="Dein Timer läuft: anhalten" onclick={(e) => e.stopPropagation()}><i class="fa-solid fa-pause"></i>{dauer(zeit, true)}</button>
      {:else if karte.laeuft}
        <span class="pw-timer fremd" title="Timer von {konto(karte.laeuft.konto).name} läuft"><i class="fa-solid fa-circle-play"></i>{dauer(zeit)}</span>
      {:else}
        <button class="pw-timer" title="Timer starten (ein laufender Timer hält dabei an und bucht)" onclick={(e) => e.stopPropagation()}><i class="fa-solid fa-play"></i>{zeit ? dauer(zeit) : ""}</button>
      {/if}
    {/if}
    {#if karte.art === "idee"}<span class="pw-angabe" style="color: var(--flieder)"><i class="fa-solid fa-lightbulb" style="color: var(--flieder)"></i>Idee</span>{/if}
    <span class="pw-schluessel">{karte.schluessel}</span>
    {#if faellig}<span class="pw-angabe {faellig.klasse}" title="Fällig {datum(karte.faellig!, true)}"><i class="fa-regular fa-calendar"></i>{faellig.text}</span>{/if}
    {#if erledigt && karte.abgeschlossen}
      <span class="pw-angabe gut" title="Abgeschlossen"><i class="fa-solid fa-check"></i>{datum(karte.abgeschlossen, true)}</span>
    {:else}
      <span class="pw-angabe {alterKlasse}" title="Seit {alter} {alter === 1 ? 'Tag' : 'Tagen'} in dieser Spalte"><i class="fa-solid fa-hourglass-half"></i>{alter}</span>
    {/if}
    {#if karte.checkliste.length}<span class="pw-angabe"><i class="fa-regular fa-square-check"></i>{erledigtePunkte}/{karte.checkliste.length}</span>{/if}
    {#if karte.kommentare.length}<span class="pw-angabe"><i class="fa-regular fa-comment"></i>{karte.kommentare.length}</span>{/if}
    {#if karte.anhaenge.length}<span class="pw-angabe"><i class="fa-solid fa-paperclip"></i>{karte.anhaenge.length}</span>{/if}
    {#if karte.gruppe}<span class="pw-angabe" title="Verknüpft: zieht mit, Zeit geteilt"><i class="fa-solid fa-link" style="color: var(--akzent)"></i></span>{/if}
    {#if karte.serie}<span class="pw-angabe" title="Aus einer Serie"><i class="fa-solid fa-repeat"></i></span>{/if}
    <span class="rechts">
      {#if karte.zustaendig.length}
        <span class="pw-personen">{#each karte.zustaendig.slice(0, 3) as p (p)}<Person id={p} />{/each}</span>
      {/if}
    </span>
  </div>
</div>
