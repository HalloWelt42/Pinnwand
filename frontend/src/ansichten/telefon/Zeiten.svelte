<script lang="ts">
  // Zeit am Telefon: dein einer Timer groß mit Anhalten oder Fortsetzen und Stopp (gebucht wird beim Anhalten und Stoppen,
  // M-79), zuletzt genutzte Karten zum Starten (ein Start beendet deinen Timer auf einer anderen Karte und bucht ihn,
  // M-80), Zeit nachbuchen auf Karte, Tag und Dauer (M-86, Eingabe wie M-90) und der Stand von heute und der Woche gegen
  // das Soll aus deinem Zeitkonto, gerechnet wie im Kopf am Rechner.
  import { istAm, kartenNummer, sitzungSek, sollTag, timerErlaubt, timerVon, zeitDerKarte } from "../../daten/abfragen";
  import { anhalten, fortsetzen, starten, stoppen } from "../../daten/anwendung/timer.svelte";
  import { buchen as zeitBuchen } from "../../daten/anwendung/zeiten.svelte";
  import { datum, dauer, differenz, uhrzeit } from "../../daten/format";
  import { ICH } from "../../daten/ich";
  import { board, karte, stand } from "../../daten/stand.svelte";
  import { uhr } from "../../daten/uhr.svelte";
  import type { Karte } from "../../modell";
  import { montagVon, plusTage } from "../../regeln/tage";
  import DatumFeld from "../../teile/DatumFeld.svelte";
  import DauerFeld from "../../teile/DauerFeld.svelte";
  import { boardPfad, wert } from "../../weg.svelte";
  import TelefonSchale from "./TelefonSchale.svelte";
  import { telPfad } from "./weg";

  const heute = $derived(uhr.heute);
  const timer = $derived(timerVon(ICH));
  const timerKarte = $derived(timer ? karte(timer.karte) : undefined);
  const anteil = $derived(timerKarte?.schaetzungMin ? zeitDerKarte(timerKarte.id) / 60 / timerKarte.schaetzungMin : 0);

  /** zuletzt von dir gebucht (Tag), sonst leer */
  const zuletztGebucht = (k: Karte): string =>
    stand.zeiteintraege.filter((z) => z.konto === ICH && z.karte === k.id).map((z) => z.datum).sort().at(-1) ?? "";
  /** zuletzt genutzt: Karten mit deinen Buchungen oder in deiner Zuständigkeit, auf denen ein Timer laufen darf */
  const zuletzt = $derived(stand.karten.filter((k) => timerErlaubt(k) && k.id !== timerKarte?.id && (k.zustaendig.includes(ICH) || zuletztGebucht(k)))
    .sort((a, b) => zuletztGebucht(b).localeCompare(zuletztGebucht(a)) || b.bewegtAm.localeCompare(a.bewegtAm)).slice(0, 4));

  // Nachbuchen: Karte als Textfeld mit Vorschlägen (vorbelegt über ?karte= aus dem Kartendetail), Tag und Dauer über die
  // gemeinsamen Felder
  const vorbelegt = stand.karten.find((k) => k.schluessel.toLowerCase() === wert("karte").toLowerCase() && timerErlaubt(k));
  let kartenId = $state(vorbelegt?.id ?? "");
  let suche = $state(vorbelegt ? `${vorbelegt.schluessel} ${vorbelegt.titel}` : "");
  let tag = $state(uhr.heute);
  let sek = $state(0);
  let fehler = $state("");
  const vorschlaege = $derived(kartenId || !suche.trim() ? [] : stand.karten.filter((k) => timerErlaubt(k) &&
    `${k.schluessel} ${k.titel}`.toLowerCase().includes(suche.trim().toLowerCase())).slice(0, 4));

  function waehlen(k: Karte): void { kartenId = k.id; suche = `${k.schluessel} ${k.titel}`; fehler = ""; }
  /** Buchen; die Dauer leert sich erst, wenn der Server gebucht hat */
  async function buchenKlick(): Promise<void> {
    if (!kartenId) fehler = "Karte bitte aus den Vorschlägen wählen.";
    else if (tag > heute) fehler = "Zeit lässt sich nur bis heute buchen.";
    else if (sek <= 0) fehler = "Dauer bitte wie 1:30, 1,5 oder 90min eingeben.";
    else {
      fehler = "";
      if (await zeitBuchen(kartenId, tag, sek)) sek = 0;
    }
  }
  const TAG_CHIPS = $derived<[string, string][]>([["Heute", heute], ["Gestern", plusTage(heute, -1)]]);
  const DAUER_CHIPS = [15 * 60, 30 * 60, 3600, 2 * 3600];

  // Stand wie im Kopf am Rechner: Ist und Soll aus dem Zeitkonto, die Woche ab Montag
  const woche = $derived(Array.from({ length: 7 }, (_, i) => plusTage(montagVon(heute), i)));
  const heuteIst = $derived(istAm(ICH, heute));
  const heuteSoll = $derived(sollTag(ICH, heute)?.sollSek ?? 0);
  const wocheIst = $derived(woche.filter((t) => t <= heute).reduce((s, t) => s + istAm(ICH, t), 0));
  const wocheSoll = $derived(woche.reduce((s, t) => s + (sollTag(ICH, t)?.sollSek ?? 0), 0));
  const tage = $derived(woche.filter((t) => t <= heute).map((t) => ({ tag: t, ist: istAm(ICH, t), soll: sollTag(ICH, t)?.sollSek ?? 0 })));
  const pfadKarte = (k: Karte): string => telPfad(boardPfad(board(k.board).kuerzel, kartenNummer(k)));
</script>

<TelefonSchale titel="Zeit" unter={datum(heute, true)} reiter="zeit">
  <section class="pw-tel-abschnitt" aria-label="Dein Timer">
    <div class="etikett">Dein Timer</div>
    {#if timer && timerKarte}
      <div class="pw-tel-uhr gross" class:laeuft={!!timer.seit}>
        <div class="oben">
          {#if timer.seit}
            <span class="zustand laeuft"><i class="fa-solid fa-circle-play"></i>Läuft seit {uhrzeit(timer.seit)}</span>
            <span class="sitzung">Sitzung <span class="zahl">{dauer(sitzungSek(timer))}</span></span>
          {:else}
            <span class="zustand pausiert"><i class="fa-solid fa-circle-pause"></i>Angehalten</span>
          {/if}
        </div>
        <b class="zahl stand">{dauer(zeitDerKarte(timerKarte.id), true)}</b>
        <a class="karte-zeile" href={pfadKarte(timerKarte)}><span class="pw-schluessel">{timerKarte.schluessel}</span> {timerKarte.titel}</a>
        {#if timerKarte.schaetzungMin}
          <div class="pw-fortschritt zeit" class:ueber={anteil > 1}><span style="width: {Math.min(100, anteil * 100)}%"></span></div>
          <span class="schaetzung" class:warnung={anteil > 1}>{Math.round(anteil * 100)} % von <span class="zahl">{dauer(timerKarte.schaetzungMin * 60)}</span> Stunden{anteil > 1 ? ", überschritten" : ""}</span>
        {/if}
        <div class="knoepfe">
          {#if timer.seit}
            <button class="knopf haupt" onclick={anhalten} title="Die Sitzung wird gebucht, fortsetzen geht weiter"><i class="fa-solid fa-pause"></i>Anhalten</button>
          {:else}
            <button class="knopf haupt" onclick={fortsetzen}><i class="fa-solid fa-play"></i>Fortsetzen</button>
          {/if}
          <button class="knopf" onclick={stoppen} title="Bucht die Sitzung und beendet den Timer"><i class="fa-solid fa-stop"></i>Stopp</button>
        </div>
      </div>
    {:else}
      <div class="pw-tel-uhr"><span class="zustand aus">Kein Timer läuft</span><span class="schwach">Unten eine Karte starten.</span></div>
    {/if}
  </section>

  {#if zuletzt.length}
    <section class="pw-tel-abschnitt" aria-label="Zuletzt genutzt">
      <div class="etikett">Zuletzt genutzt</div>
      {#each zuletzt as k (k.id)}
        <div class="pw-tel-zeile">
          <button class="pw-tel-timer" title="Timer starten; dein Timer auf einer anderen Karte pausiert dort und bucht" aria-label="Timer auf {k.schluessel} starten"
                  onclick={() => starten(k.id)}><i class="fa-solid fa-play"></i></button>
          <a class="text" href={pfadKarte(k)}><span class="titel">{k.titel}</span>
            <span class="angaben" data-farbe={board(k.board).farbe}><span class="pw-farbpunkt"></span><span class="pw-schluessel">{k.schluessel}</span>
              · gesamt <span class="zahl">{dauer(zeitDerKarte(k.id))}</span></span></a>
        </div>
      {/each}
    </section>
  {/if}

  <section class="pw-tel-abschnitt" aria-label="Zeit nachbuchen">
    <div class="etikett">Nachbuchen</div>
    <div class="pw-tel-formular">
      <label class="feld"><span class="name">Karte</span>
        <input class="eingabe" bind:value={suche} oninput={() => (kartenId = "")} placeholder="Schlüssel oder Titel" autocomplete="off" /></label>
      {#if vorschlaege.length}
        <div class="pw-tel-vorschlaege">
          {#each vorschlaege as k (k.id)}
            <button onclick={() => waehlen(k)}><span class="pw-schluessel">{k.schluessel}</span> {k.titel}</button>
          {/each}
        </div>
      {/if}
      <div class="feld"><span class="name">Tag</span><DatumFeld {tag} ontag={(t) => (tag = t)} titel="Tag der Buchung" /></div>
      <div class="pw-tel-chips">
        {#each TAG_CHIPS as [name, iso] (iso)}
          <button class="chip" aria-pressed={tag === iso} onclick={() => (tag = iso)}>{name}</button>
        {/each}
      </div>
      <div class="feld"><span class="name">Dauer</span><DauerFeld {sek} onwert={(s) => (sek = s)} klasse="feld gross" platzhalter="0:30 oder 1,5" /></div>
      <div class="pw-tel-chips">
        {#each DAUER_CHIPS as d (d)}<button class="chip zahl" aria-pressed={sek === d} onclick={() => (sek = d)}>{dauer(d)}</button>{/each}
      </div>
      {#if fehler}<div class="hinweis warnung"><i class="fa-solid fa-triangle-exclamation"></i><div>{fehler}</div></div>{/if}
      <button class="knopf pw-tel-breit" onclick={buchenKlick}><i class="fa-solid fa-plus"></i>Buchen{kartenId ? ` auf ${karte(kartenId)?.schluessel}` : ""}</button>
    </div>
  </section>

  <section class="pw-tel-abschnitt" aria-label="Stand">
    <div class="etikett">Stand</div>
    <div class="pw-tel-stand">
      <div class="kennzahl" class:laeuft={!!timer?.seit}><span>Heute</span><b>{dauer(heuteIst)}</b><small>Soll {dauer(heuteSoll)}</small>
        <div class="balken" class:lebt={!!timer?.seit}><b style="width: {heuteSoll ? Math.min(100, (100 * heuteIst) / heuteSoll) : 0}%"></b></div></div>
      <div class="kennzahl"><span>Woche</span><b>{dauer(wocheIst)}</b><small>Soll {dauer(wocheSoll)}</small>
        <div class="balken"><b style="width: {wocheSoll ? Math.min(100, (100 * wocheIst) / wocheSoll) : 0}%"></b></div></div>
    </div>
    <div class="pw-tel-tage">
      {#each tage as t (t.tag)}
        <div class="tag"><span>{datum(t.tag, true)}</span><span class="zahl">{dauer(t.ist)}</span>
          {#if t.tag === heute}<span class="schwach">{timer?.seit ? "läuft" : "bisher"}</span>
          {:else}<span class="zahl" class:gut={t.ist >= t.soll} class:warnung={t.ist < t.soll}>{differenz(t.ist - t.soll)}</span>{/if}</div>
      {/each}
    </div>
  </section>
</TelefonSchale>
