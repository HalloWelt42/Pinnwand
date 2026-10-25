<script lang="ts">
  // Archiv eines Boards: erledigte Karten, deren Abschluss älter als die Archivgrenze des Boards ist. Das Board lädt sie
  // nie (reine Ladegrenze, eine größere Grenze holt sie zurück); hier stehen sie neueste zuerst und seitenweise (beim
  // Rollen lädt die nächste Seite, der Fuß nennt die Zahl), durchsuchbar über die Werte der Karte. Ein Klick öffnet die
  // Karte über ihren Pfad; zurückholen geht dort über den Status.
  import { archivVon, kartenNummer, passt, woerter, zeitDerKarte } from "../../daten/abfragen";
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
  const tage = $derived(b.einstellungen.archivTage);
  const seite = $derived(archivVon(b));
  const gesamt = $derived(seite.length);
  const mitZeit = $derived(b.module.zeiterfassung);
  /** Abschluss vor diesem Tag: im Archiv */
  const grenze = $derived(plusTage(uhr.heute, -tage));

  let suche = $state("");
  const w = $derived(woerter(suche));
  const treffer = $derived(seite.filter((k) => passt(k, b, w)));

  function pfad(k: Karte): string {
    return boardPfad(b.kuerzel, kartenNummer(k));
  }
</script>

<div class="pw-uebersicht-seite">
  <div class="rahmen-kopf">
    <NebenKopf board={b} titel="Archiv" symbol="fa-box-archive" angabe="{gesamt} {gesamt === 1 ? 'Karte' : 'Karten'}, abgeschlossen vor dem {datumJahr(grenze)}"
               erklaerung="Erledigte Karten, deren Abschluss älter als {tage} Tage ist. Das Board lädt sie nicht mehr; eine größere Grenze holt sie zurück. Zurückholen geht in der Karte über den Status." />
    <div class="pw-uebersicht-suchzeile">
      <label class="suche"><i class="fa-solid fa-magnifying-glass"></i>
        <input placeholder="Im Archiv suchen: Titel, Schlüssel, Labels, Felder, Kommentare" aria-label="Archiv durchsuchen" bind:value={suche} /></label>
      <a class="chip" href={boardPfad(b.kuerzel, "einstellungen")} title="Archivgrenze in den Einstellungen des Boards">
        <i class="fa-solid fa-sliders"></i>Grenze {tage} Tage</a>
    </div>
  </div>

  <div class="rollfeld">
    {#if !seite.length}
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
                <p>Keine archivierte Karte passt zu "{suche}".</p></div></td></tr>
            {/each}
          </tbody>
        </table>
      </div>
      <div class="pw-uebersicht-mehr">
        {#if w.length}<span><span class="zahl">{treffer.length}</span> Treffer</span>
        {:else}<span class="zahl">{seite.length} von {gesamt} Karten</span>
          {#if seite.length < gesamt}<span class="schwach"><i class="fa-solid fa-angles-down"></i>Beim Rollen laden die nächsten</span>{/if}{/if}
      </div>
    {/if}
  </div>
</div>
