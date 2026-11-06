<script lang="ts">
  // Entwurf HELF-165: Status und Priorität im Kartendetail als Knopfleiste statt Klappliste, mit Symbol und Farbe je
  // Wahl, der Name beim Überfahren. Jeder Teil hell und dunkel nebeneinander; alles lässt sich anklicken.
  import type { Snippet } from "svelte";
  import type { Prioritaet } from "../../src/modell";
  import Farbwahl from "../../src/teile/Farbwahl.svelte";
  import { BOARDS, ohneSymbol, prioritaetsStufen, sortierungsStufen, SPALTENSYMBOLE, spaltenStufen } from "./daten";
  import Detail from "./Detail.svelte";
  import { Stufenwahl } from "appkern-oberflaeche";

  const THEMEN = [["hell", "Hell"], ["dunkel", "Dunkel"]] as const;
  const HELFER = BOARDS[0].spalten;

  /** Stand jeder Probeleiste, je Schlüssel */
  let wahl = $state<Record<string, string>>({});
  const w = (schluessel: string, vorgabe: string): string => wahl[schluessel] ?? vorgabe;

  let symbol = $state("fa-person-digging");
  const symbolStufen = SPALTENSYMBOLE.map(([s, n]) => ({ wert: s, titel: n, symbol: s, farbe: "honig" }));
  const prioName = (p: Prioritaet): string => prioritaetsStufen().find((x) => x.wert === p)!.titel;
  const prioDaten = (p: Prioritaet) => prioritaetsStufen().find((x) => x.wert === p)!;
</script>

<div class="ent-seite">
  <header>
    <h1>Entwurf HELF-165: Status und Priorität als Knopfleiste</h1>
    <p>Im Kartendetail werden die Klapplisten Status und Priorität zu Knopfleisten mit genau einer Wahl: ein Klick setzt,
      Symbol und Farbe sagen den Zustand, der Name steht beim Überfahren. Alles ist anklickbar; mit der Tastatur springt
      Tab in die Leiste, die Pfeile wandern, Leertaste oder Enter wählt.</p>
  </header>

  {#snippet paar(inhalt: Snippet<[string]>)}
    <div class="ent-paar">
      {#each THEMEN as [thema, name] (thema)}
        <div class="ent-thema" data-theme={thema}><div class="etikett">{name}</div>{@render inhalt(thema)}</div>
      {/each}
    </div>
  {/snippet}

  <section class="ent-abschnitt">
    <h2>1. Heute: Klapplisten</h2>
    <p>Zum Vergleich der jetzige Stand der Angaben.</p>
    {#snippet heute(_thema: string)}<Detail spalten={HELFER} art="heute" />{/snippet}
    {@render paar(heute)}
  </section>

  <section class="ent-abschnitt">
    <h2>2. Vorschlag A: nur Symbole <span class="zustand laeuft">empfohlen</span></h2>
    <p>Die Farben kommen aus dem Board (Farbe der Spalte) und aus der Bedeutung (Priorität: Stahl, Honig, Warnung, Gefahr).
      Den Namen des Status nennt schon der Kopf der Karte; die Leiste bleibt dadurch schmal, auch bei vielen Spalten.</p>
    {#snippet a(_thema: string)}<Detail spalten={HELFER} art="neu" anzeige="symbol" />{/snippet}
    {@render paar(a)}
  </section>

  <section class="ent-abschnitt">
    <h2>3. Vorschlag B: die gewählte mit Namen</h2>
    <p>Wie A, nur trägt die gewählte Wahl ihren Namen; die Leiste ändert dabei ihre Breite.</p>
    {#snippet b(_thema: string)}<Detail spalten={HELFER} art="neu" anzeige="gewaehlt" />{/snippet}
    {@render paar(b)}
  </section>

  <section class="ent-abschnitt">
    <h2>4. Symbole der Spalten</h2>
    <p>Spalten haben heute nur Name und Farbe. Vorschlag: jede Spalte bekommt ein Symbol, wählbar in den Einstellungen des
      Boards; die Vorlagen bringen passende mit. Ohne gewähltes Symbol zeigt eine offene Spalte einen Farbpunkt, die
      Erledigt-Spalte einen Haken (rechte Spalte der Tabelle).</p>
    {#snippet spalten(thema: string)}
      <div class="ent-tabelle">
        <span class="name"></span><span class="wert ent-notiz">mit gewähltem Symbol, ohne Symbol</span>
        {#each BOARDS as bo, i (bo.name)}
          <span class="name">{bo.name}</span>
          <span class="wert">
            <Stufenwahl wert={w(`${thema}-s${i}`, bo.spalten[1].id)} optionen={spaltenStufen(bo.spalten)} beschriftung="Status"
                        onwahl={(x) => (wahl[`${thema}-s${i}`] = x)} />
            <Stufenwahl wert={w(`${thema}-o${i}`, bo.spalten[1].id)} optionen={spaltenStufen(ohneSymbol(bo.spalten))} beschriftung="Status"
                        onwahl={(x) => (wahl[`${thema}-o${i}`] = x)} />
          </span>
        {/each}
        <span class="name">Priorität</span>
        <span class="wert"><Stufenwahl wert={w(`${thema}-p`, "dringend")} optionen={prioritaetsStufen()} beschriftung="Priorität"
                                       onwahl={(x) => (wahl[`${thema}-p`] = x)} /></span>
        <span class="name">Ohne Recht zu ändern</span>
        <span class="wert"><Stufenwahl wert="d" optionen={spaltenStufen(HELFER)} beschriftung="Status" gesperrt onwahl={() => {}} />
          <Stufenwahl wert="mittel" optionen={prioritaetsStufen()} beschriftung="Priorität" gesperrt onwahl={() => {}} /></span>
      </div>
    {/snippet}
    {@render paar(spalten)}
  </section>

  <section class="ent-abschnitt">
    <h2>5. Einstellungen des Boards: Symbol der Spalte</h2>
    <p>In Einstellungen, Spalten kommt je Spalte "Symbol" neben "Farbe", als derselbe Baustein. Ebenso könnte die
      Sortierung der Spalte (heute eine Klappliste mit sechs Einträgen) eine Knopfleiste werden; das ist eine offene Frage.</p>
    {#snippet einstellung(thema: string)}
      <article class="pw-verwaltung-eintrag" data-farbe="honig" aria-label="Spalte Dran">
        <div class="oben">
          <span class="pw-verwaltung-griff"><i class="fa-solid fa-grip-vertical"></i></span>
          <span class="pw-farbpunkt"></span>
          <input class="eingabe pw-verwaltung-name" value="Dran" aria-label="Name der Spalte" />
          <span class="pw-angabe flaeche"><i class="fa-regular fa-note-sticky"></i>3 Karten</span>
        </div>
        <div class="angaben">
          <span class="angabe"><span class="etikett">Farbe</span><Farbwahl kompakt wert="honig" waehlen={() => {}} wofuer="Farbe der Spalte Dran" /></span>
          <span class="angabe"><span class="etikett">Symbol</span>
            <Stufenwahl wert={symbol} optionen={symbolStufen} beschriftung="Symbol der Spalte Dran" onwahl={(x) => (symbol = x)} /></span>
          <span class="angabe"><span class="etikett">Sortierung</span>
            <Stufenwahl wert={w(`${thema}-so`, "arbeitsbeginn")} optionen={sortierungsStufen()} beschriftung="Sortierung der Spalte Dran"
                        onwahl={(x) => (wahl[`${thema}-so`] = x)} /></span>
        </div>
      </article>
    {/snippet}
    {@render paar(einstellung)}
  </section>

  <section class="ent-abschnitt">
    <h2>6. Telefon</h2>
    <p>Am Telefon gibt es kein Überfahren. Vorschlag: Status bleibt beim Blatt "Verschieben nach" (Erledigen dort per
      Halten, auch andere Boards), die Priorität zeigt Symbol, Farbe und Namen. Daneben die Alternative mit Leisten in
      44 Pixeln, die gewählte mit Namen.</p>
    {#snippet telefone(thema: string)}
      <div class="ent-telefone">
        <div class="ent-telefon">
          <div class="etikett">Vorschlag</div>
          <section class="pw-tel-abschnitt" aria-label="Status">
            <div class="etikett">Status</div>
            <div class="pw-tel-status"><span class="zustand" data-farbe="honig"><span class="pw-farbpunkt"></span>Dran</span><span class="schwach">seit 2 Tagen</span></div>
            <button class="knopf haupt pw-tel-breit"><i class="fa-solid fa-arrow-right-arrow-left"></i>Verschieben nach</button>
          </section>
          <section class="pw-tel-abschnitt" aria-label="Angaben">
            <div class="etikett">Angaben</div>
            <div class="pw-tel-angaben">
              <span class="name"><i class="fa-solid fa-flag"></i>Priorität</span>
              <span class="wert"><span class="ent-prio" style="--stufe: var(--{prioDaten('hoch').farbe})"><i class="fa-solid {prioDaten('hoch').symbol}"></i>{prioName("hoch")}</span></span>
              <span class="name"><i class="fa-regular fa-calendar"></i>Fällig</span>
              <span class="wert"><span class="schwach">ohne</span></span>
            </div>
          </section>
        </div>
        <div class="ent-telefon">
          <div class="etikett">Alternative</div>
          <section class="pw-tel-abschnitt" aria-label="Status">
            <div class="etikett">Status</div>
            <Stufenwahl wert={w(`${thema}-ts`, "d")} optionen={spaltenStufen(HELFER)} beschriftung="Status" anzeige="gewaehlt" gross
                        onwahl={(x) => (wahl[`${thema}-ts`] = x)} />
          </section>
          <section class="pw-tel-abschnitt" aria-label="Angaben">
            <div class="etikett">Priorität</div>
            <Stufenwahl wert={w(`${thema}-tp`, "hoch")} optionen={prioritaetsStufen()} beschriftung="Priorität" anzeige="gewaehlt" gross
                        onwahl={(x) => (wahl[`${thema}-tp`] = x)} />
          </section>
        </div>
      </div>
    {/snippet}
    {@render paar(telefone)}
  </section>
</div>

<style>
  .ent-prio { display: inline-flex; align-items: center; gap: 6px; height: 28px; padding: 0 10px; border-radius: 999px; font-weight: 600;
              color: var(--stufe); background: color-mix(in srgb, var(--stufe) var(--toenung), transparent); }
</style>
