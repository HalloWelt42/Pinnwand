<script lang="ts">
  // Einträge eines Tags im Einzelnen, als Leiste rechts über dem Stundenzettel: von, bis, Herkunft (Timer, nachgetragen,
  // Korrektur, Serie), Dauer und Notiz direkt änderbar, Löschen mit Rückgängig. Die Spuren der Buchungsregeln stehen am
  // Eintrag: zusammengefasste Sitzungen, Zerlegung an Mitternacht, der Deckel von 12 Stunden mit seiner Rückfrage.
  import { HEUTE, ICH } from "../../beispiel/daten";
  import { datum, dauer } from "../../beispiel/format";
  import { datumJahr, differenz } from "./anzeige";
  import DauerFeld from "./DauerFeld.svelte";
  import KartenName from "./KartenName.svelte";
  import { ARTEN, plusTage } from "./regeln";
  import { anhalten, dauerAendern, deckelBestaetigen, deckelKorrigieren, eintraegeVon, istAm, karteVon, laufend, laufendAm, loeschen, notizAendern, soll } from "./stand.svelte";
  import type { Eintrag } from "./typen";

  let { tag, deckel = false, schliessen, tagWechseln, nachtragen }: {
    tag: string; deckel?: boolean; schliessen: () => void; tagWechseln: (tag: string) => void; nachtragen: (tag: string) => void;
  } = $props();

  const HERKUNFT: Record<Eintrag["herkunft"], { name: string; symbol: string; titel: string }> = {
    timer: { name: "Timer", symbol: "fa-stopwatch", titel: "Aus Start und Stopp; je Karte und Tag ein Eintrag" },
    hand: { name: "nachgetragen", symbol: "fa-pen", titel: "Von Hand auf diesen Tag gebucht" },
    korrektur: { name: "Korrektur", symbol: "fa-sliders", titel: "Differenz aus dem Setzen der Zeit (Zelle oder Ticketzeit)" },
    serie: { name: "Serie", symbol: "fa-repeat", titel: "Aus einer Serie nachgetragen, mit der geplanten Dauer als Vorschlag" },
  };

  const liste = $derived(eintraegeVon(ICH, tag).slice().sort((a, b) => (a.von ?? "99").localeCompare(b.von ?? "99")));
  const s = $derived(soll(ICH, tag)!);
  const ist = $derived(istAm(ICH, tag));
  const lauf = $derived(laufend(ICH));
  const laeuftHeute = $derived(lauf && lauf.seit.slice(0, 10) === tag ? lauf : undefined);
  const offen = $derived(liste.filter((e) => e.gedeckelt));
  const offenAlle = $derived(deckel ? eintraegeVon(ICH, plusTage(tag, -1), plusTage(tag, 1)).filter((e) => e.gedeckelt) : []);
  let ende = $state("00:25");

  const grund = $derived.by(() => {
    if (s.grund === "feiertag") return `Feiertag: ${s.feiertag}, Soll 0:00`;
    if (s.abwesenheit) return `${ARTEN[s.abwesenheit.art].name}: Soll ${dauer(s.sollSek)}${s.abwesenheit.notiz ? `, ${s.abwesenheit.notiz}` : ""}`;
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
      <span><small>Ist</small><b class:laeuft={!!laeuftHeute}>{dauer(ist)}</b></span>
      <span><small>Soll</small><b>{dauer(s.sollSek)}</b></span>
      <span><small>{tag === HEUTE ? "Bisher" : "Differenz"}</small><b class:plus={ist - s.sollSek > 0 && tag < HEUTE} class:minus={ist - s.sollSek < 0 && tag < HEUTE}>{differenz(ist - s.sollSek)}</b></span>
    </div>
    {#if grund}<div class="zustand pw-zeiten-grund"><i class="fa-solid fa-calendar-day"></i>{grund}</div>{/if}

    {#if offenAlle.length}
      <div class="hinweis warnung pw-zeiten-rueckfrage">
        <i class="fa-solid fa-hourglass-end"></i>
        <div><b>Timer lief {dauer(offenAlle[0].gedeckelt!.sekunden)} Std.</b> Dein Timer auf {karteVon(offenAlle[0].karte)?.schluessel} lief
          {offenAlle[0].gedeckelt!.spanne}. Gebucht sind die ersten 12 Stunden, an Mitternacht zerlegt:
          {offenAlle.map((e) => `${datum(e.datum, true)} ${dauer(e.sekunden)}`).join(" und ")}. Wann hast du aufgehört?</div>
        <span class="rechts">
          <label class="pw-zeiten-ende">Ende <input class="eingabe zahl" bind:value={ende} title="Uhrzeit, zu der du wirklich aufgehört hast (HH:MM)" /></label>
          <button class="knopf haupt klein" onclick={() => deckelKorrigieren(offenAlle.map((e) => e.id), ende)}>Übernehmen</button>
          <button class="knopf klein" title="Die 12 Stunden stimmen so" onclick={() => deckelBestaetigen(offenAlle.map((e) => e.id))}>12 Std. lassen</button>
        </span>
      </div>
    {/if}

    <div class="pw-zeiten-eintraege">
      {#each liste as e (e.id)}
        {@const k = karteVon(e.karte)}
        {@const hk = HERKUNFT[e.herkunft]}
        <div class="pw-zeiten-eintrag" class:gedeckelt={!!e.gedeckelt}>
          <span class="was">{#if k}<KartenName karte={k} />{/if}</span>
          <button class="knopf ohne symbol klein" title="Eintrag löschen (Rückgängig möglich)" onclick={() => loeschen(e.id)}><i class="fa-solid fa-xmark"></i></button>
          <div class="mitte">
            <span class="uhr zahl">{e.von ? `${e.von} bis ${e.bis}` : "ohne Uhrzeit"}</span>
            <span class="zustand" title={hk.titel}><i class="fa-solid {hk.symbol}"></i>{hk.name}</span>
            <DauerFeld sek={e.sekunden} mitSekunden klasse="gross" titel="Dauer ändern (H:MM:SS, H:MM oder 1,5)" leerErlaubt={false} onwert={(sek) => dauerAendern(e.id, sek)} />
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
            {#if e.gedeckelt}<span class="spur warn"><i class="fa-solid fa-hourglass-end"></i>nach 12 Std. gedeckelt</span>{/if}
          </div>
        </div>
      {/each}
      {#if laeuftHeute}
        <div class="pw-zeiten-eintrag laeuft">
          <span class="was"><KartenName karte={laeuftHeute.karte} /></span>
          <button class="knopf ohne symbol klein" title="Anhalten und buchen" onclick={anhalten}><i class="fa-solid fa-stop"></i></button>
          <div class="mitte">
            <span class="uhr zahl">{laeuftHeute.seit.slice(11, 16)} bis jetzt</span>
            <span class="zustand laeuft"><span class="punkt lebt"></span>läuft</span>
            <span class="dauer zahl">{dauer(laufendAm(ICH, tag), true)}</span>
          </div>
          <div class="unten"><span class="spur">Wird beim Anhalten in den Timer-Eintrag dieser Karte für heute gerechnet; ändern geht erst danach.</span></div>
        </div>
      {/if}
      {#if !liste.length && !laeuftHeute}<p class="schwach">An diesem Tag ist keine Zeit gebucht.</p>{/if}
    </div>
    {#if offen.length === 0 && liste.some((e) => e.zerlegt)}
      <p class="schwach pw-zeiten-regel">Läuft ein Timer über Mitternacht, bucht das Anhalten jeden Tag für sich; eine Sitzung über 12 Stunden wird gedeckelt und nachgefragt.</p>
    {/if}
  </div>

  <div class="fuss">
    <button class="knopf" onclick={() => nachtragen(tag)}><i class="fa-solid fa-plus"></i>Auf diesen Tag nachtragen</button>
  </div>
</aside>
