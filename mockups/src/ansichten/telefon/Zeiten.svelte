<script lang="ts">
  // Zeit am Telefon: dein einer Timer groß mit Anhalten und Stopp (beides bucht, M-79), zuletzt genutzte Karten zum
  // Starten (ein Start hält den laufenden an und bucht, M-80), Zeit nachbuchen auf Karte, Tag und Dauer (M-86, Eingabe
  // wie M-90) und der Stand von heute und der Woche gegen das Soll aus deinem Zeitkonto.
  import { HEUTE, ICH, ZEITEINTRAEGE } from "../../beispiel/daten";
  import { datum, dauer, laufendSek, uhrzeit } from "../../beispiel/format";
  import { board, karte, stand } from "../../beispiel/stand.svelte";
  import type { Karte } from "../../modell";
  import { boardPfad, wert } from "../../weg.svelte";
  import {
    anhalten, gebucht, kartenzeit, laufende, pausierte, starten, stoppen, tagesSoll, wochenSoll, wochentage, zeitBuchen,
  } from "./aktionen.svelte";
  import { datumLesen, datumText, dauerLesen, tagePlus } from "./eingabe";
  import TelefonSchale from "./TelefonSchale.svelte";
  import { telPfad } from "./weg";

  const lauf = $derived(laufende());
  const pause = $derived(pausierte());
  const uhr = $derived(lauf ?? pause);
  const anteil = $derived(uhr?.schaetzungMin ? kartenzeit(uhr) / 60 / uhr.schaetzungMin : 0);

  /** Karten, auf die du Zeit buchen kannst: Arbeit in Boards mit Zeiterfassung, nicht erledigt */
  const buchbar = (k: Karte): boolean => {
    const b = board(k.board);
    return b.module.zeiterfassung && k.art === "arbeit" && !b.spalten.find((s) => s.id === k.spalte)?.erledigt;
  };
  const zuletztGebucht = (k: Karte): string =>
    ZEITEINTRAEGE.filter((z) => z.konto === ICH && z.karte === k.id).map((z) => z.datum).sort().at(-1) ?? "";
  const zuletzt = $derived(stand.karten.filter((k) => buchbar(k) && k.id !== uhr?.id && (k.zustaendig.includes(ICH) || zuletztGebucht(k)))
    .sort((a, b) => zuletztGebucht(b).localeCompare(zuletztGebucht(a)) || b.bewegtAm.localeCompare(a.bewegtAm)).slice(0, 4));

  // Nachbuchen: Karte als Textfeld mit Vorschlägen, Tag im deutschen Format, Dauer frei
  const vorbelegt = stand.karten.find((k) => k.schluessel.toLowerCase() === wert("karte").toLowerCase() && buchbar(k));
  let kartenId = $state(vorbelegt?.id ?? "");
  let suche = $state(vorbelegt ? `${vorbelegt.schluessel} ${vorbelegt.titel}` : "");
  let tag = $state(datumText(HEUTE));
  let dauerEingabe = $state("");
  let fehler = $state("");
  const vorschlaege = $derived(kartenId || !suche.trim() ? [] : stand.karten.filter((k) => buchbar(k) &&
    `${k.schluessel} ${k.titel}`.toLowerCase().includes(suche.trim().toLowerCase())).slice(0, 4));

  function waehlen(k: Karte): void { kartenId = k.id; suche = `${k.schluessel} ${k.titel}`; fehler = ""; }
  function tippen(): void { kartenId = ""; }
  function buchen(): void {
    const iso = datumLesen(tag);
    const sek = dauerLesen(dauerEingabe);
    if (!kartenId) fehler = "Karte bitte aus den Vorschlägen wählen.";
    else if (!iso) fehler = "Tag bitte wie 27.10.2026 eingeben.";
    else if (iso > HEUTE) fehler = "Zeit lässt sich nur bis heute buchen.";
    else if (!sek || sek <= 0) fehler = "Dauer bitte wie 1:30, 1,5 oder 90min eingeben.";
    else {
      zeitBuchen(kartenId, iso, sek);
      fehler = "";
      dauerEingabe = "";
    }
  }
  const TAG_CHIPS = [["Heute", HEUTE], ["Gestern", tagePlus(HEUTE, -1)]] as const;
  const DAUER_CHIPS = ["0:15", "0:30", "1:00", "2:00"];

  const heute = $derived(gebucht(HEUTE));
  const woche = $derived(wochentage().reduce((s, t) => s + t.sek, 0));
  const pfadKarte = (k: Karte): string => telPfad(boardPfad(board(k.board).kuerzel, k.schluessel.split("-")[1]));
</script>

<TelefonSchale titel="Zeit" unter={datum(HEUTE, true)} reiter="zeit">
  <section class="pw-tel-abschnitt" aria-label="Dein Timer">
    <div class="etikett">Dein Timer</div>
    {#if uhr}
      <div class="pw-tel-uhr gross" class:laeuft={!!lauf}>
        <div class="oben">
          {#if lauf}
            <span class="zustand laeuft"><i class="fa-solid fa-circle-play"></i>Läuft seit {uhrzeit(lauf.laeuft!.seit)}</span>
          {:else}
            <span class="zustand pausiert"><i class="fa-solid fa-circle-pause"></i>Angehalten</span>
          {/if}
          <span class="sitzung">{#if lauf}Sitzung <span class="zahl">{dauer(laufendSek(lauf.laeuft!.seit))}</span>{/if}</span>
        </div>
        <b class="zahl stand">{dauer(kartenzeit(uhr), true)}</b>
        <a class="karte-zeile" href={pfadKarte(uhr)}><span class="pw-schluessel">{uhr.schluessel}</span> {uhr.titel}</a>
        {#if uhr.schaetzungMin}
          <div class="pw-fortschritt zeit" class:ueber={anteil > 1}><span style="width: {Math.min(100, anteil * 100)}%"></span></div>
          <span class="schaetzung" class:warnung={anteil > 1}>{Math.round(anteil * 100)} % von <span class="zahl">{dauer(uhr.schaetzungMin * 60)}</span> Std{anteil > 1 ? ", überschritten" : ""}</span>
        {/if}
        <div class="knoepfe">
          {#if lauf}
            <button class="knopf haupt" onclick={anhalten}><i class="fa-solid fa-pause"></i>Anhalten</button>
          {:else}
            <button class="knopf haupt" onclick={() => starten(uhr.id)}><i class="fa-solid fa-play"></i>Fortsetzen</button>
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
          <button class="pw-tel-timer" title="Timer starten; ein laufender hält dabei an und bucht" aria-label="Timer auf {k.schluessel} starten"
                  onclick={() => starten(k.id)}><i class="fa-solid fa-play"></i></button>
          <a class="text" href={pfadKarte(k)}><span class="titel">{k.titel}</span>
            <span class="angaben" data-farbe={board(k.board).farbe}><span class="pw-farbpunkt"></span><span class="pw-schluessel">{k.schluessel}</span>
              · gesamt <span class="zahl">{dauer(kartenzeit(k))}</span></span></a>
        </div>
      {/each}
    </section>
  {/if}

  <section class="pw-tel-abschnitt" aria-label="Zeit nachbuchen">
    <div class="etikett">Nachbuchen</div>
    <div class="pw-tel-formular">
      <label class="feld"><span class="name">Karte</span>
        <input class="eingabe" bind:value={suche} oninput={tippen} placeholder="Schlüssel oder Titel" autocomplete="off" /></label>
      {#if vorschlaege.length}
        <div class="pw-tel-vorschlaege">
          {#each vorschlaege as k (k.id)}
            <button onclick={() => waehlen(k)}><span class="pw-schluessel">{k.schluessel}</span> {k.titel}</button>
          {/each}
        </div>
      {/if}
      <label class="feld"><span class="name">Tag</span><input class="eingabe zahl" bind:value={tag} inputmode="numeric" placeholder="TT.MM.JJJJ" /></label>
      <div class="pw-tel-chips">
        {#each TAG_CHIPS as [name, iso] (iso)}
          <button class="chip" aria-pressed={datumLesen(tag) === iso} onclick={() => (tag = datumText(iso))}>{name}</button>
        {/each}
      </div>
      <label class="feld"><span class="name">Dauer</span><input class="eingabe zahl" bind:value={dauerEingabe} placeholder="0:30 oder 1,5" /></label>
      <div class="pw-tel-chips">
        {#each DAUER_CHIPS as d (d)}<button class="chip zahl" aria-pressed={dauerEingabe === d} onclick={() => (dauerEingabe = d)}>{d}</button>{/each}
      </div>
      {#if fehler}<div class="hinweis warnung"><i class="fa-solid fa-triangle-exclamation"></i><div>{fehler}</div></div>{/if}
      <button class="knopf pw-tel-breit" onclick={buchen}><i class="fa-solid fa-plus"></i>Buchen{kartenId ? ` auf ${karte(kartenId)?.schluessel}` : ""}</button>
    </div>
  </section>

  <section class="pw-tel-abschnitt" aria-label="Stand">
    <div class="etikett">Stand</div>
    <div class="pw-tel-stand">
      <div class="kennzahl" class:laeuft={!!lauf}><span>Heute</span><b>{dauer(heute)}</b><small>Soll {dauer(tagesSoll())}</small>
        <div class="balken" class:lebt={!!lauf}><b style="width: {Math.min(100, (100 * heute) / tagesSoll())}%"></b></div></div>
      <div class="kennzahl"><span>Woche</span><b>{dauer(woche)}</b><small>Soll {dauer(wochenSoll())}</small>
        <div class="balken"><b style="width: {Math.min(100, (100 * woche) / wochenSoll())}%"></b></div></div>
    </div>
    <div class="pw-tel-tage">
      {#each wochentage() as t (t.tag)}
        {@const diff = t.sek - tagesSoll()}
        <div class="tag"><span>{datum(t.tag, true)}</span><span class="zahl">{dauer(t.sek)}</span>
          {#if t.tag === HEUTE}<span class="schwach">{lauf ? "läuft" : "bisher"}</span>
          {:else}<span class="zahl" class:gut={diff >= 0} class:warnung={diff < 0}>{diff >= 0 ? "+" : "-"}{dauer(Math.abs(diff))}</span>{/if}</div>
      {/each}
    </div>
  </section>
</TelefonSchale>
