<script lang="ts">
  // Nachtrag am Folgetag als Bereich auf der Seite (kein Fenster über allem): deine vorgebuchten Zeiten vergangener
  // Tage aus Serien und Terminen. Bestätigen bucht bei einer Serie die Dauer als Zeiteintrag auf die Karte des Tags
  // (Vorschlag: geplante Dauer, anpassbar), bei einem Termin zählt die geplante Zeit. Verwerfen heißt "fand für dich
  // nicht statt". Jede Antwort meldet sich unten mit Rückgängig; Später klappt zu, ohne Antwort zählt nichts.
  import { serie } from "../../beispiel/abfragen";
  import { alleBestaetigen, nachtragBestaetigen, nachtragVerwerfen } from "../../beispiel/anwendung/serien.svelte";
  import { datum, dauer } from "../../beispiel/format";
  import { karte, konto } from "../../beispiel/stand.svelte";
  import Person from "../../board/Person.svelte";
  import type { Nachtragposten } from "../../regeln/serien";
  import DauerFeld from "../../teile/DauerFeld.svelte";
  import { boardVon } from "./lesen";

  let { posten, vorbelegt = {}, schliessen }: {
    posten: Nachtragposten[];
    /** vorgeführte Eingaben: Dauer in Sekunden je Serie und Tag ("serie|tag"), etwa eine angepasste */
    vorbelegt?: Record<string, number>;
    schliessen: () => void;
  } = $props();

  const schluessel = (p: Nachtragposten): string => `${p.bezug}|${p.tag}`;
  /** eingegebene Dauer je Posten (Stand der Ansicht); ohne Eingabe gilt die vorgeführte, sonst die geplante */
  let werte = $state<Record<string, number>>({});
  const wert = (p: Nachtragposten): number => werte[schluessel(p)] ?? vorbelegt[schluessel(p)] ?? p.geplantMin * 60;
  const tage = $derived([...new Set(posten.map((p) => p.tag))]);

  function verwerfenText(p: Nachtragposten): string {
    if (p.art === "termin") return "fand für dich nicht statt, es zählt keine Zeit";
    const allein = (serie(p.bezug)?.teilnehmer.length ?? 0) === 1 || (p.karte ? karte(p.karte)?.zustaendig.length === 1 : false);
    return allein ? "die Karte geht in den Papierkorb, der Tag zählt als verworfen" : "nur deine Zeit entfällt, die Karte bleibt";
  }
  function alle(): void {
    alleBestaetigen(Object.fromEntries(posten.map((p) => [schluessel(p), wert(p)])));
  }
</script>

<section class="bereich pw-serien-nachtrag" aria-label="Nachtrag deiner vorgebuchten Zeiten">
  <div class="nachtragkopf">
    <i class="fa-solid fa-clock-rotate-left"></i>
    <div class="text">
      <h2>Nachtrag: {posten.length ? `${posten.length} ${posten.length === 1 ? "Zeit wartet" : "Zeiten warten"} auf dich` : "alles beantwortet"}</h2>
      <p class="leise">Deine vorgebuchten Zeiten zählen erst, wenn du sie bestätigst. Anpassen, wenn es länger oder kürzer war; verwerfen,
        wenn es nicht stattfand.</p>
    </div>
    <button class="knopf ohne klein" onclick={schliessen} title="Zuklappen; morgen fragt der Nachtrag wieder">Später</button>
  </div>

  {#each tage as tag (tag)}
    <div class="etikett">{datum(tag, true)}</div>
    <div class="liste">
      {#each posten.filter((p) => p.tag === tag) as p (schluessel(p))}
        {@const b = boardVon(p.board)}
        {@const geplant = p.geplantMin * 60}
        {@const k = p.karte ? karte(p.karte) : undefined}
        <div class="zeile-nachtrag">
          <span class="zahl wann">{p.von ?? "ganztägig"}</span>
          <span class="was">
            <b><i class="fa-solid {p.art === 'serie' ? 'fa-repeat' : 'fa-handshake'}" title={p.art === "serie" ? "Serie" : "Termin"}></i>{p.titel}</b>
            <span class="schwach">{b?.name}{k ? ` · ${k.schluessel}` : ""} · {p.art === "serie" ? "Serie" : "Termin"} · geplant {dauer(geplant)}
              {#if p.bestaetigt.length}· bestätigt von
                {#each p.bestaetigt as x (x)}<span class="pw-serien-mini" title="{konto(x).name} hat bestätigt"><Person id={x} /></span>{/each}{/if}</span>
          </span>
          <span class="dauer">
            {#if p.art === "serie"}
              <DauerFeld sek={wert(p)} onwert={(sek) => (werte[schluessel(p)] = sek)} klasse="feld" leerErlaubt={false}
                         titel="Dauer als Stunden:Minuten; vorbelegt mit der geplanten Zeit" />
              {#if wert(p) !== geplant}<span class="schwach klein">statt {dauer(geplant)}</span>{/if}
            {:else}
              <span class="zahl" title="Ein Termin zählt mit seiner geplanten Zeit">{dauer(geplant)}</span>
            {/if}
          </span>
          <button class="knopf klein" onclick={() => nachtragBestaetigen(p, wert(p))} title="Bucht {dauer(wert(p))} auf {datum(p.tag, true)}">
            <i class="fa-solid fa-check"></i>Bestätigen</button>
          <button class="knopf ohne klein" onclick={() => nachtragVerwerfen(p)} title="Verwerfen: {verwerfenText(p)}">Verwerfen</button>
        </div>
      {/each}
    </div>
  {:else}
    <p class="schwach klein">Alle vorgebuchten Zeiten sind beantwortet; die letzte Antwort lässt sich unten rückgängig machen.</p>
  {/each}

  {#if posten.length}
    <div class="nachtragfuss">
      <button class="knopf haupt" onclick={alle} title="Bestätigt alle offenen mit der eingetragenen Dauer"><i class="fa-solid fa-check-double"></i>Alle offenen bestätigen</button>
      <span class="schwach klein">Ohne Antwort zählt nichts; nachholen geht jederzeit unter Zeiten.</span>
    </div>
  {/if}
</section>
