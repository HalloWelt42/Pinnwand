<script lang="ts">
  // Archiv eines Boards: erledigte Karten, deren Abschluss älter als die Archivgrenze des Boards ist. Das Board lädt sie
  // nie (reine Ladegrenze, eine größere Grenze holt sie zurück); hier kommen sie seitenweise vom Server, neueste zuerst,
  // nach dem Ladeschritt des Boards (Rollen ans Ende oder "Mehr laden" holt die nächste Seite; der Kopf nennt die Zahl
  // des Servers), durchsuchbar über die Werte der geladenen Karten. Ein Klick öffnet die Karte über ihren Pfad;
  // zurückholen geht dort über den Status.
  import { untrack } from "svelte";
  import { kartenNummer, passt, woerter, zeitDerKarte } from "../../daten/abfragen";
  import { Archivseiten } from "../../daten/archiv.svelte";
  import { uhr } from "../../daten/uhr.svelte";
  import { datumJahr, dauer } from "../../daten/format";
  import { board as holeBoard, konto } from "../../daten/stand.svelte";
  import Person from "../../board/Person.svelte";
  import type { Karte } from "../../modell";
  import { plusTage } from "../../regeln/tage";
  import { boardPfad, gehe } from "../../weg.svelte";
  import NebenKopf from "./NebenKopf.svelte";

  let { boardId }: { boardId: string } = $props();
  const b = $derived(holeBoard(boardId));
  const kennung = $derived(b.id);
  const tage = $derived(b.einstellungen.archivTage);
  const schritt = $derived(b.einstellungen.ladeschritt);
  const mitZeit = $derived(b.module.zeiterfassung);
  /** Abschluss vor diesem Tag: im Archiv */
  const grenze = $derived(plusTage(uhr.heute, -tage));

  // je Board und Ladeschritt eine eigene Folge von Seiten; eine andere Archivgrenze ändert, was im Archiv liegt, und
  // fängt ebenfalls vorn an
  const seiten = $derived.by(() => {
    void tage;
    return new Archivseiten(kennung, schritt);
  });
  $effect(() => {
    const s = seiten;
    untrack(() => void s.weiter());
  });

  let suche = $state("");
  const w = $derived(woerter(suche));
  const treffer = $derived(seiten.karten.filter((k) => passt(k, b, w)));
  const anzahl = (n: number) => `${n} ${n === 1 ? "Karte" : "Karten"}`;

  function pfad(k: Karte): string {
    return boardPfad(b.kuerzel, kartenNummer(k));
  }
  function rollen(e: Event): void {
    const feld = e.currentTarget as HTMLElement;
    if (seiten.weitere > 0 && feld.scrollTop + feld.clientHeight >= feld.scrollHeight - 80) void seiten.weiter();
  }
</script>

<div class="pw-uebersicht-seite">
  <div class="rahmen-kopf">
    <NebenKopf board={b} titel="Archiv" symbol="fa-box-archive"
               angabe="{seiten.geladen ? `${anzahl(seiten.gesamt)}, ` : ''}abgeschlossen vor dem {datumJahr(grenze)}"
               erklaerung="Erledigte Karten, deren Abschluss älter als {tage} Tage ist. Das Board lädt sie nicht mehr; eine größere Grenze holt sie zurück. Zurückholen geht in der Karte über den Status." />
    <div class="pw-uebersicht-suchzeile">
      <label class="suche"><i class="fa-solid fa-magnifying-glass"></i>
        <input placeholder="Im Archiv suchen: Titel, Schlüssel, Labels, Felder, Kommentare" aria-label="Archiv durchsuchen" bind:value={suche} /></label>
      <a class="chip" href={boardPfad(b.kuerzel, "einstellungen")} title="Archivgrenze in den Einstellungen des Boards">
        <i class="fa-solid fa-sliders"></i>Grenze {tage} Tage</a>
    </div>
  </div>

  <div class="rollfeld" onscroll={rollen}>
    {#if !seiten.geladen}
      <div class="leer"><i class="fa-solid {seiten.fehler ? 'fa-triangle-exclamation' : 'fa-box-archive'}"></i>
        {#if seiten.fehler}<h2>Das Archiv ließ sich nicht laden</h2><p>{seiten.fehler}</p>
          <button class="knopf klein" onclick={() => void seiten.weiter()}><i class="fa-solid fa-rotate-right"></i>Noch einmal</button>
        {:else}<p>Das Archiv lädt</p>{/if}</div>
    {:else if !seiten.gesamt}
      <div class="leer"><i class="fa-solid fa-box-archive"></i><h2>Noch nichts im Archiv</h2>
        <p>Erledigte Karten kommen hierher, wenn ihr Abschluss älter als {tage} Tage ist.</p></div>
    {:else}
      <div class="tabellen-raum pw-uebersicht-archiv">
        <table class="tabelle karten">
          <thead>
            <tr><th>Karte</th><th>Abgeschlossen</th><th>Zuständig</th><th>Labels</th>{#if mitZeit}<th class="zahl">Zeit</th>{/if}</tr>
          </thead>
          <tbody>
            {#each treffer as k (k.id)}
              <!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_noninteractive_element_interactions -->
              <tr onclick={() => gehe(pfad(k))}>
                <td class="karte-zelle"><a href={pfad(k)} onclick={(e) => e.stopPropagation()}><span class="pw-schluessel">{k.schluessel}</span> {k.titel}</a>
                  {#if k.serie}<i class="fa-solid fa-repeat schwach" title="Aus einer Serie"></i>{/if}</td>
                <td data-titel="Abgeschlossen"><span class="zahl">{k.abgeschlossen ? datumJahr(k.abgeschlossen, true) : ""}</span></td>
                <td data-titel="Zuständig"><span class="pw-uebersicht-wer">{#each k.zustaendig as p (p)}<Person id={p} />{/each}
                  <span>{k.zustaendig.map((p) => konto(p).name).join(", ")}</span></span></td>
                <td data-titel="Labels"><span class="pw-uebersicht-labels">{#each k.labels as l (l)}{@const lab = b.labels.find((x) => x.id === l)}
                  {#if lab}<span class="pw-label" data-farbe={lab.farbe}>{lab.name}</span>{/if}{/each}</span></td>
                {#if mitZeit}<td class="zahl" data-titel="Zeit"><span class="zahl">{dauer(zeitDerKarte(k.id))}</span></td>{/if}
              </tr>
            {:else}
              <tr><td colspan={mitZeit ? 5 : 4}><div class="leer"><i class="fa-solid fa-magnifying-glass"></i>
                <p>Keine der geladenen Karten passt zu "{suche}".</p></div></td></tr>
            {/each}
          </tbody>
        </table>
      </div>
      <div class="pw-uebersicht-mehr">
        {#if w.length}<span><span class="zahl">{treffer.length}</span> Treffer in <span class="zahl">{seiten.karten.length}</span> geladenen Karten</span>
        {:else}<span class="zahl">{seiten.karten.length} von {anzahl(seiten.gesamt)}</span>{/if}
        {#if seiten.weitere > 0}
          <button class="knopf ohne klein" disabled={seiten.laedt} onclick={() => void seiten.weiter()}
                  title="Lädt die nächsten {schritt} (Ladeschritt des Boards); Rollen ans Ende lädt auch">
            <i class="fa-solid fa-angles-down"></i>Mehr laden ({Math.min(seiten.weitere, schritt)} weitere)</button>
        {/if}
        {#if seiten.fehler}<span>{seiten.fehler}</span>{/if}
      </div>
    {/if}
  </div>
</div>
