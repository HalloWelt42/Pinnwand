<script lang="ts">
  // Einträge eines Tags im Einzelnen, als Leiste rechts über dem Stundenzettel: von, bis, Herkunft (Timer, nachgetragen,
  // Korrektur, Serie, Termin), Dauer und Notiz direkt änderbar, Löschen mit Rückgängig. Die bestätigte Zeit eines Termins
  // läuft von seinem Beginn bis zum Ende; ihre Dauer ändert sich hier nicht, löschen geht. Die Spuren der Buchungsregeln
  // stehen am Eintrag: zusammengefasste Sitzungen, Zerlegung an Mitternacht, der Deckel von 12 Stunden mit seiner Rückfrage.
  import { HERKUNFT } from "../../anzeige";
  import { istAm, kartenName, sitzungAm, sollTag, timerVon } from "../../daten/abfragen";
  import { anhalten } from "../../daten/anwendung/timer.svelte";
  import { dauerAendern, deckelBestaetigen, deckelKorrigieren, loeschen, notizAendern } from "../../daten/anwendung/zeiten.svelte";
  import { datum, datumJahr, dauer, differenz, uhrzeit } from "../../daten/format";
  import { ICH } from "../../daten/ich";
  import { stand } from "../../daten/stand.svelte";
  import { uhr } from "../../daten/uhr.svelte";
  import type { Deckel, Herkunft, Zeiteintrag } from "../../modell";
  import { artName } from "../../regeln/arbeitszeit";
  import { plusTage } from "../../regeln/tage";
  import DauerFeld from "../../teile/DauerFeld.svelte";
  import KartenName from "./KartenName.svelte";
  import TerminName from "./TerminName.svelte";

  let { tag, schliessen, tagWechseln, nachtragen }: {
    tag: string; schliessen: () => void; tagWechseln: (tag: string) => void; nachtragen: (tag: string) => void;
  } = $props();

  const SYMBOL: Record<Herkunft, { symbol: string; titel: string }> = {
    timer: { symbol: "fa-stopwatch", titel: "Aus Start und Stopp; je Karte und Tag ein Eintrag" },
    hand: { symbol: "fa-pen", titel: "Von Hand auf diesen Tag gebucht" },
    korrektur: { symbol: "fa-sliders", titel: "Differenz aus dem Setzen der Zeit (Zelle oder Ticketzeit)" },
    serie: { symbol: "fa-repeat", titel: "Aus einer Serie nachgetragen, mit der geplanten Dauer als Vorschlag" },
    termin: { symbol: "fa-handshake", titel: "Bestätigte Zeit eines Termins, von Beginn bis Ende" },
  };

  const heute = $derived(uhr.heute);
  const liste = $derived(stand.zeiteintraege.filter((e) => e.konto === ICH && e.datum === tag)
    .sort((a, b) => (a.von ?? "99").localeCompare(b.von ?? "99")));
  const s = $derived(sollTag(ICH, tag));
  const soll = $derived(s?.sollSek ?? 0);
  const ist = $derived(istAm(ICH, tag));
  const timer = $derived(timerVon(ICH));
  /** dein laufender Timer, soweit seine Sitzung auf diesen Tag fällt */
  const laeuftHier = $derived(sitzungAm(timer, tag) > 0 ? timer : undefined);

  // Die Rückfrage nach dem Deckel: offen, solange Einträge einer Sitzung, die über diesen Tag lief, den Vermerk gedeckelt
  // tragen (der Server setzt ihn, beantworten nimmt ihn weg, Rückgängig bringt ihn wieder). Eine Sitzung ist ihr Anfang.
  const amTag = (d: Deckel) => d.seit.slice(0, 10) <= tag && tag <= d.bis.slice(0, 10);
  const sitzung = $derived(stand.zeiteintraege.find((e) => e.konto === ICH && e.gedeckelt && amTag(e.gedeckelt))?.gedeckelt);
  const gedeckelt = $derived(sitzung ? stand.zeiteintraege.filter((e) => e.konto === ICH && e.gedeckelt?.seit === sitzung.seit) : []);
  /** Karte der gedeckelten Sitzung (ein Timer läuft immer auf einer Karte) */
  const deckelKarte = $derived(gedeckelt.find((e) => e.karte)?.karte);
  let ende = $state("");

  function istGedeckelt(e: Zeiteintrag): boolean {
    return gedeckelt.some((x) => x.id === e.id);
  }

  /** Die genannte Uhrzeit als Zeitpunkt der Sitzung: die erste nach ihrem Anfang (am Starttag oder am Tag danach) */
  function endeAus(d: Deckel, text: string): string | null {
    const m = text.trim().match(/^(\d{1,2}):(\d{2})$/);
    if (!m || Number(m[1]) > 23 || Number(m[2]) > 59) return null;
    const hhmm = `${m[1].padStart(2, "0")}:${m[2]}`;
    const start = d.seit.slice(0, 10);
    return `${start}T${hhmm}` > d.seit.slice(0, 16) ? `${start}T${hhmm}` : `${plusTage(start, 1)}T${hhmm}`;
  }
  /** das echte Ende, wenn es in der Sitzung liegt (nicht nach dem Stopp des Timers) */
  const endeZeitpunkt = $derived(sitzung ? endeAus(sitzung, ende) : null);
  const endeGueltig = $derived(!!sitzung && !!endeZeitpunkt && endeZeitpunkt <= sitzung.bis.slice(0, 16));

  const grund = $derived.by(() => {
    if (!s) return "Ohne Zeitkonto";
    if (s.grund === "feiertag") return `Feiertag: ${s.feiertag}, Soll 0:00`;
    if (s.abwesenheit) return `${artName(s.abwesenheit)}: Soll ${dauer(s.sollSek)}${s.abwesenheit.notiz ? `, ${s.abwesenheit.notiz}` : ""}`;
    if (s.grund === "halbtagsregel") return `${s.regel}: halber Arbeitstag, Soll ${dauer(s.sollSek)}`;
    if (s.grund === "wochenende") return s.feiertag ? `Wochenende, ${s.feiertag}` : "Wochenende";
    if (s.grund === "arbeitsfrei") return "Kein Arbeitstag in deinem Zeitkonto";
    return "";
  });
</script>

<aside class="pw-zeiten-leiste" aria-label="Einträge {datumJahr(tag, true)}">
  <div class="kopf">
    <span class="etikett">Einträge</span>
    <button class="knopf ohne symbol klein" title="Vortag" onclick={() => tagWechseln(plusTage(tag, -1))}><i class="fa-solid fa-chevron-left"></i></button>
    <h2>{datumJahr(tag, true)}</h2>
    <button class="knopf ohne symbol klein" title="Folgetag" onclick={() => tagWechseln(plusTage(tag, 1))}><i class="fa-solid fa-chevron-right"></i></button>
    <button class="knopf ohne symbol klein rechts" title="Schließen" onclick={schliessen}><i class="fa-solid fa-xmark"></i></button>
  </div>

  <div class="inhalt">
    <div class="pw-zeiten-tageszahlen">
      <span><small>Ist</small><b class:laeuft={!!laeuftHier}>{dauer(ist)}</b></span>
      <span><small>Soll</small><b>{dauer(soll)}</b></span>
      <span><small>{tag === heute ? "Bisher" : "Differenz"}</small><b class:plus={ist - soll > 0 && tag < heute} class:minus={ist - soll < 0 && tag < heute}>{differenz(ist - soll)}</b></span>
    </div>
    {#if grund}<div class="zustand pw-zeiten-grund"><i class="fa-solid fa-calendar-day"></i>{grund}</div>{/if}

    {#if sitzung && gedeckelt.length}
      <div class="hinweis warnung pw-zeiten-rueckfrage">
        <i class="fa-solid fa-hourglass-end"></i>
        <div><b>Timer lief {dauer(sitzung.sekunden)} Stunden.</b> Dein Timer{deckelKarte ? ` auf ${kartenName(deckelKarte).schluessel}` : ""} lief
          von {datum(sitzung.seit, true)} {uhrzeit(sitzung.seit)} bis {datum(sitzung.bis, true)} {uhrzeit(sitzung.bis)}.
          Gebucht sind die ersten 12 Stunden{gedeckelt.length > 1 ? ", an Mitternacht zerlegt" : ""}:
          {gedeckelt.map((e) => `${datum(e.datum, true)} ${dauer(e.sekunden)}`).join(" und ")}. Wann hast du aufgehört?</div>
        <span class="rechts">
          <label class="pw-zeiten-ende">Ende <input class="eingabe zahl" bind:value={ende} placeholder="HH:MM" title="Uhrzeit, zu der du wirklich aufgehört hast (HH:MM)" /></label>
          <button class="knopf haupt klein" disabled={!endeGueltig}
                  title={endeGueltig ? `Gebucht wird von ${datum(sitzung.seit, true)} ${uhrzeit(sitzung.seit)} bis ${datum(endeZeitpunkt!, true)} ${uhrzeit(endeZeitpunkt!)}`
                    : endeZeitpunkt ? "Das Ende liegt nach dem Stopp des Timers" : "Uhrzeit wie 18:30"}
                  onclick={() => deckelKorrigieren(gedeckelt.map((e) => e.id), endeZeitpunkt!)}>Übernehmen</button>
          <button class="knopf klein" title="Die 12 Stunden stimmen so" onclick={() => deckelBestaetigen(gedeckelt.map((e) => e.id))}>12 Stunden lassen</button>
        </span>
      </div>
    {/if}

    <div class="pw-zeiten-eintraege">
      {#each liste as e (e.id)}
        <div class="pw-zeiten-eintrag" class:gedeckelt={istGedeckelt(e)}>
          <span class="was">{#if e.termin}<TerminName id={e.termin} />{:else if e.karte}<KartenName id={e.karte} />{/if}</span>
          <button class="knopf ohne symbol klein" title="Eintrag löschen (Rückgängig möglich)" onclick={() => loeschen(e.id)}><i class="fa-solid fa-xmark"></i></button>
          <div class="mitte">
            <span class="uhr zahl">{e.von ? `${e.von} bis ${e.bis}` : "ohne Uhrzeit"}</span>
            <span class="zustand" title={SYMBOL[e.herkunft].titel}><i class="fa-solid {SYMBOL[e.herkunft].symbol}"></i>{HERKUNFT[e.herkunft]}</span>
            {#if e.termin}
              <span class="dauer zahl" title="Bestätigte Zeit des Termins von Beginn bis Ende; ändern geht nicht, löschen schon">{dauer(e.sekunden)}</span>
            {:else}
              <DauerFeld sek={e.sekunden} mitSekunden klasse="gross" titel="Dauer ändern (H:MM:SS, H:MM oder 1,5)" leerErlaubt={false} onwert={(sek) => dauerAendern(e.id, sek)} />
            {/if}
          </div>
          <div class="unten">
            <input class="eingabe notiz" value={e.notiz ?? ""} placeholder="Notiz" title="Notiz zum Eintrag, steht im Stundennachweis"
                   onchange={(ev) => notizAendern(e.id, ev.currentTarget.value)} />
            {#if e.sitzungen?.length}
              <span class="spur" title={e.sitzungen.map((x) => `${x.von} bis ${x.bis}`).join(", ")}><i class="fa-solid fa-layer-group"></i>{e.sitzungen.length} Sitzungen zusammengefasst</span>
            {/if}
            {#if e.zerlegt}
              <button class="spur verweis" title="An Mitternacht taggenau zerlegt; zum anderen Teil" onclick={() => tagWechseln(e.zerlegt!)}>
                <i class="fa-solid fa-moon"></i>über Mitternacht, Teil am {datum(e.zerlegt, true)}</button>
            {/if}
            {#if istGedeckelt(e)}<span class="spur warn"><i class="fa-solid fa-hourglass-end"></i>nach 12 Stunden gedeckelt</span>{/if}
          </div>
        </div>
      {/each}
      {#if laeuftHier}
        <div class="pw-zeiten-eintrag laeuft">
          <span class="was"><KartenName id={laeuftHier.karte} /></span>
          <button class="knopf ohne symbol klein" title="Anhalten: die Sitzung wird gebucht" onclick={anhalten}><i class="fa-solid fa-pause"></i></button>
          <div class="mitte">
            <span class="uhr zahl">{laeuftHier.seit!.slice(0, 10) === tag ? uhrzeit(laeuftHier.seit!) : "00:00"} bis {tag === heute ? "jetzt" : "24:00"}</span>
            <span class="zustand laeuft"><span class="punkt lebt"></span>läuft</span>
            <span class="dauer zahl">{dauer(sitzungAm(laeuftHier, tag), true)}</span>
          </div>
          <div class="unten"><span class="spur">Wird beim Anhalten in den Timer-Eintrag dieser Karte für diesen Tag gerechnet; ändern geht erst danach.</span></div>
        </div>
      {/if}
      {#if !liste.length && !laeuftHier}<p class="schwach">An diesem Tag ist keine Zeit gebucht.</p>{/if}
    </div>
    {#if !gedeckelt.length && liste.some((e) => e.zerlegt)}
      <p class="schwach pw-zeiten-regel">Läuft ein Timer über Mitternacht, bucht das Anhalten jeden Tag für sich; eine Sitzung über 12 Stunden wird gedeckelt und nachgefragt.</p>
    {/if}
  </div>

  <div class="fuss">
    <button class="knopf" onclick={() => nachtragen(tag)}><i class="fa-solid fa-plus"></i>Auf diesen Tag nachtragen</button>
  </div>
</aside>
