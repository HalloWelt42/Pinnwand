<script lang="ts">
  // Serien und Termine aller Boards, in denen du Mitglied bist (Modul Serien und Termine an): je Serie Rhythmus,
  // Uhrzeit, Dauer, nächster Tag, Teilnehmer, Board und Zielspalte, Zustand; die kommenden Termine mit der Zusage je
  // Person. Oben der Nachtrag deiner vorgebuchten Zeiten vergangener Tage, als Bereich auf der Seite. Neue Serien und
  // Termine legt an, wer in einem Board das Recht "Serien und Termine verwalten" hat.
  import { darf, nachtrag, serienUmfeld } from "../../daten/abfragen";
  import { terminAnlegen, zusagen } from "../../daten/anwendung/termine.svelte";
  import { datum, dauer } from "../../daten/format";
  import { ICH } from "../../daten/ich";
  import { konto, stand } from "../../daten/stand.svelte";
  import { uhr } from "../../daten/uhr.svelte";
  import Person from "../../board/Person.svelte";
  import type { Kennung } from "../../modell";
  import { istPausiert, naechstes } from "../../regeln/serien";
  import DatumFeld from "../../teile/DatumFeld.svelte";
  import { rhythmusText } from "./anzeige";
  import { boardsMitSerien, boardVon, terminStand } from "./lesen";
  import Nachtrag from "./Nachtrag.svelte";
  import Teilnehmer from "./Teilnehmer.svelte";

  let boardFilter = $state("");
  let nurMeine = $state(false);
  let nachtragOffen = $state(false);

  const heute = $derived(uhr.heute);
  const boards = $derived(boardsMitSerien());
  /** Boards, in denen du Serien und Termine anlegen darfst */
  const verwaltbar = $derived(boards.filter((b) => darf(b, "serien.verwalten")));
  function sichtbar(boardId: Kennung, teilnehmer: Kennung[]): boolean {
    return boards.some((b) => b.id === boardId) && (!boardFilter || boardFilter === boardId) && (!nurMeine || teilnehmer.includes(ICH));
  }
  const serien = $derived.by(() => {
    const u = serienUmfeld();
    return stand.serien.filter((s) => sichtbar(s.board, s.teilnehmer))
      .map((s) => ({ s, naechster: naechstes(s, u), pausiert: istPausiert(s, heute) }))
      .sort((a, b) => (a.naechster?.tag ?? "9999").localeCompare(b.naechster?.tag ?? "9999") || (a.s.uhrzeit ?? "").localeCompare(b.s.uhrzeit ?? ""));
  });
  const termine = $derived(stand.termine.filter((t) => t.datum >= heute && sichtbar(t.board, t.teilnehmer))
    .sort((a, b) => (a.datum + a.von).localeCompare(b.datum + b.von)));
  const offen = $derived(nachtrag());

  // Termin an Ort und Stelle anlegen (ohne Karte); das Formular ist Stand der Ansicht, gespeichert wird über terminAnlegen
  let terminNeu = $state(false);
  let neu = $state({ titel: "", board: "", tag: "", von: "", bis: "", ort: "", teilnehmer: [ICH] as Kennung[] });
  let fehler = $state("");
  const neuBoard = $derived(boardVon(neu.board));
  const UHRZEIT = /^([01]?\d|2[0-3]):[0-5]\d$/;

  function boardWaehlen(id: Kennung): void {
    neu.board = id;
    neu.teilnehmer = neu.teilnehmer.filter((k) => boardVon(id)?.mitglieder.some((m) => m.konto === k));
  }

  /** Formular auf- und zuklappen; geöffnet steht es auf einem Board, in dem du Termine anlegen darfst */
  function terminUmschalten(): void {
    if (!terminNeu && !verwaltbar.some((b) => b.id === neu.board) && verwaltbar.length) boardWaehlen(verwaltbar[0].id);
    terminNeu = !terminNeu;
    fehler = "";
  }

  async function anlegen(): Promise<void> {
    if (!neu.titel.trim()) { fehler = "Titel fehlt"; return; }
    if (!neu.tag) { fehler = "Tag fehlt, etwa 05.11.2026"; return; }
    if (!UHRZEIT.test(neu.von) || !UHRZEIT.test(neu.bis)) { fehler = "Von und bis als Uhrzeit, etwa 09:00 bis 10:00"; return; }
    const von = neu.von.padStart(5, "0"), bis = neu.bis.padStart(5, "0");
    if (bis <= von) { fehler = "Das Ende liegt vor dem Beginn"; return; }
    if (!neu.teilnehmer.length) { fehler = "Mindestens eine Person nimmt teil"; return; }
    fehler = "";
    const id = await terminAnlegen({ board: neu.board, titel: neu.titel, datum: neu.tag, von, bis, ort: neu.ort, teilnehmer: [...neu.teilnehmer] });
    if (!id) return;
    neu = { titel: "", board: neu.board, tag: "", von: "", bis: "", ort: "", teilnehmer: [ICH] };
    terminNeu = false;
  }
</script>

<div class="rahmen-kopf">
  <div class="seitenkopf">
    <h1>Serien und Termine</h1>
    {#if verwaltbar.length}
      <div class="aktionen">
        <a class="knopf" class:haupt={!(nachtragOffen && offen.length)} href="/serien/neu" title="Wiederkehrende Karten mit vorgebuchter Zeit"><i class="fa-solid fa-plus"></i>Neue Serie</a>
      </div>
    {/if}
    <div class="unterzeile">Aus allen Boards, in denen du Mitglied bist. Eine Serie legt ihre Tage als Karten in die Zielspalte, ein Termin steht
      ohne Karte im Kalender. Deine Zeit zählt, sobald du sie am Folgetag bestätigst.</div>
  </div>
  <div class="filter" style="margin: 0">
    <button class="chip" class:aktiv={!boardFilter} onclick={() => (boardFilter = "")}>Alle Boards</button>
    {#each boards as b (b.id)}
      <button class="chip" class:aktiv={boardFilter === b.id} onclick={() => (boardFilter = b.id)}>
        <span class="pw-farbpunkt" data-farbe={b.farbe}></span>{b.name}</button>
    {/each}
    <span class="trenner"></span>
    <button class="chip" class:aktiv={nurMeine} onclick={() => (nurMeine = !nurMeine)} title="Nur Serien und Termine, an denen du teilnimmst">
      <i class="fa-solid fa-user"></i>Nur meine</button>
    <span class="rechts schwach klein" title="Boards ohne das Modul Serien und Termine erscheinen hier nicht">
      {boards.length} {boards.length === 1 ? "Board" : "Boards"} mit Serien und Terminen</span>
  </div>
</div>

<div class="rollfeld pw-serien">
  {#if offen.length}
    {#if nachtragOffen}
      <Nachtrag posten={offen} schliessen={() => (nachtragOffen = false)} />
    {:else}
      <div class="hinweis"><i class="fa-solid fa-clock-rotate-left"></i>
        <div><b>{offen.length} vorgebuchte {offen.length === 1 ? "Zeit wartet" : "Zeiten warten"} auf deine Bestätigung.</b>
          Bis dahin zählen sie nicht in deinem Zeitkonto.</div>
        <span class="rechts"><button class="knopf klein" onclick={() => (nachtragOffen = true)}>Jetzt bestätigen</button></span>
      </div>
    {/if}
  {/if}

  <section class="pw-serien-abschnitt">
    <h2>Serien <span class="zaehler">{serien.length}</span></h2>
    <div class="tabellen-raum">
      <table class="tabelle karten">
        <thead><tr><th>Serie</th><th>Rhythmus</th><th class="zahl">Uhrzeit</th><th class="zahl" title="Stunden:Minuten je Tag und Teilnehmer">Dauer</th>
          <th>Nächster Tag</th><th>Teilnehmer</th><th>Board und Zielspalte</th><th>Zustand</th></tr></thead>
        <tbody>
          {#each serien as { s, naechster, pausiert } (s.id)}
            {@const b = boardVon(s.board)!}
            {@const ziel = b.spalten.find((x) => x.id === s.zielspalte)}
            <tr>
              <td><a class="pw-serien-name" href="/serien/{s.id}" title={darf(b, "serien.verwalten") ? "Serie bearbeiten" : "Serie ansehen"}>
                <i class="fa-solid fa-repeat"></i>{s.titel}</a></td>
              <td data-titel="Rhythmus">{rhythmusText(s)}</td>
              <td data-titel="Uhrzeit" class="zahl"><span class="zahl">{s.uhrzeit ?? "ganztägig"}</span></td>
              <td data-titel="Dauer" class="zahl"><span class="zahl">{dauer(s.dauerMin * 60)}</span></td>
              <td data-titel="Nächster Tag">
                {#if pausiert}<span class="schwach" title="Pausiert seit {datum(s.pausiertSeit ?? heute, true)}">keiner</span>
                {:else if naechster}<span class="zahl">{datum(naechster.tag, true)}</span>
                  {#if naechster.ohne.length}<span class="schwach" title={naechster.ohne.map((o) => `${konto(o.konto).name}: ${o.grund}`).join(", ")}>
                    ohne {naechster.ohne.length} {naechster.ohne.length === 1 ? "Person" : "Personen"}</span>{/if}
                {:else}<span class="schwach">keiner</span>{/if}
              </td>
              <td data-titel="Teilnehmer"><span class="pw-personen">{#each s.teilnehmer as k (k)}<Person id={k} />{/each}</span></td>
              <td data-titel="Board und Zielspalte"><span class="pw-serien-ort">
                <span class="paar"><span class="pw-farbpunkt" data-farbe={b.farbe}></span>{b.name}</span>
                <span class="paar"><i class="fa-solid fa-arrow-right schwach"></i><span class="pw-farbpunkt" data-farbe={ziel?.farbe}></span>{ziel?.name ?? "erste Spalte"}</span></span></td>
              <td data-titel="Zustand">
                {#if pausiert}<span class="zustand pausiert" title="Keine neuen Vorbuchungen; unberührte Zukunftskarten sind zurückgenommen"><i class="fa-solid fa-circle-pause"></i>pausiert</span>
                {:else}<span class="zustand fertig" title="Bucht {s.vorlaufTage} Tage im Voraus vor"><i class="fa-solid fa-circle-play"></i>aktiv</span>{/if}
              </td>
            </tr>
          {:else}
            <tr><td colspan="8" class="schwach">Keine Serien in dieser Auswahl.</td></tr>
          {/each}
        </tbody>
      </table>
    </div>
  </section>

  <section class="pw-serien-abschnitt">
    <h2>Kommende Termine <span class="zaehler">{termine.length}</span>
      {#if verwaltbar.length}
        <span class="rechts"><button class="knopf ohne klein" onclick={terminUmschalten} title="Einmaliger Termin mit Teilnehmern, ohne Karte"><i class="fa-solid fa-calendar-plus"></i>Termin anlegen</button></span>
      {/if}</h2>
    {#if terminNeu && verwaltbar.length}
      <div class="bereich pw-serien-terminneu">
        <div class="pw-felder">
          <span class="name"><i class="fa-solid fa-heading"></i>Titel</span>
          <span class="wert"><input class="eingabe" bind:value={neu.titel} placeholder="Worum geht es" /></span>
          <span class="name"><i class="fa-solid fa-table-columns"></i>Board</span>
          <span class="wert"><span class="stufen">{#each verwaltbar as b (b.id)}
            <button class:an={neu.board === b.id} onclick={() => boardWaehlen(b.id)}>{b.name}</button>{/each}</span></span>
          <span class="name"><i class="fa-regular fa-calendar"></i>Wann</span>
          <span class="wert pw-serien-wannfelder">
            <DatumFeld tag={neu.tag} ontag={(t) => (neu.tag = t)} titel="Tag des Termins, etwa 05.11.2026" breite="150px" />
            <input class="eingabe zahl pw-serien-kurz" class:falsch={neu.von !== "" && !UHRZEIT.test(neu.von)} bind:value={neu.von} placeholder="09:00" title="Beginn als Uhrzeit" />
            <span class="schwach">bis</span>
            <input class="eingabe zahl pw-serien-kurz" class:falsch={neu.bis !== "" && !UHRZEIT.test(neu.bis)} bind:value={neu.bis} placeholder="10:00" title="Ende als Uhrzeit" />
          </span>
          <span class="name"><i class="fa-solid fa-location-dot"></i>Ort</span>
          <span class="wert"><input class="eingabe" bind:value={neu.ort} placeholder="frei lassen, wenn egal" /></span>
          <span class="name"><i class="fa-solid fa-user-group"></i>Teilnehmer</span>
          <span class="wert">{#if neuBoard}<Teilnehmer board={neuBoard} bind:konten={neu.teilnehmer} />{/if}</span>
        </div>
        <div class="pw-serien-knoepfe">
          <button class="knopf haupt klein" onclick={anlegen}><i class="fa-solid fa-check"></i>Anlegen</button>
          <button class="knopf ohne klein" onclick={terminUmschalten}>Abbrechen</button>
          {#if fehler}<span class="pw-serien-fehler"><i class="fa-solid fa-triangle-exclamation"></i>{fehler}</span>
          {:else if neu.teilnehmer.includes(ICH)}<span class="schwach klein">Du bist zugesagt; die anderen sagen selbst zu und bekommen einen Hinweis.</span>
          {:else}<span class="schwach klein">Die Teilnehmer sagen selbst zu und bekommen einen Hinweis.</span>{/if}
        </div>
      </div>
    {/if}
    <div class="tabellen-raum">
      <table class="tabelle karten">
        <thead><tr><th>Wann</th><th>Termin</th><th>Board</th><th>Teilnehmer</th><th>Du</th></tr></thead>
        <tbody>
          {#each termine as t (t.id)}
            {@const b = boardVon(t.board)!}
            {@const zu = t.teilnehmer.filter((k) => terminStand(t, k).klasse === "gut").length}
            <tr>
              <td><span class="zahl pw-serien-wann">{datum(t.datum, true)} {t.von} bis {t.bis}</span></td>
              <td data-titel="Termin"><span class="pw-serien-termin"><b>{t.titel}</b>
                {#if t.ort}<span class="schwach"><i class="fa-solid fa-location-dot"></i>{t.ort}</span>{/if}</span></td>
              <td data-titel="Board"><span class="pw-serien-ort"><span class="pw-farbpunkt" data-farbe={b.farbe}></span>{b.name}</span></td>
              <td data-titel="Teilnehmer">
                <span class="pw-serien-teilnehmer">
                  {#each t.teilnehmer as k (k)}
                    {@const st = terminStand(t, k)}
                    <span class="pw-serien-person {st.klasse}" title="{konto(k).name}: {st.text}"><Person id={k} /><i class="fa-solid {st.symbol}"></i></span>
                  {/each}
                  <span class="schwach klein">{zu} von {t.teilnehmer.length} zugesagt</span>
                </span>
              </td>
              <td data-titel="Du">
                {#if !t.teilnehmer.includes(ICH)}<span class="schwach">nicht dabei</span>
                {:else if t.zugesagt.includes(ICH)}<span class="pw-serien-du"><span class="zustand fertig"><i class="fa-solid fa-circle-check"></i>zugesagt</span>
                  <button class="knopf ohne klein" onclick={() => zusagen(t.id, false)} title="Zusage zurücknehmen">Absagen</button></span>
                {:else}<button class="knopf klein" onclick={() => zusagen(t.id)} title="Teilnahme zusagen; die Zeit zählt nach dem Termin, wenn du sie bestätigst">Zusagen</button>{/if}
              </td>
            </tr>
          {:else}
            <tr><td colspan="5" class="schwach">Keine kommenden Termine in dieser Auswahl.</td></tr>
          {/each}
        </tbody>
      </table>
    </div>
  </section>
</div>
