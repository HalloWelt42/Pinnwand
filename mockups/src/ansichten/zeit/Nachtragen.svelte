<script lang="ts">
  // Zeit nachtragen, als Leiste rechts über dem Stundenzettel: Karte suchen (alle Boards, in denen du Zeit buchen darfst
  // und die Zeiterfassung an ist; keine Ideen), Tag, Dauer, Notiz. Links im Stundenzettel steht schon beim Tippen, wo die
  // Zeit landet; unten die Wirkung neben Buchen. Buchen lässt die Leiste offen für die nächste Buchung.
  import { darf, istAm, sollTag } from "../../beispiel/abfragen";
  import { buchen } from "../../beispiel/anwendung/zeiten.svelte";
  import { HEUTE, ICH } from "../../beispiel/daten";
  import { datum, datumJahr, dauer } from "../../beispiel/format";
  import { board, stand } from "../../beispiel/stand.svelte";
  import type { Karte } from "../../modell";
  import { dauerLesen } from "../../regeln/eingabe";
  import { plusTage } from "../../regeln/tage";
  import DatumFeld from "../../teile/DatumFeld.svelte";
  import KartenName from "./KartenName.svelte";

  let { tag: tagVorgabe, vorfuehren = false, schliessen, vorschauSetzen }: {
    tag: string; vorfuehren?: boolean; schliessen: () => void;
    vorschauSetzen: (v: { karte: string; tag: string; sek: number } | null) => void;
  } = $props();

  // svelte-ignore state_referenced_locally
  let suche = $state(vorfuehren ? "prüfvor" : "");
  // svelte-ignore state_referenced_locally
  let karteId = $state(vorfuehren ? "c-137" : "");
  // svelte-ignore state_referenced_locally
  let tag = $state(tagVorgabe);
  // svelte-ignore state_referenced_locally
  let dauerText = $state(vorfuehren ? "1,5" : "");
  // svelte-ignore state_referenced_locally
  let notiz = $state(vorfuehren ? "Anschläge gesetzt" : "");

  /** Auf dieser Karte darfst du Zeit buchen: Arbeit, Board mit Zeiterfassung, Recht "Eigene Zeit buchen" */
  function buchbar(k: Karte): boolean {
    const b = board(k.board);
    return b.module.zeiterfassung && k.art === "arbeit" && darf(b, "zeit.buchen");
  }
  const erledigt = (k: Karte) => !!board(k.board).spalten.find((s) => s.id === k.spalte)?.erledigt;
  const treffer = $derived.by(() => {
    const woerter = suche.toLowerCase().split(/\s+/).filter(Boolean);
    if (!woerter.length) return [];
    return stand.karten.filter((k) => buchbar(k) && woerter.every((w) => `${k.schluessel} ${k.titel}`.toLowerCase().includes(w)))
      .sort((a, b) => Number(erledigt(a)) - Number(erledigt(b)) || b.bewegtAm.localeCompare(a.bewegtAm)).slice(0, 8);
  });
  const gewaehlt = $derived(stand.karten.find((k) => k.id === karteId && buchbar(k)));
  const sek = $derived(dauerLesen(dauerText));
  const bereit = $derived(!!gewaehlt && !!sek && sek > 0);

  $effect(() => { vorschauSetzen(bereit ? { karte: karteId, tag, sek: sek! } : null); });

  const aufKarte = $derived(stand.zeiteintraege.filter((e) => e.konto === ICH && e.datum === tag && e.karte === karteId).reduce((s, e) => s + e.sekunden, 0));
  const tagIst = $derived(istAm(ICH, tag));
  const tagSoll = $derived(sollTag(ICH, tag)?.sollSek ?? 0);

  function absenden(): void {
    if (!bereit) return;
    buchen(karteId, tag, sek!, notiz);
    dauerText = "";
    notiz = "";
  }
</script>

<aside class="pw-zeiten-leiste" aria-label="Zeit nachtragen">
  <div class="kopf">
    <span class="etikett">Nachtragen</span>
    <h2>Zeit auf eine Karte buchen</h2>
    <button class="knopf ohne symbol klein rechts" title="Schließen" onclick={schliessen}><i class="fa-solid fa-xmark"></i></button>
  </div>

  <div class="inhalt pw-zeiten-nachtragen">
    <section>
      <div class="etikett"><span class="zaehler">1</span>Karte</div>
      <label class="suche"><i class="fa-solid fa-magnifying-glass"></i>
        <input bind:value={suche} oninput={() => (karteId = "")} placeholder="Schlüssel oder Titel, in allen Boards"
               title="Jedes Wort muss vorkommen; Ideen und Boards ohne Zeiterfassung fehlen" /></label>
      {#if gewaehlt}
        <div class="pw-zeiten-gewaehlt"><KartenName id={gewaehlt.id} /><span class="schwach klein">{board(gewaehlt.board).name}</span>
          <button class="knopf ohne symbol klein" title="Andere Karte wählen" onclick={() => (karteId = "")}><i class="fa-solid fa-xmark"></i></button></div>
      {:else if treffer.length}
        <div class="pw-zeiten-treffer" role="listbox" aria-label="Treffer">
          {#each treffer as k (k.id)}
            {@const b = board(k.board)}
            <button class="zeile" role="option" aria-selected="false" onclick={() => (karteId = k.id)}>
              <KartenName id={k.id} /><span class="spalte">{b.spalten.find((s) => s.id === k.spalte)?.name}</span>
            </button>
          {/each}
        </div>
      {:else if suche.trim()}
        <p class="schwach klein">Keine Karte gefunden, auf der du Zeit buchen darfst.</p>
      {/if}
    </section>

    <section>
      <div class="etikett"><span class="zaehler">2</span>Tag</div>
      <div class="pw-zeiten-tagwahl">
        <DatumFeld {tag} ontag={(t) => (tag = t)} breite="190px" />
        <button class="chip" class:aktiv={tag === HEUTE} onclick={() => (tag = HEUTE)}>Heute</button>
        <button class="chip" class:aktiv={tag === plusTage(HEUTE, -1)} onclick={() => (tag = plusTage(HEUTE, -1))}>Gestern</button>
      </div>
    </section>

    <section>
      <div class="etikett"><span class="zaehler">3</span>Dauer</div>
      <div class="pw-zeiten-tagwahl">
        <input class="eingabe zahl" class:falsch={dauerText.trim() !== "" && sek === null} bind:value={dauerText} placeholder="1:30, 1:30:15 oder 1,5"
               title="H:MM, H:MM:SS, Stunden mit Komma oder 90min" style="width: 190px"
               onkeydown={(e) => { if (e.key === "Enter") absenden(); }} />
        <span class="pw-zeiten-gelesen" class:falsch={dauerText.trim() !== "" && sek === null}>
          {dauerText.trim() === "" ? "" : sek === null ? "Dauer bitte wie 1:30, 1,5 oder 90min" : `= ${dauer(sek, true)}`}</span>
      </div>
      <input class="eingabe" bind:value={notiz} placeholder="Notiz (steht im Stundennachweis)" />
    </section>
  </div>

  <div class="fuss pw-zeiten-nachtragen-fuss">
    {#if bereit}
      <div class="pw-zeiten-wirkung" aria-live="polite">
        <div class="zeile-wert"><span>{gewaehlt!.schluessel} am {datum(tag, true)}</span><b class="zahl">{dauer(aufKarte)} auf {dauer(aufKarte + sek!)}</b></div>
        <div class="zeile-wert"><span>{datumJahr(tag, true)} gesamt</span><b class="zahl">{dauer(tagIst)} auf {dauer(tagIst + sek!)} <small>von {dauer(tagSoll)} Soll</small></b></div>
      </div>
    {/if}
    <div class="knoepfe">
      <button class="knopf haupt" disabled={!bereit} onclick={absenden} title="Ein eigener Eintrag nachgetragen mit deiner Person, an genau diesem Tag"><i class="fa-solid fa-check"></i>Buchen</button>
      <button class="knopf" onclick={schliessen}>Fertig</button>
    </div>
  </div>
</aside>
