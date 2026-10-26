<script lang="ts">
  // Karte am Telefon bearbeiten (Nutzer: "Titel, Beschreibung, Fällig, Zuständig"): ein schlichtes Formular wie beim
  // Erfassen, gespeichert über denselben Anwendungsfall wie am Rechner, mit Rückgängig; nur Geändertes geht hinaus.
  // Hat jemand anders inzwischen dasselbe Feld geändert, wird nicht still überschrieben: die Ansicht fragt, ob der
  // jetzige Stand bleibt oder die eigene Änderung gilt. Notizen, Labels, Priorität und eigene Felder bleiben am Rechner.
  import { untrack } from "svelte";
  import { darf, kartenNummer } from "../../daten/abfragen";
  import { bearbeiten, type Kartenaenderung } from "../../daten/anwendung/karten.svelte";
  import { board, karte as holeKarte, konto, mitKonto } from "../../daten/stand.svelte";
  import { uhr } from "../../daten/uhr.svelte";
  import Person from "../../board/Person.svelte";
  import DatumFeld from "../../teile/DatumFeld.svelte";
  import { boardPfad, gehe, wert } from "../../weg.svelte";
  import { faelligWahl } from "./faellig";
  import TelefonSchale from "./TelefonSchale.svelte";
  import { telPfad } from "./weg";

  let { kartenId }: { kartenId: string } = $props();

  // was die Karte beim Öffnen hatte (bewusst nur einmal gelesen): Vorgabe der Felder und Grundlage, um fremde
  // Änderungen zu erkennen
  const anfang = untrack(() => holeKarte(kartenId));
  const gekannt: Kartenaenderung = {
    titel: anfang?.titel ?? "", beschreibung: anfang?.beschreibung, faellig: anfang?.faellig, zustaendig: [...(anfang?.zustaendig ?? [])],
  };
  let titel = $state(gekannt.titel ?? "");
  let beschreibung = $state(gekannt.beschreibung ?? "");
  let faellig = $state(gekannt.faellig ?? "");
  let zustaendig = $state<string[]>([...(gekannt.zustaendig ?? [])]);
  let datumGueltig = $state(true);
  let konflikt = $state(false);

  const k = $derived(holeKarte(kartenId));
  const b = $derived(k ? board(k.board) : undefined);
  const darfEs = $derived(!!b && darf(b, "karten.bearbeiten"));
  const detail = $derived(k && b ? telPfad(boardPfad(b.kuerzel, kartenNummer(k)), wert("von") ? { von: wert("von") } : {}) : telPfad("/boards"));
  const mitglieder = $derived(b ? mitKonto(b).map((m) => m.konto) : []);
  const FAELLIG = faelligWahl(uhr.heute);

  /** nur Geändertes, mit dem Text der Meldung */
  function aenderung(): [Kartenaenderung, string[]] {
    const a: Kartenaenderung = {};
    const was: string[] = [];
    if (titel.trim() !== gekannt.titel) { a.titel = titel.trim(); was.push("Titel"); }
    if (beschreibung.trim() !== (gekannt.beschreibung ?? "").trim()) { a.beschreibung = beschreibung.trim() || undefined; was.push("Beschreibung"); }
    if (faellig !== (gekannt.faellig ?? "")) { a.faellig = faellig || undefined; was.push("Fällig"); }
    const vorher = gekannt.zustaendig ?? [];
    if (zustaendig.length !== vorher.length || zustaendig.some((p) => !vorher.includes(p))) { a.zustaendig = zustaendig; was.push("Zuständig"); }
    return [a, was];
  }

  const geaendert = $derived(aenderung()[1].length > 0);

  async function speichern(ueberschreiben = false): Promise<void> {
    if (!k) return;
    const [a, was] = aenderung();
    if (!was.length) { gehe(detail); return; }
    const vorher = Object.fromEntries(Object.keys(a).map((f) => [f, gekannt[f as keyof Kartenaenderung]])) as Kartenaenderung;
    const ok = await bearbeiten(k.id, a, `${was.join(", ")} geändert`, { gekannt: vorher, ueberschreiben, beiKonflikt: () => (konflikt = true) });
    if (ok) gehe(detail);
  }

  function zuweisen(p: string): void {
    zustaendig = zustaendig.includes(p) ? zustaendig.filter((x) => x !== p) : [...zustaendig, p];
  }
</script>

{#snippet knoepfe()}
  <div class="pw-tel-aktionen">
    <a class="knopf" href={detail}><i class="fa-solid fa-xmark"></i>Abbrechen</a>
    <button class="knopf haupt" disabled={!titel.trim() || !datumGueltig || !geaendert} title={datumGueltig ? "" : "Das Datum ist nicht lesbar"}
            onclick={() => speichern()}><i class="fa-solid fa-check"></i>Speichern</button>
  </div>
{/snippet}

<TelefonSchale titel={k?.schluessel ?? "Karte"} unter="Bearbeiten" reiter="boards" zurueck={detail} unten={k && darfEs ? knoepfe : undefined}>
  {#if !k || !b}
    <div class="leer"><i class="fa-solid fa-circle-question"></i><h2>Diese Karte gibt es nicht (mehr)</h2></div>
  {:else if !darfEs}
    <div class="leer"><i class="fa-solid fa-lock"></i><h2>Nur lesen</h2><p>Dir fehlt in {b.name} das Recht Karten bearbeiten.</p></div>
  {:else}
    {#if konflikt}
      <div class="hinweis warnung"><i class="fa-solid fa-code-merge"></i>
        <div><b>{k.schluessel} wurde inzwischen geändert.</b> Deine Änderung ist nicht gespeichert, damit nichts still
          überschrieben wird.
          <div class="pw-tel-chips"><a class="chip" href={detail}>Jetzige behalten</a>
            <button class="chip" onclick={() => speichern(true)}>Meine übernehmen</button></div></div>
      </div>
    {/if}
    <label class="pw-tel-abschnitt">
      <span class="etikett">Titel</span>
      <textarea class="eingabe" rows="2" bind:value={titel}></textarea>
    </label>
    <label class="pw-tel-abschnitt">
      <span class="etikett">Beschreibung</span>
      <textarea class="eingabe" rows="6" bind:value={beschreibung} placeholder="Markdown: **fett**, - Liste, @Name erwähnt"></textarea>
    </label>
    <section class="pw-tel-abschnitt" aria-label="Fällig">
      <div class="etikett">Fällig</div>
      <DatumFeld tag={faellig} ontag={(t) => (faellig = t)} bind:gueltig={datumGueltig} leerErlaubt titel="Fällig wie 30.10.2026 oder 30.10.; leer: ohne" />
      <div class="pw-tel-chips">
        {#each FAELLIG as [name, iso] (iso)}
          <button class="chip" aria-pressed={faellig === iso} onclick={() => (faellig = iso)}>{name}</button>
        {/each}
        <button class="chip" aria-pressed={!faellig} onclick={() => (faellig = "")}>Ohne</button>
      </div>
    </section>
    <section class="pw-tel-abschnitt" aria-label="Zuständig">
      <div class="etikett">Zuständig</div>
      <div class="pw-tel-wahl">
        {#each mitglieder as p (p)}
          <button class:an={zustaendig.includes(p)} aria-pressed={zustaendig.includes(p)} onclick={() => zuweisen(p)}>
            <Person id={p} />{konto(p).name}{#if zustaendig.includes(p)}<i class="fa-solid fa-check"></i>{/if}</button>
        {/each}
      </div>
    </section>
  {/if}
</TelefonSchale>
