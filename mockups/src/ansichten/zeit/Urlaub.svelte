<script lang="ts">
  // Urlaub und Abwesenheit: links eintragen (von, bis, Art, halber Tag, Notiz) und die Liste des Jahres mit ihrer Wirkung
  // auf das Soll, rechts das Ergebnis der Eingabe Tag für Tag und Brückentage als Vorschlag. Wochenenden und Feiertage
  // zählen nie als Urlaubstag; was sich mit einer vorhandenen Abwesenheit überschneidet, wird ersetzt.
  import { HEUTE, ICH, SERIEN } from "../../beispiel/daten";
  import { datum, dauer } from "../../beispiel/format";
  import type { Abwesenheit, AbwesenheitArt } from "../../modell";
  import { spanne, tageZahl } from "./anzeige";
  import DatumFeld from "./DatumFeld.svelte";
  import { ARTEN, brueckentage, urlaubstage, wirkung, wochentag } from "./regeln";
  import { abwesenheitEintragen, abwesenheitEntfernen, halbtage, kontoVon, zeit } from "./stand.svelte";

  let { entwurf: _entwurf = "" }: { entwurf?: string } = $props();

  const k = kontoVon(ICH)!;
  const jahr = Number(HEUTE.slice(0, 4));
  let von = $state("2026-11-16");
  let bis = $state("2026-11-20");
  let art = $state<AbwesenheitArt>("urlaub");
  let halb = $state(false);
  let notiz = $state("");
  const WAHL: AbwesenheitArt[] = ["urlaub", "krank", "frei", "fortbildung"];

  const gueltig = $derived(von <= bis);
  const neu = $derived<Abwesenheit>({ konto: ICH, von, bis: gueltig ? bis : von, art: art === "urlaub" && halb ? "halbtag" : art, notiz: notiz || undefined });
  const w = $derived(wirkung(k, halbtage(ICH), neu));
  const vorhanden = $derived(zeit.abwesenheiten.filter((a) => a.konto === ICH && a.von <= neu.bis && a.bis >= neu.von));
  const ersetzt = $derived(vorhanden.reduce((s, a) => s + wirkung(k, halbtage(ICH), a).urlaubstage, 0));
  const genommen = $derived(urlaubstage(k, halbtage(ICH), zeit.abwesenheiten, jahr, HEUTE));
  const geplant = $derived(urlaubstage(k, halbtage(ICH), zeit.abwesenheiten, jahr, HEUTE, true));
  const frei = $derived(k.urlaubsanspruch + k.resturlaubVorjahr - genommen - geplant);

  /** Serien nur für dich legen an Abwesenheitstagen keine Karte an (wie bisher: Urlaubstage werden übersprungen) */
  const ausgesetzt = $derived.by(() => {
    if (ARTEN[neu.art].soll >= 1) return [];
    const weg = w.tage.filter((t) => t.basisSek > 0 && t.sollSek < t.basisSek).map((t) => t.tag);
    return SERIEN.filter((x) => !x.pausiert && x.teilnehmer.length === 1 && x.teilnehmer[0] === ICH).map((x) => {
      const passt = (t: string) => x.rhythmus === "taeglich" || (x.rhythmus === "werktags" && wochentag(t) >= 1 && wochentag(t) <= 5)
        || (x.rhythmus === "woechentlich" && !!x.tage?.includes(wochentag(t)));
      return { titel: x.titel, tage: weg.filter(passt).length };
    }).filter((x) => x.tage > 0);
  });
  const liste = $derived(zeit.abwesenheiten.filter((a) => a.konto === ICH && a.bis.slice(0, 4) >= String(jahr)).slice().sort((a, b) => a.von.localeCompare(b.von)));
  const bruecken = $derived(brueckentage(k, HEUTE, `${jahr + 1}-12-31`));

  function eintragen(): void {
    if (!gueltig || w.arbeitstage === 0) return;
    abwesenheitEintragen(neu);
    notiz = "";
  }
  function bruecke(t: string): void {
    von = t; bis = t; art = "urlaub"; halb = false; notiz = "Brückentag";
  }
</script>

<div class="spalten breit-rechts pw-arbeitszeit-spalten">
  <div class="rollfeld pw-arbeitszeit-links">
    <section class="bereich pw-arbeitszeit-formular pw-arbeitszeit-vorn">
      <h2 class="pw-arbeitszeit-titel">Eintragen</h2>
      <div class="pw-arbeitszeit-felder">
        <label><span class="etikett">Von</span><DatumFeld tag={von} ontag={(t) => { von = t; if (bis < t) bis = t; }} /></label>
        <label><span class="etikett">Bis</span><DatumFeld tag={bis} ontag={(t) => (bis = t)} /></label>
      </div>
      {#if !gueltig}<p class="pw-arbeitszeit-fehler"><i class="fa-solid fa-triangle-exclamation"></i>Bis liegt vor Von.</p>{/if}
      <div class="etikett">Art</div>
      <div class="wahl pw-arbeitszeit-arten">
        {#each WAHL as a (a)}
          <label class:an={art === a}><input type="radio" name="art" value={a} bind:group={art} class="pw-arbeitszeit-unsichtbar" />
            <span class="kreis"></span>
            <div><b><i class="fa-solid {ARTEN[a].symbol}"></i> {ARTEN[a].name}</b><span>{ARTEN[a].wirkung}</span></div></label>
        {/each}
      </div>
      {#if art === "urlaub"}
        <label class="pw-arbeitszeit-schalter"><button class="schalter" class:an={halb} aria-pressed={halb} aria-label="Halbe Tage" onclick={() => (halb = !halb)}></button>
          Halbe Tage <span class="schwach klein">jeder Tag zählt halb, für Soll und Urlaub</span></label>
      {/if}
      <input class="eingabe" bind:value={notiz} placeholder="Notiz, etwa Sommer oder Messe" />
      <div class="knoepfe">
        <button class="knopf haupt" disabled={!gueltig || w.arbeitstage === 0} onclick={eintragen}><i class="fa-solid fa-check"></i>Eintragen</button>
      </div>
    </section>

    <section class="bereich pw-arbeitszeit-spaeter">
      <h2 class="pw-arbeitszeit-titel">Abwesenheiten {jahr}</h2>
      <div class="tabellen-raum">
        <table class="tabelle pw-arbeitszeit-liste">
          <thead><tr><th>Zeitraum</th><th>Art</th><th class="zahl">Arbeitstage</th><th class="zahl">Urlaub</th><th class="zahl">Soll</th><th>Notiz</th><th></th></tr></thead>
          <tbody>
            {#each liste as a (`${a.von}-${a.art}`)}
              {@const wa = wirkung(k, halbtage(ICH), a)}
              <tr class:spaeter={a.von > HEUTE}>
                <td>{spanne(a.von, a.bis)} {#if a.von > HEUTE}<span class="zustand wartet">geplant</span>{/if}</td>
                <td data-titel="Art"><span class="pw-arbeitszeit-art art-{a.art}"><i class="fa-solid {ARTEN[a.art].symbol}"></i>{ARTEN[a.art].name}</span></td>
                <td class="zahl" data-titel="Arbeitstage">{tageZahl(wa.arbeitstage)}</td>
                <td class="zahl" data-titel="Urlaub">{wa.urlaubstage ? tageZahl(wa.urlaubstage) : ""}</td>
                <td class="zahl" data-titel="Soll" title={ARTEN[a.art].wirkung}>{wa.sollSek ? `-${dauer(wa.sollSek)}` : "bleibt"}</td>
                <td data-titel="Notiz">{a.notiz ?? ""}</td>
                <td>{#if a.von > HEUTE}<button class="knopf ohne symbol klein" title="Entfernen (Rückgängig möglich)" onclick={() => abwesenheitEntfernen(a)}><i class="fa-solid fa-xmark"></i></button>{/if}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </section>
  </div>

  <div class="rollfeld pw-arbeitszeit-seite">
    <section class="bereich pw-arbeitszeit-mitte">
      <div class="etikett">Wirkung</div>
      <h2>{gueltig ? spanne(neu.von, neu.bis) : "Zeitraum prüfen"}</h2>
      <div class="pw-arbeitszeit-wirkung">
        <div class="zeile-wert"><span>Arbeitstage</span><b class="zahl">{tageZahl(w.arbeitstage)}</b></div>
        <div class="zeile-wert"><span>Soll</span><b class="zahl">{w.sollSek ? `-${dauer(w.sollSek)}` : "bleibt"}</b></div>
        {#if ARTEN[neu.art].urlaub > 0}
          <div class="zeile-wert"><span>Urlaubstage</span><b class="zahl">{tageZahl(w.urlaubstage)}</b></div>
          <div class="zeile-wert"><span>Frei verplanbar</span><b class="zahl" class:minus={frei + ersetzt - w.urlaubstage < 0}>{tageZahl(frei)} auf {tageZahl(frei + ersetzt - w.urlaubstage)}</b></div>
        {/if}
      </div>
      {#each ausgesetzt as x (x.titel)}
        <div class="zeile-wert"><span><i class="fa-solid fa-repeat"></i> Serie {x.titel}</span><b class="zahl">an {x.tage} {x.tage === 1 ? "Tag" : "Tagen"} ausgesetzt</b></div>
      {/each}
      {#if vorhanden.length}
        <div class="hinweis warnung"><i class="fa-solid fa-triangle-exclamation"></i><div>Ersetzt {vorhanden.map((a) => `${ARTEN[a.art].name} ${spanne(a.von, a.bis)}`).join(", ")}.</div></div>
      {/if}
      <div class="pw-arbeitszeit-tage">
        {#each w.tage as t (t.tag)}
          <div class="zeile-wert" class:schwach={t.basisSek === 0}>
            <span>{datum(t.tag, true)} {#if t.feiertag}<span class="pw-arbeitszeit-art ft">{t.feiertag}</span>{:else if t.regel}<span class="pw-arbeitszeit-art halb">{t.regel}</span>{/if}</span>
            <b class="zahl">{t.basisSek ? `${dauer(t.basisSek)} auf ${dauer(t.sollSek)}` : t.grund === "wochenende" ? "Wochenende" : t.grund === "feiertag" ? "Feiertag" : "frei"}</b>
          </div>
        {/each}
      </div>
    </section>

    <section class="bereich pw-arbeitszeit-spaeter">
      <div class="etikett">Brückentage</div>
      <p class="schwach klein">Ein Urlaubstag zwischen Feiertag und Wochenende, in {k.bundesland}.</p>
      {#each bruecken as b (b.tag)}
        <div class="pw-arbeitszeit-bruecke">
          <i class="fa-solid fa-bridge"></i>
          <div><b>{datum(b.tag, true)}{b.tag.slice(0, 4)}</b><span class="schwach klein">neben {b.feiertag}: 1 Urlaubstag, {b.frei} Tage frei</span></div>
          <button class="knopf klein" onclick={() => bruecke(b.tag)}>Übernehmen</button>
        </div>
      {:else}
        <p class="schwach">Bis Ende {jahr + 1} keine Brückentage.</p>
      {/each}
    </section>
  </div>
</div>
