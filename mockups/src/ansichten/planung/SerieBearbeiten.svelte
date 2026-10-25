<script lang="ts">
  // Eine Serie anlegen oder bearbeiten: links tun (Karte, Rhythmus, Teilnehmer, Vorbuchen), rechts das Ergebnis (die
  // Tage der Serie mit ihrem Stand). Das Formular ist Stand der Ansicht; gespeichert wird über die Anwendungsfälle.
  // Ändern zieht nur unberührte Vorbuchungen nach; angefasste Karten, vergangene und bewusst gelöschte Tage bleiben
  // (M-108, M-109). Pause nimmt unberührte Zukunftskarten zurück, Löschen löst Karten mit Zeit von der Serie (M-110).
  // Rückfragen stehen in der Fläche, jede Änderung meldet sich unten mit Rückgängig.
  import { untrack } from "svelte";
  import { darf as darfIm } from "../../beispiel/abfragen";
  import { serienUmfeld } from "../../beispiel/abfragen";
  import { fortsetzen, pausieren, serieAendern, serieAnlegen, serieLoeschen, tagAuslassen } from "../../beispiel/anwendung/serien.svelte";
  import { HEUTE, ICH } from "../../beispiel/daten";
  import { datum, dauer } from "../../beispiel/format";
  import { karte, konto, stand } from "../../beispiel/stand.svelte";
  import Person from "../../board/Person.svelte";
  import type { Kennung, Monatsregel, Rhythmus, Serie } from "../../modell";
  import { istPausiert, naechstes, vorkommenListe, vorlaufEnde, type Vorkommen } from "../../regeln/serien";
  import { kalenderwoche, montagVon, plusTage, TAGE_KURZ, TAGE_LANG, WOCHE_AB_MONTAG } from "../../regeln/tage";
  import DatumFeld from "../../teile/DatumFeld.svelte";
  import DauerFeld from "../../teile/DauerFeld.svelte";
  import { gehe } from "../../weg.svelte";
  import { rhythmusText, STAND } from "./anzeige";
  import { boardsMitSerien, boardVon, kartenPfad } from "./lesen";
  import Teilnehmer from "./Teilnehmer.svelte";

  let { serieId = "", neu = false, entwurf = "" }: { serieId?: string; neu?: boolean; entwurf?: string } = $props();

  const original = $derived(neu ? undefined : stand.serien.find((x) => x.id === serieId));

  /** Vorschlag einer neuen Serie (in der App: du als Teilnehmer und die erste offene Spalte) */
  function neueSerie(): Serie {
    return { id: "neu", board: "b-prod", titel: "Wochenplanung Werkstatt", beschreibung: "Aufträge der nächsten Woche, Maschinenbelegung, Material.",
             labels: ["l-intern"], rhythmus: "woechentlich", tage: [4], uhrzeit: "15:00", dauerMin: 30, zielspalte: "s-geplant",
             teilnehmer: [ICH, "k-jonas"], ab: HEUTE, vorlaufTage: 14, wochenendenUeberspringen: false, feiertageUeberspringen: true,
             auslass: [], beruehrt: [], verworfen: [] };
  }

  /** Formular: die änderbaren Felder; Pause, Auslass und angefasste Tage kommen immer aus dem Zustand */
  let s = $state<Serie>(neueSerie());
  let loeschenFrage = $state(false);

  function laden(): void {
    s = original ? $state.snapshot(original) as Serie : neueSerie();
    if (entwurf === "aendern") { s.uhrzeit = "07:45"; s.dauerMin = 20; }
    loeschenFrage = entwurf === "loeschen";
  }
  // neu laden, wenn Serie oder Entwurf wechseln; was laden() selbst liest und schreibt, zählt nicht als Abhängigkeit
  $effect(() => { void serieId; void neu; void entwurf; untrack(laden); });

  /** Vorschau mit dem Formular und dem Stand der Serie (Pause, Auslass, angefasste und verworfene Tage) */
  const vorschau = $derived<Serie>(original
    ? { ...s, pausiertSeit: original.pausiertSeit, fortgesetzt: original.fortgesetzt, auslass: original.auslass, beruehrt: original.beruehrt,
        verworfen: original.verworfen }
    : s);
  const b = $derived(boardVon(s.board));
  const darf = $derived(!!b && darfIm(b, "serien.verwalten"));
  const pausiert = $derived(istPausiert(vorschau, HEUTE));
  const umfeld = $derived(serienUmfeld());
  const liste = $derived(vorkommenListe(vorschau, umfeld));
  const naechster = $derived(naechstes(vorschau, umfeld));
  const spalten = $derived(b?.spalten.filter((x) => !x.erledigt) ?? []);
  const UHRZEIT = /^([01]?\d|2[0-3]):[0-5]\d$/;
  const uhrzeitFalsch = $derived(!!s.uhrzeit && !UHRZEIT.test(s.uhrzeit));

  /** Die änderbaren Felder des Formulars (ohne Kennung, Board und den Stand aus Pause, Auslass und Nachtrag) */
  function felder(x: Serie): Partial<Serie> {
    const { id: _i, board: _b, pausiertSeit: _p, fortgesetzt: _f, auslass: _a, beruehrt: _r, verworfen: _v, ...rest } = $state.snapshot(x) as Serie;
    return { ...rest, uhrzeit: rest.uhrzeit?.trim() ? rest.uhrzeit.padStart(5, "0") : undefined };
  }

  /** Was sich gegenüber der gespeicherten Fassung geändert hat, als kurze Sätze */
  const aenderungen = $derived.by(() => {
    if (!original) return [] as string[];
    const o = original;
    const a: string[] = [];
    if (s.titel !== o.titel) a.push(`Titel "${s.titel}"`);
    if (s.rhythmus !== o.rhythmus || JSON.stringify(s.tage ?? []) !== JSON.stringify(o.tage ?? []) || s.monatsregel !== o.monatsregel
        || s.monatstag !== o.monatstag || s.wochenendenUeberspringen !== o.wochenendenUeberspringen) a.push(`Rhythmus ${rhythmusText(s)}`);
    if ((s.uhrzeit || "") !== (o.uhrzeit || "")) a.push(`Uhrzeit ${s.uhrzeit || "ganztägig"} statt ${o.uhrzeit || "ganztägig"}`);
    if (s.dauerMin !== o.dauerMin) a.push(`Dauer ${dauer(s.dauerMin * 60)} statt ${dauer(o.dauerMin * 60)}`);
    if (s.zielspalte !== o.zielspalte) a.push(`Zielspalte ${spalten.find((x) => x.id === s.zielspalte)?.name}`);
    if (JSON.stringify(s.teilnehmer) !== JSON.stringify(o.teilnehmer)) a.push(`Teilnehmer ${s.teilnehmer.map((k) => konto(k).name).join(", ")}`);
    if (s.vorlaufTage !== o.vorlaufTage) a.push(`Vorlauf ${s.vorlaufTage} Tage`);
    if (s.feiertageUeberspringen !== o.feiertageUeberspringen) a.push(s.feiertageUeberspringen ? "Feiertage auslassen" : "Feiertage nicht auslassen");
    if (s.ab !== o.ab || s.bis !== o.bis) a.push("Zeitraum");
    if ((s.beschreibung ?? "") !== (o.beschreibung ?? "")) a.push("Beschreibung");
    return a;
  });
  const geaendert = $derived(aenderungen.length > 0);
  const zaehle = (st: Vorkommen["stand"]): number => liste.filter((v) => v.stand === st && v.tag > HEUTE).length;

  function anzeige(v: Vorkommen): { text: string; symbol: string; klasse: string; erklaerung: string } {
    if (neu && (v.stand === "vorgebucht" || v.stand === "heute")) {
      return { text: "wird vorgebucht", symbol: "fa-thumbtack", klasse: "wartet", erklaerung: "Anlegen legt für diesen Tag eine Karte in die Zielspalte" };
    }
    if (geaendert && v.stand === "vorgebucht") {
      return { text: "wird angepasst", symbol: "fa-arrows-rotate", klasse: "wartet", erklaerung: "Unberührte Vorbuchung: Speichern passt die Karte an" };
    }
    return STAND[v.stand];
  }
  /** Uhrzeit eines Tages: unberührte und künftige folgen dem Formular, alle anderen bleiben bei der gespeicherten */
  function uhrzeitAm(v: Vorkommen): string {
    const folgt = neu || ["vorgebucht", "geplant"].includes(v.stand);
    return (folgt ? s.uhrzeit : original?.uhrzeit) || "ganztägig";
  }
  function geloeschtText(tag: string): string {
    const a = vorschau.auslass.find((x) => x.tag === tag);
    return a ? `gelöscht von ${konto(a.von).name} am ${datum(a.am)}` : "";
  }

  const wochen = $derived.by(() => {
    const g: { kw: number; von: string; tage: Vorkommen[] }[] = [];
    for (const v of liste) {
      const kw = kalenderwoche(v.tag);
      if (g[g.length - 1]?.kw !== kw) g.push({ kw, von: montagVon(v.tag), tage: [] });
      g[g.length - 1].tage.push(v);
    }
    return g;
  });

  const RHYTHMEN: [Rhythmus, string][] = [["taeglich", "Täglich"], ["werktags", "Werktags"], ["woechentlich", "Wöchentlich"], ["monatlich", "Monatlich"]];
  const MONATSREGELN: [Monatsregel, string][] = [["tag", "am Tag"], ["erster-werktag", "erster Werktag"], ["letzter-werktag", "letzter Werktag"]];

  function tagUmschalten(t: number): void {
    const tage = s.tage ?? [];
    s.tage = tage.includes(t) ? tage.filter((x) => x !== t) : [...tage, t];
  }
  function boardWaehlen(id: Kennung): void {
    s.board = id;
    const nb = boardVon(id);
    s.zielspalte = nb?.spalten.find((x) => !x.erledigt)?.id ?? "";
    s.teilnehmer = s.teilnehmer.filter((k) => nb?.mitglieder.some((m) => m.konto === k));
    s.labels = [];
  }

  /** Pfad innerhalb dieses Bereichs; ein vorgeführter Zustand bleibt, damit die eben gemachte Änderung sichtbar bleibt */
  function hin(pfad: string): void {
    gehe(entwurf ? `${pfad}?entwurf=${entwurf}` : pfad);
  }

  function speichern(): void {
    if (uhrzeitFalsch) return;
    if (neu) {
      const id = serieAnlegen({ ...(felder(s) as Omit<Serie, "id">), board: s.board, auslass: [], beruehrt: [], verworfen: [] });
      if (id) hin(`/serien/${id}`);
      return;
    }
    if (!original) return;
    serieAendern(original.id, felder(s));
    laden();
  }

  /** erst zurück zur Übersicht, dann löschen: so steht die Ansicht nie auf einer Serie, die es nicht mehr gibt */
  function loeschen(): void {
    if (!original) return;
    const id = original.id;
    hin("/serien");
    serieLoeschen(id);
  }
</script>

{#if !neu && !original}
<div class="rahmen-kopf">
  <div class="seitenkopf"><h1>Serie nicht gefunden</h1></div>
</div>
<div class="rollfeld">
  <div class="leer"><i class="fa-solid fa-repeat"></i><h2>Diese Serie gibt es nicht mehr</h2>
    <p>Sie wurde gelöscht; solange die Meldung steht, holt Rückgängig sie zurück.</p>
    <a class="knopf" href="/serien"><i class="fa-solid fa-chevron-left"></i>Serien und Termine</a></div>
</div>
{:else}
<div class="rahmen-kopf">
  <div class="seitenkopf">
    <h1><i class="fa-solid fa-repeat pw-serien-kopfsymbol"></i>{neu ? "Neue Serie" : original?.titel}</h1>
    {#if !neu}
      {#if pausiert}<span class="zustand pausiert"><i class="fa-solid fa-circle-pause"></i>pausiert seit {datum(vorschau.pausiertSeit ?? HEUTE, true)}</span>
      {:else}<span class="zustand fertig"><i class="fa-solid fa-circle-play"></i>aktiv</span>{/if}
    {/if}
    <div class="aktionen">
      {#if neu}
        <a class="knopf ohne" href="/serien">Abbrechen</a>
        <button class="knopf haupt" onclick={speichern} disabled={!s.titel.trim() || !s.teilnehmer.length || uhrzeitFalsch}
                title="Legt die Serie an und bucht die Tage im Vorlauf als Karten vor"><i class="fa-solid fa-check"></i>Anlegen und vorbuchen</button>
      {:else if darf}
        <button class="knopf" onclick={() => (pausiert ? fortsetzen(original!.id) : pausieren(original!.id))}
                title={pausiert ? "Ab heute wieder vorbuchen" : "Keine neuen Vorbuchungen; unberührte Zukunftskarten werden zurückgenommen"}>
          <i class="fa-solid {pausiert ? 'fa-play' : 'fa-pause'}"></i>{pausiert ? "Fortsetzen" : "Pausieren"}</button>
        <button class="knopf ohne gefahr" onclick={() => (loeschenFrage = true)}><i class="fa-solid fa-trash-can"></i>Löschen</button>
      {/if}
    </div>
    <div class="unterzeile"><a class="pw-serien-zurueck" href="/serien"><i class="fa-solid fa-chevron-left"></i> Serien und Termine</a>
      {#if b}<span class="schwach"> · {b.name} · {rhythmusText(s)}{s.uhrzeit ? ` um ${s.uhrzeit}` : ""}</span>{/if}</div>
  </div>

  {#if loeschenFrage && original}
    <div class="hinweis gefahr"><i class="fa-solid fa-trash-can"></i>
      <div><b>Serie "{original.titel}" löschen?</b> {zaehle("vorgebucht")} unberührte Vorbuchungen werden zurückgenommen.
        {#if zaehle("beruehrt")}{zaehle("beruehrt")} angefasste {zaehle("beruehrt") === 1 ? "Karte bleibt" : "Karten bleiben"} stehen.{/if}
        Karten mit erfasster Zeit und erledigte bleiben als Verlauf und werden von der Serie gelöst; bestätigte Zeiten zählen weiter.</div>
      <span class="rechts"><button class="knopf klein" onclick={() => (loeschenFrage = false)}>Behalten</button>
        <button class="knopf gefahr-voll klein" onclick={loeschen}><i class="fa-solid fa-trash-can"></i>Löschen</button></span>
    </div>
  {:else if geaendert && darf}
    <div class="hinweis"><i class="fa-solid fa-arrows-rotate"></i>
      <div><b>Nicht gespeichert: {aenderungen.join(", ")}.</b> Speichern passt {zaehle("vorgebucht")} unberührte Vorbuchungen an;
        {zaehle("beruehrt") === 0 ? "" : zaehle("beruehrt") === 1 ? "die angefasste Karte, " : "angefasste Karten, "}vergangene und gelöschte Tage bleiben, wie sie sind.</div>
      <span class="rechts"><button class="knopf klein" onclick={laden}>Verwerfen</button>
        <button class="knopf haupt klein" onclick={speichern} disabled={uhrzeitFalsch}><i class="fa-solid fa-check"></i>Speichern</button></span>
    </div>
  {:else if pausiert}
    <div class="hinweis warnung"><i class="fa-solid fa-circle-pause"></i>
      <div>Pausiert: es entstehen keine neuen Karten, unberührte Zukunftskarten sind zurückgenommen, angefasste bleiben. Fortsetzen bucht
        ab heute wieder vor; gelöschte Tage bleiben gelöscht.</div></div>
  {/if}
</div>

<div class="spalten pw-serien-spalten">
  <div class="rollfeld pw-serien-formular">
    {#if !darf && b}
      <div class="hinweis"><i class="fa-solid fa-lock"></i><div>Nur ansehen: dir fehlt im Board {b.name} das Recht "Serien und Termine verwalten".</div></div>
    {/if}
    <fieldset disabled={!darf}>
      <section class="bereich">
        <h2>Karte</h2>
        <div class="pw-felder">
          <span class="name"><i class="fa-solid fa-heading"></i>Titel</span>
          <span class="wert"><input class="eingabe" bind:value={s.titel} placeholder="Titel jeder Karte; die Uhrzeit steht davor" /></span>
          <span class="name"><i class="fa-solid fa-table-columns"></i>Board</span>
          <span class="wert">
            {#if neu}
              <span class="stufen">{#each boardsMitSerien().filter((x) => darfIm(x, "serien.verwalten")) as x (x.id)}
                <button class:an={s.board === x.id} onclick={() => boardWaehlen(x.id)}>{x.name}</button>{/each}</span>
            {:else if b}
              <span class="pw-serien-ort" title="Das Board einer Serie steht nach dem Anlegen fest"><span class="pw-farbpunkt" data-farbe={b.farbe}></span>{b.name}</span>
            {/if}
          </span>
          <span class="name" title="Hier legt die Serie ihre Karten an"><i class="fa-solid fa-inbox"></i>Zielspalte</span>
          <span class="wert"><span class="stufen">{#each spalten as x (x.id)}
            <button class:an={s.zielspalte === x.id} onclick={() => (s.zielspalte = x.id)}><span class="pw-farbpunkt" data-farbe={x.farbe}></span>{x.name}</button>{/each}</span></span>
          <span class="name"><i class="fa-solid fa-tag"></i>Labels</span>
          <span class="wert">
            {#each s.labels as l (l)}{@const lab = b?.labels.find((x) => x.id === l)}{#if lab}<span class="pw-label" data-farbe={lab.farbe}>{lab.name}</span>{/if}{/each}
            <button class="knopf ohne symbol klein" title="Label wählen"><i class="fa-solid fa-plus"></i></button>
          </span>
        </div>
        <textarea class="eingabe" rows="2" bind:value={s.beschreibung} placeholder="Beschreibung jeder Karte (Markdown)"></textarea>
      </section>

      <section class="bereich">
        <h2>Rhythmus</h2>
        <div class="pw-felder">
          <span class="name"><i class="fa-solid fa-repeat"></i>Wie oft</span>
          <span class="wert"><span class="stufen">{#each RHYTHMEN as [w, n] (w)}<button class:an={s.rhythmus === w} onclick={() => (s.rhythmus = w)}>{n}</button>{/each}</span></span>
          {#if s.rhythmus === "woechentlich"}
            <span class="name"><i class="fa-solid fa-calendar-week"></i>An Tagen</span>
            <span class="wert"><span class="stufen">{#each WOCHE_AB_MONTAG as t (t)}
              <button class:an={(s.tage ?? []).includes(t)} title={TAGE_LANG[t]} onclick={() => tagUmschalten(t)}>{TAGE_KURZ[t]}</button>{/each}</span></span>
          {:else if s.rhythmus === "monatlich"}
            <span class="name"><i class="fa-solid fa-calendar-day"></i>Im Monat</span>
            <span class="wert">
              <span class="stufen">{#each MONATSREGELN as [w, n] (w)}<button class:an={(s.monatsregel ?? "tag") === w} onclick={() => (s.monatsregel = w)}>{n}</button>{/each}</span>
              {#if (s.monatsregel ?? "tag") === "tag"}
                <input class="eingabe zahl pw-serien-kurz" value={s.monatstag ?? Number(s.ab.slice(8, 10))} title="Tag im Monat; hat ein Monat weniger Tage, gilt sein letzter"
                       oninput={(e) => { const n = Number(e.currentTarget.value); if (n >= 1 && n <= 31) s.monatstag = n; }} />.
              {/if}
            </span>
          {:else if s.rhythmus === "taeglich"}
            <span class="name"><i class="fa-solid fa-calendar-week"></i>Wochenende</span>
            <span class="wert"><button class="schalter" class:an={s.wochenendenUeberspringen} aria-label="Samstag und Sonntag auslassen"
              onclick={() => (s.wochenendenUeberspringen = !s.wochenendenUeberspringen)}></button><span class="leise klein">Samstag und Sonntag auslassen</span></span>
          {/if}
          <span class="name"><i class="fa-regular fa-clock"></i>Uhrzeit</span>
          <span class="wert"><input class="eingabe zahl pw-serien-kurz" class:falsch={uhrzeitFalsch} bind:value={s.uhrzeit} placeholder="ganztägig"
                                    title={uhrzeitFalsch ? "Uhrzeit bitte wie 07:30" : "Steht vor dem Titel jeder Karte; leer: ganztägig"} />
            <span class="name-neben"><i class="fa-solid fa-hourglass-half"></i>Dauer</span>
            <span class="pw-serien-kurz"><DauerFeld sek={s.dauerMin * 60} onwert={(sek) => (s.dauerMin = Math.round(sek / 60))} klasse="feld" leerErlaubt={false}
                       titel="Stunden:Minuten; Schätzung jeder Karte und vorgebuchte Zeit je Teilnehmer" /></span></span>
          <span class="name"><i class="fa-regular fa-calendar"></i>Zeitraum</span>
          <span class="wert pw-serien-zeitraum"><DatumFeld tag={s.ab} ontag={(t) => { if (t) s.ab = t; }} titel="Erster möglicher Tag" breite="150px" />
            <span class="schwach">bis</span>
            <DatumFeld tag={s.bis ?? ""} ontag={(t) => (s.bis = t || undefined)} leerErlaubt titel="Letzter möglicher Tag; leer: ohne Ende" breite="150px" /></span>
        </div>
      </section>

      <section class="bereich">
        <h2>Teilnehmer</h2>
        {#if b}<Teilnehmer board={b} bind:konten={s.teilnehmer} />{/if}
        <p class="leise klein">Jeder Teilnehmer bekommt die Zeit vorgebucht und bestätigt sie am Folgetag selbst. Wer an einem Tag fehlt
          (Urlaub, Abwesenheit, Feiertag seines Bundeslands), bekommt nichts vorgebucht; fehlen alle, entfällt der Tag.</p>
      </section>

      <section class="bereich">
        <h2>Vorbuchen</h2>
        <div class="einstellung">
          <div><div class="name">Vorlauf</div><div class="erklaerung">So viele Tage im Voraus liegen die Karten in der Zielspalte; 0: nur heute</div></div>
          <div class="wert"><input class="eingabe" value={s.vorlaufTage}
            oninput={(e) => { const n = Number(e.currentTarget.value); if (Number.isInteger(n) && n >= 0 && n <= 90) s.vorlaufTage = n; }} /><span class="einheit">Tage</span></div>
        </div>
        <div class="einstellung">
          <div><div class="name">Feiertage auslassen</div><div class="erklaerung">Nach dem Bundesland jedes Teilnehmers aus seinem Zeitkonto</div></div>
          <div class="wert"><button class="schalter" class:an={s.feiertageUeberspringen} aria-label="Feiertage auslassen"
            onclick={() => (s.feiertageUeberspringen = !s.feiertageUeberspringen)}></button></div>
        </div>
      </section>
    </fieldset>
  </div>

  <div class="rollfeld pw-serien-tage">
    <div class="pw-serien-tage-kopf">
      <h2>{neu ? "So bucht die Serie vor" : "Tage der Serie"}</h2>
      <p class="leise klein">
        {#if pausiert}Pausiert: keine Vorbuchungen.
        {:else}Karten liegen bis {datum(vorlaufEnde(s, HEUTE), true)} in {spalten.find((x) => x.id === s.zielspalte)?.name ?? "der ersten Spalte"};
          {#if naechster}nächster Tag {datum(naechster.tag, true)}{:else}kein weiterer Tag{/if}{/if}</p>
    </div>
    {#each wochen as w (w.von)}
      <div class="etikett">Woche {w.kw} <span class="zahl">{datum(w.von)} bis {datum(plusTage(w.von, 6))}</span></div>
      <div class="pw-serien-tagliste">
        {#each w.tage as v (v.tag)}
          {@const a = anzeige(v)}
          {@const k = v.karte ? karte(v.karte) : undefined}
          {@const notiz = v.stand === "geloescht" ? geloeschtText(v.tag) : v.notiz}
          <div class="pw-serien-tagzeile {v.stand}" class:heute={v.tag === HEUTE}>
            <span class="wann"><b class="zahl">{datum(v.tag, true)}</b><span class="zahl">{uhrzeitAm(v)}</span></span>
            <span class="kopfzeile">
              <span class="zustand {a.klasse}" title={a.erklaerung}><i class="fa-solid {a.symbol}"></i>{a.text}</span>
              {#if k && b}<a class="pw-schluessel" href={kartenPfad(b, k)} title="Karte des Tags öffnen">{k.schluessel}</a>{/if}
              {#if !neu && darf && original && v.tag > HEUTE && ["vorgebucht", "geplant", "beruehrt"].includes(v.stand)}
                <button class="knopf ohne symbol klein auslassen" onclick={() => tagAuslassen(original!.id, v.tag)}
                        title="Diesen Tag auslassen: er wird gemerkt und kommt nicht wieder"><i class="fa-solid fa-calendar-xmark"></i></button>
              {/if}
            </span>
            {#if v.stand === "wartet" || notiz || (v.ohne.length && v.stand !== "ausgelassen")}
            <span class="notiz">
              {#if v.stand === "wartet"}<span class="schwach">wartet auf</span>{#each v.offen as x (x)}<span class="pw-serien-mini" title={konto(x).name}><Person id={x} /></span>{/each}
              {:else if notiz}<span class="schwach">{notiz}</span>{/if}
              {#if v.ohne.length && v.stand !== "ausgelassen"}
                <span class="schwach">ohne</span>{#each v.ohne as o (o.konto)}<span class="pw-serien-mini" title="{konto(o.konto).name}: {o.grund}"><Person id={o.konto} /><span class="klein schwach">{o.grund}</span></span>{/each}
              {/if}
            </span>
            {/if}
          </div>
        {/each}
      </div>
    {:else}
      <div class="leer"><i class="fa-regular fa-calendar"></i><p>Kein Tag im Zeitraum; Rhythmus oder Tage wählen.</p></div>
    {/each}
  </div>
</div>
{/if}
