<script lang="ts">
  // Berichte: links die Auswahl als Schritte (Art, Zeitraum, Boards, Personen, Format), rechts die erstellten Berichte
  // oder die Vorschau genau dessen, was die Datei enthält (vom Server gerechnet). Erstellen legt die Datei in der
  // Kellerwolke im Ordner Berichte der Pinnwand ab; von dort lädst du sie herunter. Im Stundennachweis stehen außer dir
  // nur Personen, deren Abwesenheiten du siehst; in Board-Berichten zählt die Zeit anderer nur mit "Zeiten anderer sehen".
  import { darf } from "../../daten/abfragen";
  import { berichtAdresse, berichtErstellen, berichtVorschau } from "../../daten/anwendung/berichte.svelte";
  import { berichtText, berichtVorlesen, liest, vorlesen, vorlesenDa } from "../../daten/anwendung/vorlesen.svelte";
  import { ICH } from "../../daten/ich";
  import { monatText, spanne, wann, wocheText } from "../../daten/format";
  import { konto, mitKonto, stand } from "../../daten/stand.svelte";
  import { uhr } from "../../daten/uhr.svelte";
  import Person from "../../board/Person.svelte";
  import type { BerichtArt, BerichtAuswahl, BerichtFormat, BerichtVorschau } from "../../modell";
  import { fassungAm } from "../../regeln/arbeitszeit";
  import { monatsende, montagVon, plusMonate, plusTage } from "../../regeln/tage";
  import DatumFeld from "../../teile/DatumFeld.svelte";

  const ARTNAMEN: Record<BerichtArt, string> = {
    stundennachweis: "Stundennachweis je Person",
    board: "Zeiten je Board und Karte",
    erledigt: "Erledigte Karten",
  };
  const ARTEN_WAHL: [BerichtArt, string, string][] = [
    ["stundennachweis", "fa-user-clock", "Soll, Ist und Differenz je Tag aus dem Zeitkonto, mit Karten und Abwesenheiten"],
    ["board", "fa-table-list", "Gebuchte Zeit je Karte eines Boards, mit Personen und Schätzung"],
    ["erledigt", "fa-circle-check", "Karten, die im Zeitraum erledigt wurden, mit Zuständigen und Zeit"],
  ];
  const FORMATE: [BerichtFormat, string, string][] = [["pdf", "PDF", "fa-file-pdf"], ["tabelle", "Tabelle", "fa-file-csv"], ["markdown", "Markdown", "fa-file-code"]];
  const SYMBOL: Record<BerichtFormat, string> = { pdf: "fa-file-pdf", tabelle: "fa-file-csv", markdown: "fa-file-code" };
  const ZAHLEN = ["Soll", "Ist", "Differenz", "Zeit", "Schätzung"];
  /** Spaltenbreite je Art der Spalte, damit alle Abschnitte gleich gebaut sind (wie in der Datei) */
  function breite(spalte: string): string {
    if (ZAHLEN.includes(spalte)) return "zahl";
    if (["Tag", "Schlüssel", "Erledigt", "Zuständig", "Personen"].includes(spalte)) return "kurz";
    return "frei";
  }

  let rechts = $state<"liste" | "vorschau">("liste");
  let art = $state<BerichtArt>("stundennachweis");
  let zeitraum = $state("vorwoche");
  let eigenVon = $state(uhr.heute.slice(0, 8) + "01");
  let eigenBis = $state(uhr.heute);
  let personen = $state<string[]>([ICH]);
  let boards = $state<string[]>([]);
  let format = $state<BerichtFormat>("pdf");
  let suche = $state("");
  /** der eben erstellte Bericht, hervorgehoben in der Liste */
  let neu = $state("");
  let vorschau = $state<BerichtVorschau | null>(null);
  let unterwegs = $state(false);

  const ZEITRAEUME = $derived.by(() => {
    const heute = uhr.heute, montag = montagVon(heute), anfang = heute.slice(0, 8) + "01", vormonat = plusMonate(anfang, -1);
    return {
      woche: { name: "Diese Woche", von: montag, bis: plusTage(montag, 6) },
      vorwoche: { name: "Letzte Woche", von: plusTage(montag, -7), bis: plusTage(montag, -1) },
      monat: { name: "Dieser Monat", von: anfang, bis: monatsende(anfang) },
      vormonat: { name: "Letzter Monat", von: vormonat, bis: monatsende(vormonat) },
      jahr: { name: "Dieses Jahr", von: `${heute.slice(0, 4)}-01-01`, bis: `${heute.slice(0, 4)}-12-31` },
    } as Record<string, { name: string; von: string; bis: string }>;
  });
  const bereich = $derived(zeitraum === "eigen" ? { von: eigenVon, bis: eigenBis } : ZEITRAEUME[zeitraum]);
  const zeitraumText = $derived(zeitraum === "woche" || zeitraum === "vorwoche" ? wocheText(bereich.von)
    : zeitraum === "monat" || zeitraum === "vormonat" ? monatText(bereich.von) : spanne(bereich.von, bereich.bis));

  /** Boards, in denen das Modul Berichte an ist und deine Rolle Berichte erstellen darf */
  const moeglicheBoards = $derived(stand.boards.filter((b) => darf(b, "berichte.erstellen")));
  /** Wer im Bericht vorkommen kann: im Stundennachweis du und, wessen Abwesenheiten du siehst, mit Zeitkonto; sonst die
   *  Mitglieder der gewählten Boards (Zeiten anderer zählt der Server nur mit dem Recht) */
  const erlaubt = $derived.by(() => {
    if (art !== "stundennachweis") return [...new Set(stand.boards.filter((b) => boards.includes(b.id)).flatMap((b) => mitKonto(b).map((m) => m.konto)))];
    const wer = new Set([ICH]);
    for (const b of stand.boards) if (darf(b, "abwesenheit.sehen")) for (const m of mitKonto(b)) wer.add(m.konto);
    return [...wer].filter((p) => !!fassungAm(stand.zeitkonten, p, uhr.heute));
  });
  const vorschlaege = $derived(erlaubt.filter((p) => !personen.includes(p) && konto(p).name.toLowerCase().includes(suche.trim().toLowerCase())).slice(0, 6));
  const auswahl = $derived<BerichtAuswahl>({ art, von: bereich.von, bis: bereich.bis, boards: art === "stundennachweis" ? [] : boards,
                                              personen: personen.filter((p) => erlaubt.includes(p)), format });
  const bereit = $derived((art !== "stundennachweis" || auswahl.personen.length > 0) && (art === "stundennachweis" || boards.length > 0)
    && bereich.von <= bereich.bis);

  // die Vorschau folgt der Auswahl, solange sie offen ist (kurz verzögert, damit Tippen nicht jedes Mal fragt)
  $effect(() => {
    const a = $state.snapshot(auswahl) as BerichtAuswahl;
    if (rechts !== "vorschau" || !bereit) return;
    const zeit = setTimeout(async () => { vorschau = await berichtVorschau(a); }, 250);
    return () => clearTimeout(zeit);
  });

  function boardUmschalten(id: string): void {
    boards = boards.includes(id) ? boards.filter((x) => x !== id) : [...boards, id];
  }

  async function erstellen(): Promise<void> {
    if (!bereit || unterwegs) return;
    unterwegs = true;
    const b = await berichtErstellen($state.snapshot(auswahl) as BerichtAuswahl);
    unterwegs = false;
    if (!b) return;
    neu = b.id;
    rechts = "liste";
  }
</script>

<div class="rahmen-kopf">
  <div class="seitenkopf">
    <h1>Berichte</h1>
    <div class="unterzeile">Auswertungen aus deinem Zeitkonto und den Boards, abgelegt in der Kellerwolke im Ordner Berichte der Pinnwand.</div>
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
        <h2><span class="zaehler">2</span>Zeitraum <span class="schwach klein pw-berichte-gewaehlt">{zeitraumText}</span></h2>
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
        <p class="schwach klein">{art === "stundennachweis"
          ? "Andere Personen mit Zeitkonto, deren Abwesenheiten du in einem gemeinsamen Board sehen darfst."
          : "Ohne das Recht \"Zeiten anderer sehen\" zählt im Board nur deine eigene Zeit."}</p>
      </section>

      <section class="bereich">
        <h2><span class="zaehler">5</span>Format</h2>
        <div class="stufen" role="group" aria-label="Format">
          {#each FORMATE as [id, name, symbol] (id)}<button class:an={format === id} onclick={() => (format = id)}><i class="fa-solid {symbol}"></i> {name}</button>{/each}
        </div>
      </section>

      <div class="pw-berichte-knoepfe">
        <button class="knopf" class:aktiv={rechts === "vorschau"} disabled={!bereit} onclick={() => (rechts = "vorschau")}><i class="fa-solid fa-eye"></i>Vorschau</button>
        <button class="knopf haupt" disabled={!bereit || unterwegs} onclick={erstellen}><i class="fa-solid fa-file-export"></i>Erstellen und ablegen</button>
      </div>
    </div>

    <div class="rollfeld pw-berichte-rechts">
      {#if rechts === "vorschau"}
        <div class="pw-berichte-vorschaukopf">
          <span class="etikett">Vorschau</span><span class="pw-schluessel">{vorschau?.datei ?? ""}</span>
          {#if vorschau && vorlesenDa()}
            <button class="knopf klein" aria-pressed={liest("berichtvorschau")} onclick={() => vorschau && vorlesen("berichtvorschau", berichtText(vorschau.titel, vorschau.inhalt))}>
              <i class="fa-solid {liest('berichtvorschau') ? 'fa-stop' : 'fa-volume-high'}"></i>{liest("berichtvorschau") ? "Stopp" : "Vorlesen"}</button>
          {/if}
          <button class="knopf klein rechts" onclick={() => (rechts = "liste")}><i class="fa-solid fa-list-ul"></i>Erstellte Berichte</button>
        </div>
        {#if !vorschau}
          <p class="schwach">Die Vorschau wird gerechnet.</p>
        {:else if vorschau.text !== undefined && vorschau.text !== null}
          <pre class="pw-berichte-text">{vorschau.text}</pre>
        {:else}
          <article class="pw-berichte-blatt" class:tabelle-format={format === "tabelle"}>
            {#if format === "pdf"}
              <header><span class="pw-marke-symbol"><i class="fa-solid fa-thumbtack"></i></span>
                <div><h2>{vorschau.titel}</h2><span class="schwach">{vorschau.inhalt.zeitraum}, erstellt von {konto(ICH).name}</span></div></header>
            {/if}
            {#each vorschau.inhalt.abschnitte as a, n (n)}
              <section>
                <h3>{a.titel}</h3>
                <div class="tabellen-raum">
                  <table class="tabelle">
                    <colgroup>{#each a.spalten as sp, i (i)}<col class="b-{breite(sp)}" />{/each}</colgroup>
                    <thead><tr>{#each a.spalten as s, i (i)}<th class:zahl={ZAHLEN.includes(s)}>{s}</th>{/each}</tr></thead>
                    <tbody>
                      {#each a.zeilen as z, r (r)}<tr>{#each z as w, i (i)}<td class:zahl={ZAHLEN.includes(a.spalten[i])}>{w}</td>{/each}</tr>{/each}
                      {#if !a.zeilen.length}<tr><td colspan={a.spalten.length} class="schwach">Im Zeitraum nichts gebucht.</td></tr>{/if}
                    </tbody>
                    {#if a.summe}<tfoot><tr>{#each a.summe as w, i (i)}<td class:zahl={ZAHLEN.includes(a.spalten[i])}>{w}</td>{/each}</tr></tfoot>{/if}
                  </table>
                </div>
                {#if a.fuss && format === "pdf"}<p class="schwach klein">{a.fuss}</p>{/if}
              </section>
            {/each}
          </article>
        {/if}
      {:else}
        <section class="bereich">
          <h2 class="pw-arbeitszeit-titel">Erstellte Berichte <span class="zaehler">{stand.berichte.length}</span></h2>
          <p class="schwach klein"><i class="fa-solid fa-cloud"></i> Kellerwolke, Ordner Berichte der Pinnwand</p>
          <div class="pw-berichte-liste">
            {#each stand.berichte as b (b.id)}
              <div class="pw-berichte-eintrag" class:neu={b.id === neu}>
                <i class="fa-solid {SYMBOL[b.format]} art"></i>
                <div class="was"><b>{b.titel}</b><span class="schwach klein">{b.zeitraum}, {wann(b.erstellt)}, {b.groesse}</span></div>
                <span class="knoepfe">
                  {#if b.format === "markdown" && vorlesenDa()}
                    <button class="knopf symbol klein" title={liest(`bericht-${b.id}`) ? "Vorlesen anhalten" : "Vorlesen"} aria-pressed={liest(`bericht-${b.id}`)}
                            onclick={() => berichtVorlesen(b)}><i class="fa-solid {liest(`bericht-${b.id}`) ? 'fa-stop' : 'fa-volume-high'}"></i></button>
                  {/if}
                  <a class="knopf symbol klein" href={berichtAdresse(b)} download={b.datei} title="Herunterladen: {b.datei}"><i class="fa-solid fa-download"></i></a>
                </span>
              </div>
            {:else}
              <p class="schwach klein">Noch keine Berichte erstellt.</p>
            {/each}
          </div>
        </section>
      {/if}
    </div>
  </div>
</div>
