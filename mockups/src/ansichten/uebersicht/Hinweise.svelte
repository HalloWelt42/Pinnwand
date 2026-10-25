<script lang="ts">
  // Hinweise: was dich in deinen Boards betrifft (zugewiesen, fällig, erwähnt, Termin, Kommentar, verschoben), neueste
  // zuerst und nach Tagen. Ungelesene stehen hervorgehoben mit dem Wort "Neu"; ein Klick springt zur Karte und gilt als
  // gelesen. Der Gelesen-Stand gehört dem Konto, nicht dem Browser. Welche Arten zusätzlich per Push aufs Telefon und an
  // den Assistenten gehen, steht in den Einstellungen.
  import { HEUTE } from "../../beispiel/daten";
  import { datum, tageZwischen, wann } from "../../beispiel/format";
  import { board, karte, konto } from "../../beispiel/stand.svelte";
  import Person from "../../board/Person.svelte";
  import type { Farbe, Hinweis, HinweisArt } from "../../modell";
  import { boardPfad } from "../../weg.svelte";
  import { alleGelesen, gelesen, uebersicht } from "./aktionen.svelte";
  import BoardMarke from "./BoardMarke.svelte";

  const ARTEN: Record<HinweisArt, { name: string; symbol: string; farbe: Farbe }> = {
    zugewiesen: { name: "Zugewiesen", symbol: "fa-user-plus", farbe: "himmel" },
    faellig: { name: "Fällig", symbol: "fa-calendar-day", farbe: "koralle" },
    erwaehnt: { name: "Erwähnt", symbol: "fa-at", farbe: "violett" },
    termin: { name: "Termin", symbol: "fa-calendar-check", farbe: "petrol" },
    kommentar: { name: "Kommentar", symbol: "fa-comment", farbe: "stahl" },
    verschoben: { name: "Verschoben", symbol: "fa-arrow-right-arrow-left", farbe: "tuerkis" },
  };
  const ART_LISTE = Object.keys(ARTEN) as HinweisArt[];

  let filter = $state<"alle" | "ungelesen" | HinweisArt>("alle");
  const alle = $derived([...uebersicht.hinweise].sort((a, b) => b.zeit.localeCompare(a.zeit)));
  const ungelesen = $derived(alle.filter((h) => !h.gelesen).length);
  const liste = $derived(alle.filter((h) => filter === "alle" || (filter === "ungelesen" ? !h.gelesen : h.art === filter)));
  const tage = $derived.by(() => {
    const t: { name: string; hinweise: Hinweis[] }[] = [];
    for (const h of liste) {
      const d = tageZwischen(h.zeit, HEUTE);
      const name = d === 0 ? "Heute" : d === 1 ? "Gestern" : datum(h.zeit, true);
      if (t.at(-1)?.name !== name) t.push({ name, hinweise: [] });
      t.at(-1)!.hinweise.push(h);
    }
    return t;
  });

  /** Ziel eines Hinweises: die Karte über ihren Pfad, ein Termin in Serien und Termine */
  function ziel(h: Hinweis): { pfad: string; name: string } {
    const k = h.karte ? karte(h.karte) : undefined;
    if (k) return { pfad: boardPfad(board(k.board).kuerzel, k.schluessel.split("-")[1]), name: k.schluessel };
    return h.art === "termin" ? { pfad: "/serien", name: "Termin" } : { pfad: boardPfad(board(h.board).kuerzel), name: "Board" };
  }
</script>

<div class="pw-uebersicht-seite">
  <div class="rahmen-kopf">
    <div class="seitenkopf">
      <h1>Hinweise</h1>
      <span class="zahl">{ungelesen} ungelesen</span>
      <div class="aktionen">
        <button class="knopf" disabled={!ungelesen} onclick={alleGelesen}><i class="fa-solid fa-check-double"></i>Alle gelesen</button>
        <a class="knopf" href="/einstellungen/hinweise" title="Welche Hinweise per Push aufs Telefon und an den Assistenten gehen">
          <i class="fa-solid fa-sliders"></i>Einstellen</a>
      </div>
      <div class="unterzeile">Was dich in deinen Boards betrifft. Gelesen gilt auf allen deinen Geräten; Push aufs Telefon und den
        Assistenten stellst du je Art in den Einstellungen ein.</div>
    </div>
    <div class="filter pw-uebersicht-filter" role="group" aria-label="Nach Art filtern">
      <button class="chip" class:aktiv={filter === "alle"} onclick={() => (filter = "alle")}>Alle<span class="zaehler">{alle.length}</span></button>
      <button class="chip" class:aktiv={filter === "ungelesen"} onclick={() => (filter = "ungelesen")}>Ungelesen<span class="zaehler">{ungelesen}</span></button>
      <span class="trenner"></span>
      {#each ART_LISTE as a (a)}
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
          <div class="pw-uebersicht-hinweis" class:neu={!h.gelesen}>
            <span class="art" data-farbe={a.farbe}><i class="fa-solid {a.symbol}"></i>{a.name}</span>
            <div class="inhalt">
              <a class="text" href={z.pfad} onclick={() => gelesen(h.id)}>{h.text}</a>
              <div class="angaben">
                {#if !h.gelesen}<span class="zaehler info">Neu</span>{/if}
                {#if h.von}<span class="wer"><Person id={h.von} />{konto(h.von).name}</span>
                {:else}<span class="wer"><span class="pw-person"><i class="fa-solid fa-thumbtack"></i></span>Pinnwand</span>{/if}
                <span class="zeit">{wann(h.zeit)}</span>
                <BoardMarke board={board(h.board)} />
              </div>
            </div>
            <a class="knopf klein" href={z.pfad} onclick={() => gelesen(h.id)}>{z.name}<i class="fa-solid fa-arrow-right"></i></a>
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
