<script lang="ts">
  // Hinweise: was dich in deinen Boards betrifft (zugewiesen, fällig, erwähnt, Termin, Kommentar, verschoben), neueste
  // zuerst und nach Tagen. Ungelesene stehen hervorgehoben mit dem Wort "Neu"; ein Klick springt zur Karte und gilt als gelesen. Der
  // Gelesen-Stand gehört dem Konto, nicht dem Browser. Welche Arten kommen, steht in den Einstellungen.
  import { kartenNummer, ungelesen as ungeleseneZahl } from "../../daten/abfragen";
  import { alleGelesen, artenDa, gelesen } from "../../daten/anwendung/hinweise.svelte";
  import { uhr } from "../../daten/uhr.svelte";
  import { datum, wann } from "../../daten/format";
  import { karte, konto, stand } from "../../daten/stand.svelte";
  import Person from "../../board/Person.svelte";
  import { HINWEIS_ARTEN } from "../../anzeige";
  import type { Hinweis, HinweisArt } from "../../modell";
  import { modulAn } from "../../regeln/board";
  import { tageZwischen } from "../../regeln/tage";
  import { boardPfad } from "../../weg.svelte";
  import BoardMarke from "./BoardMarke.svelte";

  const ARTEN = Object.fromEntries(HINWEIS_ARTEN.map((a) => [a.art, a])) as Record<HinweisArt, (typeof HINWEIS_ARTEN)[number]>;
  const artListe = $derived(artenDa().map((a) => a.art));

  let filter = $state<"alle" | "ungelesen" | HinweisArt>("alle");
  const alle = $derived([...stand.hinweise].sort((a, b) => b.zeit.localeCompare(a.zeit)));
  const ungelesen = $derived(ungeleseneZahl());
  const liste = $derived(alle.filter((h) => filter === "alle" || (filter === "ungelesen" ? !h.gelesen : h.art === filter)));
  const tage = $derived.by(() => {
    const t: { name: string; hinweise: Hinweis[] }[] = [];
    for (const h of liste) {
      const d = tageZwischen(h.zeit.slice(0, 10), uhr.heute);
      const name = d === 0 ? "Heute" : d === 1 ? "Gestern" : datum(h.zeit, true);
      if (t.at(-1)?.name !== name) t.push({ name, hinweise: [] });
      t.at(-1)!.hinweise.push(h);
    }
    return t;
  });

  /** Board eines Hinweises, solange du es siehst */
  const boardVon = (h: Hinweis) => stand.boards.find((b) => b.id === h.board);

  /** Ziel eines Hinweises: die Karte über ihren Pfad, ein Termin in Serien und Termine (solange sein Board das Modul an
   *  hat), sonst das Board; keines, wenn du das Board nicht mehr siehst */
  function ziel(h: Hinweis): { pfad: string; name: string } | undefined {
    const b = boardVon(h);
    if (!b) return undefined;
    const k = h.karte ? karte(h.karte) : undefined;
    if (k) return { pfad: boardPfad(b.kuerzel, kartenNummer(k)), name: k.schluessel };
    if (h.art === "termin" && modulAn(b, "serien", stand.moduleDa)) return { pfad: "/serien", name: "Termin" };
    return { pfad: boardPfad(b.kuerzel), name: "Board" };
  }
</script>

<div class="pw-uebersicht-seite">
  <div class="rahmen-kopf">
    <div class="seitenkopf">
      <h1>Hinweise</h1>
      <span class="zahl">{ungelesen} ungelesen</span>
      <div class="aktionen">
        <button class="knopf" disabled={!ungelesen} onclick={alleGelesen}><i class="fa-solid fa-check-double"></i>Alle gelesen</button>
        <a class="knopf" href="/einstellungen/hinweise" title="Welche Hinweise du bekommst">
          <i class="fa-solid fa-sliders"></i>Einstellen</a>
      </div>
      <div class="unterzeile">Was dich in deinen Boards betrifft. Gelesen gilt auf allen deinen Geräten; welche Arten du bekommst,
        stellst du in den Einstellungen ein.</div>
    </div>
    <div class="filter pw-uebersicht-filter" role="group" aria-label="Nach Art filtern">
      <button class="chip" class:aktiv={filter === "alle"} onclick={() => (filter = "alle")}>Alle<span class="zaehler">{alle.length}</span></button>
      <button class="chip" class:aktiv={filter === "ungelesen"} onclick={() => (filter = "ungelesen")}>Ungelesen<span class="zaehler">{ungelesen}</span></button>
      <span class="trenner"></span>
      {#each artListe as a (a)}
        <button class="chip" class:aktiv={filter === a} onclick={() => (filter = a)}>
          <i class="fa-solid {ARTEN[a].symbol}"></i>{ARTEN[a].name}<span class="zaehler">{alle.filter((h) => h.art === a).length}</span></button>
      {/each}
    </div>
  </div>

  <div class="rollfeld">
    {#each tage as t (t.name)}
      <section class="pw-uebersicht-gruppe" aria-label={t.name}>
        <h2>{t.name}<span class="zaehler">{t.hinweise.length}</span></h2>
        {#each t.hinweise as h (h.id)}
          {@const a = ARTEN[h.art]}
          {@const z = ziel(h)}
          {@const b = boardVon(h)}
          <div class="pw-uebersicht-hinweis" class:neu={!h.gelesen}>
            <span class="art" data-farbe={a.farbe}><i class="fa-solid {a.symbol}"></i>{a.name}</span>
            <div class="inhalt">
              {#if z}<a class="text" href={z.pfad} onclick={() => gelesen(h.id)}>{h.text}</a>
              {:else}<span class="text">{h.text}</span>{/if}
              <div class="angaben">
                {#if !h.gelesen}<span class="zaehler info">Neu</span>{/if}
                {#if h.von}<span class="wer"><Person id={h.von} />{konto(h.von).name}</span>
                {:else}<span class="wer"><span class="pw-person"><i class="fa-solid fa-thumbtack"></i></span>Pinnwand</span>{/if}
                <span class="zeit">{wann(h.zeit)}</span>
                {#if b}<BoardMarke board={b} />{/if}
              </div>
            </div>
            {#if z}<a class="knopf klein" href={z.pfad} onclick={() => gelesen(h.id)}>{z.name}<i class="fa-solid fa-arrow-right"></i></a>{/if}
            <button class="knopf ohne symbol klein" title={h.gelesen ? "Als ungelesen markieren" : "Als gelesen markieren"}
                    onclick={() => gelesen(h.id, !h.gelesen)}><i class="fa-solid {h.gelesen ? 'fa-envelope' : 'fa-envelope-open'}"></i></button>
          </div>
        {/each}
      </section>
    {:else}
      <div class="leer"><i class="fa-regular fa-bell"></i><h2>Keine Hinweise</h2>
        <p>{filter === "alle" ? "Hier erscheint, was dir zugewiesen wird, was fällig ist und wo dich jemand erwähnt." : "Keine Hinweise dieser Auswahl."}</p></div>
    {/each}
  </div>
</div>
