<script lang="ts">
  // Nachtrag am Folgetag als Bereich auf der Seite (kein Fenster über allem): deine vorgebuchten Zeiten vergangener
  // Tage aus Serien und Terminen. Bestätigen bucht die Dauer auf den Tag (Vorschlag: geplante Zeit, anpassbar);
  // Verwerfen heißt "fand für dich nicht statt": eine Serienkarte nur für dich geht in den Papierkorb, ihr Tag kommt
  // nicht wieder; sonst entfällt nur deine Zeit. Später schiebt auf; ohne Antwort zählt nichts. Nur deine Zeiten.
  import { datum, dauer } from "../../beispiel/format";
  import { konto } from "../../beispiel/stand.svelte";
  import Person from "../../board/Person.svelte";
  import { boardVon, plan } from "./plan.svelte";
  import type { Nachtragposten } from "./typen";

  let { posten, vorbelegt = {}, schliessen }: {
    posten: Nachtragposten[];
    /** vorgeführte Eingaben: Dauer je Bezug (etwa angepasst) */
    vorbelegt?: Record<string, string>;
    schliessen: () => void;
  } = $props();

  const schluessel = (p: Nachtragposten): string => `${p.bezug}|${p.tag}`;
  /** eingegebene Dauer je Posten; ohne Eingabe gilt die vorgeführte, sonst die geplante */
  let werte = $state<Record<string, string>>({});
  let erledigt = $state<Record<string, "bestaetigt" | "verworfen">>({});
  const wert = (p: Nachtragposten): string => werte[schluessel(p)] ?? vorbelegt[p.bezug] ?? dauer(p.geplantMin * 60);

  const tage = $derived([...new Set(posten.map((p) => p.tag))]);
  const offen = $derived(posten.filter((p) => !erledigt[schluessel(p)]).length);

  function nurFuerDich(p: Nachtragposten): boolean {
    return p.art === "serie" && (plan.serien.find((s) => s.id === p.bezug)?.teilnehmer.length ?? 0) === 1;
  }
  function verwerfenText(p: Nachtragposten): string {
    if (p.art === "termin") return "fand für dich nicht statt";
    return nurFuerDich(p) ? "Karte im Papierkorb, der Tag kommt nicht wieder" : "deine Zeit entfällt, die Karte bleibt";
  }
  function alleBestaetigen(): void {
    for (const p of posten) erledigt[schluessel(p)] ??= "bestaetigt";
  }
</script>

<section class="bereich pw-serien-nachtrag" aria-label="Nachtrag deiner vorgebuchten Zeiten">
  <div class="nachtragkopf">
    <i class="fa-solid fa-clock-rotate-left"></i>
    <div class="text">
      <h2>Nachtrag: {offen} {offen === 1 ? "Zeit wartet" : "Zeiten warten"} auf dich</h2>
      <p class="leise">Deine vorgebuchten Zeiten zählen erst, wenn du sie bestätigst. Anpassen, wenn es länger oder kürzer war; verwerfen,
        wenn es nicht stattfand.</p>
    </div>
    <button class="knopf ohne klein" onclick={schliessen} title="Zuklappen; morgen fragt der Nachtrag wieder">Später</button>
  </div>

  {#each tage as tag (tag)}
    <div class="etikett">{datum(tag, true)}</div>
    <div class="liste">
      {#each posten.filter((p) => p.tag === tag) as p (schluessel(p))}
        {@const k = schluessel(p)}
        {@const b = boardVon(p.board)}
        {@const geplant = dauer(p.geplantMin * 60)}
        <div class="zeile-nachtrag" class:fertig={!!erledigt[k]}>
          <span class="zahl wann">{p.von ?? "ganztägig"}</span>
          <span class="was">
            <b><i class="fa-solid {p.art === 'serie' ? 'fa-repeat' : 'fa-handshake'}" title={p.art === "serie" ? "Serie" : "Termin"}></i>{p.titel}</b>
            <span class="schwach">{b?.name} · {p.art === "serie" ? "Serie" : "Termin"} · geplant {geplant}
              {#if p.bestaetigt.length}· bestätigt von
                {#each p.bestaetigt as x (x)}<span class="pw-serien-mini" title="{konto(x).name} hat bestätigt"><Person id={x} /></span>{/each}{/if}</span>
          </span>
          {#if erledigt[k] === "bestaetigt"}
            <span class="zustand fertig"><i class="fa-solid fa-check"></i>{wert(p)} gebucht</span>
            <button class="knopf ohne klein" onclick={() => delete erledigt[k]}>Rückgängig</button>
          {:else if erledigt[k] === "verworfen"}
            <span class="zustand aus" title={verwerfenText(p)}><i class="fa-solid fa-ban"></i>verworfen</span>
            <button class="knopf ohne klein" onclick={() => delete erledigt[k]}>Rückgängig</button>
          {:else}
            <span class="dauer">
              <input class="eingabe" value={wert(p)} oninput={(e) => (werte[k] = e.currentTarget.value)}
                     title="Dauer als Stunden:Minuten; vorbelegt mit der geplanten Zeit" aria-label="Dauer {p.titel}" />
              {#if wert(p) !== geplant}<span class="schwach klein">statt {geplant}</span>{/if}
            </span>
            <button class="knopf klein" onclick={() => (erledigt[k] = "bestaetigt")} title="Bucht {wert(p)} auf {datum(p.tag, true)}">
              <i class="fa-solid fa-check"></i>Bestätigen</button>
            <button class="knopf ohne klein" onclick={() => (erledigt[k] = "verworfen")} title="Verwerfen: {verwerfenText(p)}">Verwerfen</button>
          {/if}
        </div>
      {/each}
    </div>
  {/each}

  <div class="nachtragfuss">
    <button class="knopf haupt" onclick={alleBestaetigen} disabled={offen === 0} title="Bestätigt alle offenen mit der eingetragenen Dauer"><i class="fa-solid fa-check-double"></i>Alle offenen bestätigen</button>
    <span class="schwach klein">Ohne Antwort zählt nichts; nachholen geht jederzeit unter Zeiten.</span>
  </div>
</section>
