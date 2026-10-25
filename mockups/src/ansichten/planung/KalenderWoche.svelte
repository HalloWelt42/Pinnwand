<script lang="ts">
  // Woche im Kalender eines Boards: oben ganztägig (fällige Karten, Abwesenheiten, Serien ohne Uhrzeit), darunter das
  // Stundenraster mit Terminen und Serientagen zur Uhrzeit; überlappende stehen nebeneinander. Die Linie zeigt jetzt.
  // Jede Spalte nimmt eine gezogene Karte an (Fälligkeit an diesem Tag).
  import { HEUTE, JETZT } from "../../beispiel/daten";
  import { datum } from "../../beispiel/format";
  import { konto } from "../../beispiel/stand.svelte";
  import type { Board, Serie, Termin } from "../../modell";
  import { STAND } from "./anzeige";
  import type { TagInhalt } from "./kalender";
  import KalenderKarte from "./KalenderKarte.svelte";
  import { ABWESENHEIT_NAME, ABWESENHEIT_SYMBOL, feiertagTitel } from "./plan.svelte";
  import { istWochenende, minutenAus, TAGE_LANG, uhrzeitAus, wochentag } from "./tage";
  import type { Vorkommen } from "./typen";

  let { board, tage, inhalt, gezogen = $bindable(null), ablegen }: {
    board: Board;
    tage: string[];
    inhalt: Map<string, TagInhalt>;
    gezogen?: string | null;
    ablegen: (id: string, tag: string) => void;
  } = $props();

  const STUNDE = 52;
  type Block = { id: string; von: number; bis: number; spur: number; spuren: number } &
    ({ art: "termin"; t: Termin } | { art: "serie"; s: Serie; v: Vorkommen });

  /** Blöcke eines Tages mit Spuren: was sich überschneidet, steht nebeneinander */
  function bloecke(i: TagInhalt): Block[] {
    const roh: Block[] = [
      ...i.termine.map((t) => ({ id: t.id, art: "termin" as const, t, von: minutenAus(t.von), bis: minutenAus(t.bis), spur: 0, spuren: 1 })),
      ...i.serien.filter((x) => x.serie.uhrzeit).map((x) => {
        const von = minutenAus(x.serie.uhrzeit!);
        return { id: x.serie.id, art: "serie" as const, s: x.serie, v: x.v, von, bis: von + x.serie.dauerMin, spur: 0, spuren: 1 };
      }),
    ].sort((a, b) => a.von - b.von);
    const enden: number[] = [];
    for (const b of roh) {
      const sichtbarBis = Math.max(b.bis, b.von + 30);
      let spur = enden.findIndex((e) => e <= b.von);
      if (spur < 0) spur = enden.length;
      enden[spur] = sichtbarBis;
      b.spur = spur;
    }
    for (const b of roh) b.spuren = Math.max(1, ...roh.filter((x) => x.von < Math.max(b.bis, b.von + 30) && b.von < Math.max(x.bis, x.von + 30)).map((x) => x.spur + 1));
    return roh;
  }

  const tagBloecke = $derived(new Map(tage.map((t) => [t, bloecke(inhalt.get(t)!)])));
  const alle = $derived([...tagBloecke.values()].flat());
  const ab = $derived(Math.min(7, ...alle.map((b) => Math.floor(b.von / 60))));
  const bis = $derived(Math.max(17, ...alle.map((b) => Math.ceil(b.bis / 60))));
  const stunden = $derived(Array.from({ length: bis - ab }, (_, i) => ab + i));
  const jetztMin = minutenAus(JETZT.slice(11, 16));

  let ziel = $state<string | null>(null);
  function ueber(e: DragEvent, tag: string): void {
    if (!gezogen) return;
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

<div class="pw-kalender-rollfeld">
  <div class="pw-kalender-woche" style="--stunde: {STUNDE}px">
    <div class="spaltenkopf ecke"></div>
    {#each tage as t (t)}
      {@const i = inhalt.get(t)!}
      <div class="spaltenkopf tagname" class:wochenende={istWochenende(t)} class:heute={t === HEUTE} title={TAGE_LANG[wochentag(t)]}>
        <b class="zahl">{datum(t, true)}</b>
        {#if t === HEUTE}<span class="heute-wort">heute</span>{/if}
        {#each i.feiertage as f (f.feiertag.name)}<span class="feiertag-name" title={feiertagTitel(f.feiertag, f.konten)}><i class="fa-solid fa-flag"></i>{f.feiertag.name}</span>{/each}
      </div>
    {/each}

    <div class="ganztags-name">ganztägig</div>
    {#each tage as t (t)}
      {@const i = inhalt.get(t)!}
      <div class="ganztags" class:wochenende={istWochenende(t)} class:feiertag={i.feiertage.length > 0} class:ziel={ziel === t}
           role="gridcell" aria-label="{datum(t, true)} ganztägig" tabindex="-1"
           ondragover={(e) => ueber(e, t)} ondragleave={() => { if (ziel === t) ziel = null; }} ondrop={(e) => fallen(e, t)}>
        {#each i.abwesend as a (a.konto)}
          <span class="pw-kalender-abwesend lang" data-farbe={konto(a.konto).farbe} title="{konto(a.konto).name}: {ABWESENHEIT_NAME[a.art]}{a.notiz ? ` (${a.notiz})` : ''}">
            <i class="fa-solid {ABWESENHEIT_SYMBOL[a.art]}"></i>{konto(a.konto).kuerzel} {ABWESENHEIT_NAME[a.art]}</span>
        {/each}
        {#each i.serien.filter((x) => !x.serie.uhrzeit) as x (x.serie.id)}
          <a class="pw-kalender-eintrag serie {x.v.stand}" href="/serien/{x.serie.id}" title="Serie {x.serie.titel}: {STAND[x.v.stand].text}">
            <i class="fa-solid fa-repeat zeichen"></i><span class="titel">{x.serie.titel}</span></a>
        {/each}
        {#each i.karten as k (k.id)}<KalenderKarte {board} karte={k} ziehen={(id) => (gezogen = id)} />{/each}
      </div>
    {/each}

    <div class="stunden">{#each stunden as h (h)}<span class="zahl">{String(h).padStart(2, "0")}:00</span>{/each}</div>
    {#each tage as t (t)}
      <div class="raster" class:wochenende={istWochenende(t)} class:feiertag={(inhalt.get(t)?.feiertage.length ?? 0) > 0} class:ziel={ziel === t} style="height: {(bis - ab) * STUNDE}px"
           role="gridcell" aria-label="{datum(t, true)} nach Uhrzeit" tabindex="-1"
           ondragover={(e) => ueber(e, t)} ondragleave={() => { if (ziel === t) ziel = null; }} ondrop={(e) => fallen(e, t)}>
        {#each tagBloecke.get(t) ?? [] as b (b.art + b.id)}
          {@const lage = `top: ${((b.von - ab * 60) / 60) * STUNDE}px; height: ${Math.max(26, ((b.bis - b.von) / 60) * STUNDE - 2)}px; left: calc(${(b.spur / b.spuren) * 100}% + 2px); width: calc(${100 / b.spuren}% - 4px)`}
          {#if b.art === "termin"}
            <div class="pw-kalender-block termin" class:kurz={b.bis - b.von < 50} style={lage}
                 title="Termin {b.t.von} bis {b.t.bis}: {b.t.titel}{b.t.ort ? `, ${b.t.ort}` : ''}; {b.t.teilnehmer.map((k) => konto(k).name).join(', ')}">
              <span class="zahl">{b.t.von} bis {b.t.bis}</span><span class="titel">{b.t.titel}</span>
              {#if b.t.ort}<span class="ort"><i class="fa-solid fa-location-dot"></i>{b.t.ort}</span>{/if}
            </div>
          {:else}
            <a class="pw-kalender-block serie {b.v.stand}" class:kurz={b.bis - b.von < 50} style={lage} href="/serien/{b.s.id}"
               title="Serie {b.s.titel} {b.s.uhrzeit} bis {uhrzeitAus(b.bis)}: {STAND[b.v.stand].text}{b.v.ohne.length ? `, ohne ${b.v.ohne.map((o) => konto(o.konto).name).join(', ')}` : ''}">
              <span class="zahl"><i class="fa-solid fa-repeat"></i>{b.s.uhrzeit}</span><span class="titel">{b.s.titel}</span></a>
          {/if}
        {/each}
        {#if t === HEUTE && jetztMin >= ab * 60 && jetztMin <= bis * 60}
          <div class="jetzt" style="top: {((jetztMin - ab * 60) / 60) * STUNDE}px" title="Jetzt, {JETZT.slice(11, 16)}"></div>
        {/if}
      </div>
    {/each}
  </div>
</div>
