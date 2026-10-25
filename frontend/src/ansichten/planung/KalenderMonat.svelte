<script lang="ts">
  // Monat im Kalender eines Boards: sechs Wochen ab dem Montag vor dem Monatsersten, links die Kalenderwoche. Je Tag
  // Feiertag, Abwesenheiten, Serientage als kurze Marken (Uhrzeit, Titel im Hinweis), dann die fälligen Karten und
  // Termine; was nicht passt, öffnet die Woche des Tages. Jeder Tag nimmt eine gezogene Karte an (Fälligkeit). Zeigt der
  // Monat heute, rollt er zur Woche von heute.
  import { tick } from "svelte";
  import { uhr } from "../../daten/uhr.svelte";
  import { datum } from "../../daten/format";
  import { konto } from "../../daten/stand.svelte";
  import type { Board } from "../../modell";
  import { istWochenende, kalenderwoche, TAGE_KURZ, TAGE_LANG, WOCHE_AB_MONTAG } from "../../regeln/tage";
  import { STAND } from "./anzeige";
  import KalenderKarte from "./KalenderKarte.svelte";
  import { abwesenheitSymbol, artName, feiertagTitel, type TagInhalt } from "./lesen";

  let { board, tage, inhalt, monat, gezogen = $bindable(null), ablegen, zuTag, gesperrt = false }: {
    board: Board;
    tage: string[];
    inhalt: Map<string, TagInhalt>;
    /** JJJJ-MM des gezeigten Monats */
    monat: string;
    gezogen?: string | null;
    ablegen: (id: string, tag: string) => void;
    zuTag: (tag: string) => void;
    /** Ziehen gesperrt (Suche oder Filter aktiv) */
    gesperrt?: boolean;
  } = $props();

  const MAX = 4;
  let ziel = $state<string | null>(null);
  let feld = $state<HTMLElement>();
  $effect(() => {
    void tage;
    tick().then(() => {
      const h = feld?.querySelector<HTMLElement>(".pw-kalender-tag.heute");
      if (feld && h) feld.scrollTop += h.getBoundingClientRect().top - feld.getBoundingClientRect().top - 40;
    });
  });
  const wochen = $derived(Array.from({ length: tage.length / 7 }, (_, i) => tage.slice(i * 7, i * 7 + 7)));

  function ueber(e: DragEvent, tag: string): void {
    if (!gezogen || gesperrt) return;
    e.preventDefault();
    ziel = tag;
  }
  function fallen(e: DragEvent, tag: string): void {
    e.preventDefault();
    const id = e.dataTransfer?.getData("text/plain") || gezogen;
    ziel = null;
    if (id) ablegen(id, tag);
  }
</script>

<div class="pw-kalender-rollfeld" bind:this={feld}>
  <div class="pw-kalender-monat" role="grid" aria-label="Monat">
    <div class="spaltenkopf kw" title="Kalenderwoche">Woche</div>
    {#each WOCHE_AB_MONTAG as w (w)}<div class="spaltenkopf" class:wochenende={w === 0 || w === 6} title={TAGE_LANG[w]}>{TAGE_KURZ[w]}</div>{/each}
    {#each wochen as woche (woche[0])}
      <div class="kw zahl" title="Kalenderwoche {kalenderwoche(woche[0])}">{kalenderwoche(woche[0])}</div>
      {#each woche as t (t)}
        {@const i = inhalt.get(t)!}
        {@const zeilen = [...i.karten.map((x) => ({ art: "karte" as const, id: x.id, x })), ...i.termine.map((x) => ({ art: "termin" as const, id: x.id, x }))]}
        {@const frei = i.serien.length ? MAX - 1 : MAX}
        {@const sichtbar = zeilen.slice(0, zeilen.length > frei ? frei - 1 : frei)}
        <div class="pw-kalender-tag" class:anderer={!t.startsWith(monat)} class:wochenende={istWochenende(t)} class:feiertag={i.feiertage.length > 0}
             class:heute={t === uhr.heute} class:ziel={ziel === t} role="gridcell" aria-label={datum(t, true)} tabindex="-1"
             ondragover={(e) => ueber(e, t)} ondragleave={() => { if (ziel === t) ziel = null; }} ondrop={(e) => fallen(e, t)}>
          <div class="tagkopf">
            <span class="nummer zahl">{Number(t.slice(8, 10))}</span>
            {#if t === uhr.heute}<span class="heute-wort">heute</span>{/if}
            {#each i.feiertage as f (f.name)}<span class="feiertag-name" title={feiertagTitel(f)}><i class="fa-solid fa-flag"></i>{f.name}</span>{/each}
          </div>
          {#if i.abwesend.length}
            <div class="abwesend">
              {#each i.abwesend as a (a.konto)}
                <span class="pw-kalender-abwesend" data-farbe={konto(a.konto).farbe} title="{konto(a.konto).name}: {artName(a)}{a.notiz ? ` (${a.notiz})` : ''}">
                  <i class="fa-solid {abwesenheitSymbol(a)}"></i>{konto(a.konto).kuerzel}</span>
              {/each}
            </div>
          {/if}
          {#if i.serien.length}
            <div class="serienmarken">
              {#each i.serien as x (x.serie.id)}
                <a class="pw-kalender-serienmarke {x.v.stand}" href="/serien/{x.serie.id}"
                   title="Serie {x.serie.titel}{x.serie.uhrzeit ? ` um ${x.serie.uhrzeit}` : ''}: {STAND[x.v.stand].text}{x.v.ohne.length ? `, ohne ${x.v.ohne.map((o) => konto(o.konto).name).join(', ')}` : ''}">
                  <i class="fa-solid fa-repeat"></i><span>{x.serie.uhrzeit ?? x.serie.titel}</span></a>
              {/each}
            </div>
          {/if}
          {#each sichtbar as e (e.art + e.id)}
            {#if e.art === "karte"}
              <KalenderKarte {board} karte={e.x} {gesperrt} ziehen={(id) => (gezogen = id)} />
            {:else}
              <span class="pw-kalender-eintrag termin" title="Termin {e.x.von} bis {e.x.bis}: {e.x.titel}{e.x.ort ? `, ${e.x.ort}` : ''}">
                <i class="fa-solid fa-handshake zeichen"></i><span class="schluessel">{e.x.von}</span><span class="titel">{e.x.titel}</span></span>
            {/if}
          {/each}
          {#if zeilen.length > sichtbar.length}
            <button class="pw-kalender-mehr" onclick={() => zuTag(t)} title="Woche dieses Tages mit allen Einträgen">+{zeilen.length - sichtbar.length} weitere</button>
          {/if}
        </div>
      {/each}
    {/each}
  </div>
</div>
