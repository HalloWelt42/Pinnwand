<script lang="ts">
  // Urlaub und Abwesenheit: links eintragen (von, bis, Art, halber Tag, Notiz) und die Liste des Jahres mit ihrer Wirkung
  // auf das Soll, rechts das Ergebnis der Eingabe Tag für Tag und Brückentage als Vorschlag. Wochenenden und Feiertage
  // zählen nie als Urlaubstag; wo sich eine vorhandene Abwesenheit überschneidet, wird sie ersetzt, ihre übrigen Tage bleiben. Arbeitszeit zeigt
  // diese Ansicht nur mit Zeitkonto.
  import { urlaub } from "../../daten/abfragen";
  import { eintragen as abwesenheitEintragen, entfernen } from "../../daten/anwendung/abwesenheiten.svelte";
  import { datum, dauer, spanne, tageZahl } from "../../daten/format";
  import { ICH } from "../../daten/ich";
  import { stand } from "../../daten/stand.svelte";
  import { uhr } from "../../daten/uhr.svelte";
  import type { Abwesenheit, AbwesenheitArt } from "../../modell";
  import { ARTEN, artName, brueckentage, fassungAm, imZeitraum, wirkung } from "../../regeln/arbeitszeit";
  import DatumFeld from "../../teile/DatumFeld.svelte";

  const heute = $derived(uhr.heute);
  const jahr = $derived(Number(heute.slice(0, 4)));
  let von = $state(uhr.heute);
  let bis = $state(uhr.heute);
  let art = $state<AbwesenheitArt>("urlaub");
  let halb = $state(false);
  let notiz = $state("");
  const WAHL: AbwesenheitArt[] = ["urlaub", "krank", "frei", "fortbildung"];

  const gueltig = $derived(von <= bis);
  /** die Eingabe als geplante Abwesenheit, nur zur Vorschau der Wirkung */
  const neu = $derived<Abwesenheit>({ id: "vorschau", konto: ICH, von, bis: gueltig ? bis : von, art, anteil: halb ? 0.5 : undefined, notiz: notiz || undefined });
  const k = $derived(fassungAm(stand.zeitkonten, ICH, von)!);
  const w = $derived(wirkung(k, neu));
  /** was die neue Abwesenheit von vorhandenen ersetzt: nur ihr Teil im neuen Zeitraum, die übrigen Tage bleiben */
  const vorhanden = $derived(stand.abwesenheiten.filter((a) => a.konto === ICH && a.von <= neu.bis && a.bis >= neu.von)
    .map((a) => imZeitraum(a, neu.von, neu.bis)));
  const ersetzt = $derived(vorhanden.reduce((s, a) => s + wirkung(k, a).urlaubstage, 0));
  const u = $derived(urlaub(ICH)!);
  const liste = $derived(stand.abwesenheiten.filter((a) => a.konto === ICH && a.bis.slice(0, 4) >= String(jahr)).slice().sort((a, b) => a.von.localeCompare(b.von)));
  const kHeute = $derived(fassungAm(stand.zeitkonten, ICH, heute)!);
  const bruecken = $derived(brueckentage(kHeute, heute, `${jahr + 1}-12-31`));

  /** Eintragen; die Notiz leert sich erst, wenn der Server eingetragen hat */
  async function eintragen(): Promise<void> {
    if (!gueltig || w.arbeitstage === 0) return;
    if (await abwesenheitEintragen({ von: neu.von, bis: neu.bis, art: neu.art, anteil: neu.anteil, notiz: neu.notiz })) notiz = "";
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
      {#if art !== "frei"}
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
            {#each liste as a (a.id)}
              {@const wa = wirkung(fassungAm(stand.zeitkonten, ICH, a.von)!, a)}
              <tr class:spaeter={a.von > heute}>
                <td>{spanne(a.von, a.bis)} {#if a.von > heute}<span class="zustand wartet">geplant</span>{/if}</td>
                <td data-titel="Art"><span class="pw-arbeitszeit-art art-{a.art}"><i class="fa-solid {ARTEN[a.art].symbol}"></i>{artName(a)}</span></td>
                <td class="zahl" data-titel="Arbeitstage">{tageZahl(wa.arbeitstage)}</td>
                <td class="zahl" data-titel="Urlaub">{wa.urlaubstage ? tageZahl(wa.urlaubstage) : ""}</td>
                <td class="zahl" data-titel="Soll" title={ARTEN[a.art].wirkung}>{wa.sollSek ? `-${dauer(wa.sollSek)}` : "bleibt"}</td>
                <td data-titel="Notiz">{a.notiz ?? ""}</td>
                <td>{#if a.von > heute}<button class="knopf ohne symbol klein" title="Entfernen (Rückgängig möglich)" onclick={() => entfernen(a.id)}><i class="fa-solid fa-xmark"></i></button>{/if}</td>
              </tr>
            {:else}
              <tr><td colspan="7" class="schwach">In diesem Jahr ist noch nichts eingetragen.</td></tr>
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
          <div class="zeile-wert"><span>Frei verplanbar</span><b class="zahl" class:minus={u.rest + ersetzt - w.urlaubstage < 0}>{tageZahl(u.rest)} auf {tageZahl(u.rest + ersetzt - w.urlaubstage)}</b></div>
        {/if}
      </div>
      {#if vorhanden.length}
        <div class="hinweis warnung"><i class="fa-solid fa-triangle-exclamation"></i><div>Ersetzt {vorhanden.map((a) => `${artName(a)} ${spanne(a.von, a.bis)}`).join(", ")}; übrige Tage davor und danach bleiben.</div></div>
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
      <p class="schwach klein">Ein Urlaubstag zwischen Feiertag und Wochenende, in {kHeute.bundesland}.</p>
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
