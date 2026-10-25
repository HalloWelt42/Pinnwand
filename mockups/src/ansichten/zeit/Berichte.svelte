<script lang="ts">
  // Berichte: links die Auswahl als Schritte (Art, Zeitraum, Boards, Personen, Format), rechts die erstellten Berichte
  // aus der Kellerwolke oder die Vorschau genau dessen, was die Datei enthält. Erstellen legt die Datei im Ordner der
  // Pinnwand ab; von dort herunterladen oder vorlesen. Personen außer dir nur mit dem Recht "Zeiten anderer sehen".
  import { untrack } from "svelte";
  import { darf } from "../../beispiel/abfragen";
  import { melden } from "../../beispiel/anwendung/meldung.svelte";
  import { neueKennung } from "../../beispiel/anwendung/zeiten.svelte";
  import { HEUTE, ICH, JETZT } from "../../beispiel/daten";
  import { BERICHTE, BERICHTSORDNER } from "../../beispiel/daten-zeit";
  import { datumJahr, monatText, spanne, wann, wocheText } from "../../beispiel/format";
  import { konto, stand } from "../../beispiel/stand.svelte";
  import Person from "../../board/Person.svelte";
  import type { Bericht, BerichtArt, BerichtFormat } from "../../modell";
  import { monatsende, montagVon, plusMonate, plusTage } from "../../regeln/tage";
  import DatumFeld from "../../teile/DatumFeld.svelte";
  import { alsMarkdown, ARTNAMEN, dateiname, inhalt, sichtbarePersonen, titelVon, type Auswahl } from "./bericht";

  let { entwurf = "" }: { entwurf?: string } = $props();

  let rechts = $state<"liste" | "vorschau">("liste");
  let art = $state<BerichtArt>("stundennachweis");
  let zeitraum = $state("vorwoche");
  let eigenVon = $state("2026-10-01");
  let eigenBis = $state(HEUTE);
  let personen = $state<string[]>([ICH]);
  let boards = $state<string[]>(["b-prod"]);
  let format = $state<BerichtFormat>("pdf");
  let suche = $state("");
  /** in dieser Sitzung erstellte Berichte (die Ablage selbst liegt in der Kellerwolke) */
  let erstellt = $state<Bericht[]>([]);
  let neu = $state("");
  const liste = $derived([...erstellt, ...BERICHTE]);

  // vorgeführte Vorschau: Stundennachweis der letzten Woche für dich und Jonas, einmal je Entwurf
  $effect(() => {
    const e = entwurf;
    untrack(() => {
      rechts = e === "vorschau" ? "vorschau" : "liste";
      personen = e === "vorschau" ? [ICH, "k-jonas"] : [ICH];
    });
  });

  const montag = montagVon(HEUTE);
  const monatsanfang = HEUTE.slice(0, 8) + "01";
  const vormonat = plusMonate(monatsanfang, -1);
  const ZEITRAEUME: Record<string, { name: string; von: string; bis: string }> = {
    woche: { name: "Diese Woche", von: montag, bis: plusTage(montag, 6) },
    vorwoche: { name: "Letzte Woche", von: plusTage(montag, -7), bis: plusTage(montag, -1) },
    monat: { name: "Dieser Monat", von: monatsanfang, bis: monatsende(monatsanfang) },
    vormonat: { name: "Letzter Monat", von: vormonat, bis: monatsende(vormonat) },
    jahr: { name: "Dieses Jahr", von: `${HEUTE.slice(0, 4)}-01-01`, bis: `${HEUTE.slice(0, 4)}-12-31` },
  };
  const bereich = $derived(zeitraum === "eigen" ? { von: eigenVon, bis: eigenBis } : ZEITRAEUME[zeitraum]);
  function zeitraumText(): string {
    if (zeitraum === "woche" || zeitraum === "vorwoche") return wocheText(bereich.von);
    if (zeitraum === "monat" || zeitraum === "vormonat") return monatText(bereich.von);
    return spanne(bereich.von, bereich.bis);
  }

  /** Boards, in denen das Modul Berichte an ist und deine Rolle Berichte erstellen darf */
  const moeglicheBoards = $derived(stand.boards.filter((b) => b.module.berichte && darf(b, "berichte.erstellen")));
  const erlaubt = $derived(sichtbarePersonen(art === "stundennachweis" ? [] : boards, art === "stundennachweis"));
  const vorschlaege = $derived(erlaubt.filter((p) => !personen.includes(p) && konto(p).name.toLowerCase().includes(suche.trim().toLowerCase())).slice(0, 6));
  const auswahl = $derived<Auswahl>({ art, von: bereich.von, bis: bereich.bis, boards, personen: personen.filter((p) => erlaubt.includes(p)), format });
  const bereit = $derived((art !== "stundennachweis" || auswahl.personen.length > 0) && (art === "stundennachweis" || boards.length > 0) && bereich.von <= bereich.bis);
  const daten = $derived(inhalt(auswahl));
  const zeilenZahl = $derived(daten.abschnitte.reduce((s, a) => s + a.zeilen.length, 0));

  const ARTEN_WAHL: [BerichtArt, string, string][] = [
    ["stundennachweis", "fa-user-clock", "Soll, Ist und Differenz je Tag aus dem Zeitkonto, mit Karten und Abwesenheiten"],
    ["board", "fa-table-list", "Gebuchte Zeit je Karte eines Boards, mit Personen und Schätzung"],
    ["erledigt", "fa-circle-check", "Karten, die im Zeitraum erledigt wurden, mit Zuständigen und Zeit"],
  ];
  const FORMATE: [BerichtFormat, string, string][] = [["pdf", "PDF", "fa-file-pdf"], ["tabelle", "Tabelle", "fa-file-csv"], ["markdown", "Markdown", "fa-file-code"]];
  const SYMBOL: Record<BerichtFormat, string> = { pdf: "fa-file-pdf", tabelle: "fa-file-csv", markdown: "fa-file-code" };

  /** Spaltenbreite je Art der Spalte, damit alle Abschnitte gleich gebaut sind */
  function breite(spalte: string): string {
    if (["Soll", "Ist", "Differenz", "Zeit", "Schätzung"].includes(spalte)) return "zahl";
    if (["Tag", "Schlüssel", "Erledigt", "Zuständig", "Personen"].includes(spalte)) return "kurz";
    return "frei";
  }

  function boardUmschalten(id: string): void {
    boards = boards.includes(id) ? boards.filter((x) => x !== id) : [...boards, id];
  }
  function erstellen(): void {
    if (!bereit) return;
    const b: Bericht = { id: neueKennung("r"), art, titel: titelVon(auswahl), zeitraum: zeitraumText(), format, datei: dateiname(auswahl),
      erstellt: JETZT, groesse: format === "pdf" ? `${40 + zeilenZahl * 2} KB` : `${2 + Math.ceil(zeilenZahl / 8)} KB` };
    erstellt = [b, ...erstellt];
    neu = b.id;
    rechts = "liste";
    melden(`Abgelegt in ${BERICHTSORDNER}: ${b.datei}`);
  }
</script>

<div class="rahmen-kopf">
  <div class="seitenkopf">
    <h1>Berichte</h1>
    <div class="unterzeile">Auswertungen aus deinem Zeitkonto und den Boards, abgelegt in der Kellerwolke unter {BERICHTSORDNER}.</div>
  </div>
  <div class="kette pw-berichte-kette" aria-label="Schritte">
    {#each ["Art", "Zeitraum", "Boards", "Personen", "Format"] as s, i (s)}
      <span class="schritt erledigt"><i class="fa-solid fa-check"></i>{i + 1}. {s}</span><span class="pfeil erledigt"></span>
    {/each}
    <span class="schritt" class:jetzt={rechts === "vorschau"} class:offen={rechts !== "vorschau"}><i class="fa-solid fa-eye"></i>6. Vorschau</span>
  </div>
</div>

<div class="pw-zeiten-raum">
  <div class="spalten breit-rechts pw-berichte-spalten">
    <div class="rollfeld pw-berichte-schritte">
      <section class="bereich">
        <h2><span class="zaehler">1</span>Art</h2>
        <div class="wahl">
          {#each ARTEN_WAHL as [id, symbol, text] (id)}
            <label class:an={art === id}><input type="radio" name="berichtsart" value={id} bind:group={art} class="pw-arbeitszeit-unsichtbar" />
              <span class="kreis"></span><div><b><i class="fa-solid {symbol}"></i> {ARTNAMEN[id]}</b><span>{text}</span></div></label>
          {/each}
        </div>
      </section>

      <section class="bereich">
        <h2><span class="zaehler">2</span>Zeitraum <span class="schwach klein pw-berichte-gewaehlt">{zeitraumText()}</span></h2>
        <div class="pw-berichte-chips">
          {#each Object.entries(ZEITRAEUME) as [id, z] (id)}<button class="chip" class:aktiv={zeitraum === id} onclick={() => (zeitraum = id)}>{z.name}</button>{/each}
          <button class="chip" class:aktiv={zeitraum === "eigen"} onclick={() => (zeitraum = "eigen")}>Eigener</button>
        </div>
        {#if zeitraum === "eigen"}
          <div class="pw-arbeitszeit-felder">
            <label><span class="etikett">Von</span><DatumFeld tag={eigenVon} ontag={(t) => (eigenVon = t)} /></label>
            <label><span class="etikett">Bis</span><DatumFeld tag={eigenBis} ontag={(t) => (eigenBis = t)} /></label>
          </div>
        {/if}
      </section>

      <section class="bereich">
        <h2><span class="zaehler">3</span>Boards</h2>
        {#if art === "stundennachweis"}
          <p class="schwach klein">Der Stundennachweis kommt aus dem Zeitkonto und umfasst alle Boards.</p>
        {:else}
          <div class="pw-berichte-chips">
            {#each moeglicheBoards as b (b.id)}
              <button class="chip" class:aktiv={boards.includes(b.id)} aria-pressed={boards.includes(b.id)} onclick={() => boardUmschalten(b.id)}>
                <span class="pw-farbpunkt" data-farbe={b.farbe}></span>{b.name}</button>
            {/each}
          </div>
          <p class="schwach klein">Boards mit dem Modul Berichte, in denen du Berichte erstellen darfst.</p>
        {/if}
      </section>

      <section class="bereich">
        <h2><span class="zaehler">4</span>Personen {#if art !== "stundennachweis" && !personen.length}<span class="schwach klein">alle</span>{/if}</h2>
        <div class="pw-berichte-personen">
          {#each personen as p (p)}
            <span class="chip"><Person id={p} />{konto(p).name}
              <button class="knopf ohne symbol klein" title="Entfernen" onclick={() => (personen = personen.filter((x) => x !== p))}><i class="fa-solid fa-xmark"></i></button></span>
          {/each}
          <label class="suche"><i class="fa-solid fa-user-plus"></i><input bind:value={suche} placeholder="Person hinzufügen" /></label>
        </div>
        {#if vorschlaege.length}
          <div class="pw-berichte-vorschlaege">
            {#each vorschlaege as p (p)}<button class="chip" onclick={() => { personen = [...personen, p]; suche = ""; }}><Person id={p} />{konto(p).name}</button>{/each}
          </div>
        {/if}
        <p class="schwach klein">Andere Personen nur aus Boards, in denen du "Zeiten anderer sehen" darfst.</p>
      </section>

      <section class="bereich">
        <h2><span class="zaehler">5</span>Format</h2>
        <div class="stufen" role="group" aria-label="Format">
          {#each FORMATE as [id, name, symbol] (id)}<button class:an={format === id} onclick={() => (format = id)}><i class="fa-solid {symbol}"></i> {name}</button>{/each}
        </div>
      </section>

      <div class="pw-berichte-knoepfe">
        <button class="knopf" class:aktiv={rechts === "vorschau"} disabled={!bereit} onclick={() => (rechts = "vorschau")}><i class="fa-solid fa-eye"></i>Vorschau</button>
        <button class="knopf haupt" disabled={!bereit} onclick={erstellen}><i class="fa-solid fa-file-export"></i>Erstellen und ablegen</button>
      </div>
    </div>

    <div class="rollfeld pw-berichte-rechts">
      {#if rechts === "vorschau"}
        <div class="pw-berichte-vorschaukopf">
          <span class="etikett">Vorschau</span><span class="pw-schluessel">{dateiname(auswahl)}</span>
          <button class="knopf klein rechts" onclick={() => (rechts = "liste")}><i class="fa-solid fa-list-ul"></i>Erstellte Berichte</button>
        </div>
        {#if format === "markdown"}
          <pre class="pw-berichte-text">{alsMarkdown(daten)}</pre>
        {:else}
          <article class="pw-berichte-blatt" class:tabelle-format={format === "tabelle"}>
            {#if format === "pdf"}
              <header><span class="pw-marke-symbol"><i class="fa-solid fa-thumbtack"></i></span>
                <div><h2>{titelVon(auswahl)}</h2><span class="schwach">{zeitraumText()} · erstellt {datumJahr(HEUTE)} von {konto(ICH).name}</span></div></header>
            {/if}
            {#each daten.abschnitte as a (a.titel)}
              <section>
                <h3>{a.titel}</h3>
                <div class="tabellen-raum">
                  <table class="tabelle">
                    <colgroup>{#each a.spalten as sp, i (i)}<col class="b-{breite(sp)}" />{/each}</colgroup>
                    <thead><tr>{#each a.spalten as s, i (i)}<th class:zahl={["Soll", "Ist", "Differenz", "Zeit", "Schätzung"].includes(s)}>{s}</th>{/each}</tr></thead>
                    <tbody>
                      {#each a.zeilen as z, r (r)}<tr>{#each z as w, i (i)}<td class:zahl={["Soll", "Ist", "Differenz", "Zeit", "Schätzung"].includes(a.spalten[i])}>{w}</td>{/each}</tr>{/each}
                      {#if !a.zeilen.length}<tr><td colspan={a.spalten.length} class="schwach">Im Zeitraum nichts gebucht.</td></tr>{/if}
                    </tbody>
                    {#if a.summe}<tfoot><tr>{#each a.summe as w, i (i)}<td class:zahl={["Soll", "Ist", "Differenz", "Zeit", "Schätzung"].includes(a.spalten[i])}>{w}</td>{/each}</tr></tfoot>{/if}
                  </table>
                </div>
                {#if a.fuss && format === "pdf"}<p class="schwach klein">{a.fuss}</p>{/if}
              </section>
            {/each}
          </article>
        {/if}
      {:else}
        <section class="bereich">
          <h2 class="pw-arbeitszeit-titel">Erstellte Berichte <span class="zaehler">{liste.length}</span></h2>
          <p class="schwach klein"><i class="fa-solid fa-cloud"></i> Kellerwolke, {BERICHTSORDNER}</p>
          <div class="pw-berichte-liste">
            {#each liste as b (b.id)}
              <div class="pw-berichte-eintrag" class:neu={b.id === neu}>
                <i class="fa-solid {SYMBOL[b.format]} art"></i>
                <div class="was"><b>{b.titel}</b><span class="schwach klein">{b.zeitraum} · {wann(b.erstellt)} · {b.groesse}</span></div>
                <span class="knoepfe">
                  <button class="knopf symbol klein" title="Herunterladen: {b.datei}"><i class="fa-solid fa-download"></i></button>
                  <button class="knopf symbol klein" title="Vorlesen"><i class="fa-solid fa-volume-high"></i></button>
                </span>
              </div>
            {/each}
          </div>
        </section>
      {/if}
    </div>
  </div>
</div>
