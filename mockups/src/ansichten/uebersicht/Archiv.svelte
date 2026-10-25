<script lang="ts">
  // Archiv eines Boards: erledigte Karten, deren Abschluss älter als die Archivgrenze ist. Das Board lädt sie nie (reine
  // Ladegrenze, eine größere Grenze holt sie zurück); hier stehen sie neueste zuerst und seitenweise (beim Rollen lädt
  // die nächste Seite, der Fuß nennt die Zahl), durchsuchbar über die Werte der Karte. Ein Klick lädt die Karte einzeln
  // und öffnet sie über ihren Pfad; zurückholen geht dort über den Status.
  import { HEUTE } from "../../beispiel/daten";
  import { datum, dauer } from "../../beispiel/format";
  import { board as holeBoard, konto } from "../../beispiel/stand.svelte";
  import Person from "../../board/Person.svelte";
  import type { Karte } from "../../modell";
  import { boardPfad, gehe } from "../../weg.svelte";
  import { einzelnLaden } from "./aktionen.svelte";
  import { ARCHIV, ARCHIV_GESAMT, ARCHIVGRENZE } from "./daten";
  import Meldung from "./Meldung.svelte";
  import NebenKopf from "./NebenKopf.svelte";

  let { boardId }: { boardId: string } = $props();
  const b = $derived(holeBoard(boardId));
  const seite = $derived(ARCHIV.filter((k) => k.board === b.id));
  const gesamt = $derived(ARCHIV_GESAMT[b.id] ?? seite.length);
  const mitZeit = $derived(b.module.zeiterfassung);

  /** erster Tag, der noch im Board bleibt: Abschluss davor liegt im Archiv */
  const grenze = $derived.by(() => {
    const d = new Date(HEUTE + "T12:00:00");
    d.setDate(d.getDate() - ARCHIVGRENZE);
    return d.toISOString().slice(0, 10);
  });

  // Suche über die Werte (nicht über gespeicherte Rohtexte): jedes Wort muss vorkommen
  let suche = $state("");
  function text(k: Karte): string {
    return [k.schluessel, k.titel, k.beschreibung, k.notizen, ...k.labels.map((l) => b.labels.find((x) => x.id === l)?.name),
      ...Object.values(k.felder), ...k.kommentare.map((c) => c.text), ...k.checkliste.map((p) => p.text),
      ...k.zustaendig.map((p) => konto(p).name)].filter(Boolean).join(" ").toLowerCase();
  }
  const woerter = $derived(suche.toLowerCase().split(/\s+/).filter(Boolean));
  const treffer = $derived(woerter.length ? seite.filter((k) => woerter.every((w) => text(k).includes(w))) : seite);

  function oeffnen(k: Karte): void {
    einzelnLaden(k);
    gehe(boardPfad(b.kuerzel, k.schluessel.split("-")[1]));
  }
</script>

<div class="pw-uebersicht-seite">
  <div class="rahmen-kopf">
    <NebenKopf board={b} titel="Archiv" symbol="fa-box-archive" angabe="{gesamt} {gesamt === 1 ? 'Karte' : 'Karten'}, abgeschlossen vor dem {datum(grenze)}{grenze.slice(0, 4)}"
               erklaerung="Erledigte Karten, deren Abschluss älter als {ARCHIVGRENZE} Tage ist. Das Board lädt sie nicht mehr; eine größere Grenze holt sie zurück. Zurückholen geht in der Karte über den Status." />
    <div class="pw-uebersicht-suchzeile">
      <label class="suche"><i class="fa-solid fa-magnifying-glass"></i>
        <input placeholder="Im Archiv suchen: Titel, Schlüssel, Labels, Felder, Kommentare" aria-label="Archiv durchsuchen" bind:value={suche} /></label>
      <a class="chip" href={boardPfad(b.kuerzel, "einstellungen")} title="Archivgrenze in den Einstellungen des Boards">
        <i class="fa-solid fa-sliders"></i>Grenze {ARCHIVGRENZE} Tage</a>
    </div>
  </div>

  <div class="rollfeld">
    {#if !seite.length}
      <div class="leer"><i class="fa-solid fa-box-archive"></i><h2>Noch nichts im Archiv</h2>
        <p>Erledigte Karten kommen hierher, wenn ihr Abschluss älter als {ARCHIVGRENZE} Tage ist.</p></div>
    {:else}
      <div class="tabellen-raum pw-uebersicht-archiv">
        <table class="tabelle karten">
          <thead>
            <tr><th>Karte</th><th>Abgeschlossen</th><th>Zuständig</th><th>Labels</th>{#if mitZeit}<th class="zahl">Zeit</th>{/if}</tr>
          </thead>
          <tbody>
            {#each treffer as k (k.id)}
              <!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_noninteractive_element_interactions -->
              <tr onclick={() => oeffnen(k)}>
                <td class="karte-zelle"><a href={boardPfad(b.kuerzel, k.schluessel.split("-")[1])} onclick={(e) => { e.stopPropagation(); einzelnLaden(k); }}>
                  <span class="pw-schluessel">{k.schluessel}</span> {k.titel}</a>
                  {#if k.serie}<i class="fa-solid fa-repeat schwach" title="Aus einer Serie"></i>{/if}</td>
                <td data-titel="Abgeschlossen"><span class="zahl">{datum(k.abgeschlossen ?? "", true)}{(k.abgeschlossen ?? "").slice(0, 4)}</span></td>
                <td data-titel="Zuständig"><span class="pw-uebersicht-wer">{#each k.zustaendig as p (p)}<Person id={p} />{/each}
                  <span>{k.zustaendig.map((p) => konto(p).name).join(", ")}</span></span></td>
                <td data-titel="Labels"><span class="pw-uebersicht-labels">{#each k.labels as l (l)}{@const lab = b.labels.find((x) => x.id === l)}
                  {#if lab}<span class="pw-label" data-farbe={lab.farbe}>{lab.name}</span>{/if}{/each}</span></td>
                {#if mitZeit}<td class="zahl" data-titel="Zeit"><span class="zahl">{dauer(k.erfasstSek)}</span></td>{/if}
              </tr>
            {:else}
              <tr><td colspan={mitZeit ? 5 : 4}><div class="leer"><i class="fa-solid fa-magnifying-glass"></i>
                <p>Keine archivierte Karte passt zu "{suche}".</p></div></td></tr>
            {/each}
          </tbody>
        </table>
      </div>
      <div class="pw-uebersicht-mehr">
        {#if woerter.length}<span><span class="zahl">{treffer.length}</span> Treffer</span>
        {:else}<span class="zahl">{seite.length} von {gesamt} Karten</span>
          {#if seite.length < gesamt}<span class="schwach"><i class="fa-solid fa-angles-down"></i>Beim Rollen laden die nächsten</span>{/if}{/if}
      </div>
    {/if}
  </div>
  <Meldung />
</div>
