<script lang="ts">
  // Zeiten: dein Stundenzettel der Woche aus allen Boards. Zeilen je Karte, Spalten Mo bis So; jede Zelle ist deine Zeit
  // auf der Karte an dem Tag und direkt änderbar (sekundengenau). Bestätigte Termine stehen als eigene Zeile mit ihrem
  // Titel; ihre Zeit ändert sich nicht in der Zelle, gelöscht wird sie in den Einträgen des Tags wie jeder eigene
  // Eintrag. Darunter Summe, Soll aus dem Zeitkonto und Differenz.
  // Ein Klick auf einen Tag öffnet seine Einträge rechts als Leiste (wie das Kartendetail über dem Board); "Zeit
  // nachtragen" öffnet dort die Buchung. Zellen von Karten, die in keinem deiner Boards mehr stehen, bleiben fest; deine
  // Zeit auf Karten, die es nicht mehr gibt, nennt ein Hinweis über allen Wochen und löscht sie mit einem Schritt.
  // Gelesen wird über die Abfragen, geändert nur über die Anwendungsfälle.
  import { Hilfepunkt } from "appkern-oberflaeche";
  import { istAm, kartenName, modulIrgendwo, saldo, sitzungAm, sitzungSek, sollTag, timerErlaubt, timerVon, zeitAufEntferntenKarten,
           zeitSetzbar } from "../../daten/abfragen";
  import { anhalten, fortsetzen, starten } from "../../daten/anwendung/timer.svelte";
  import { setzeTageszeit, zeitAufKartenLoeschen } from "../../daten/anwendung/zeiten.svelte";
  import { datum, dauer, differenz, wocheText } from "../../daten/format";
  import { ICH } from "../../daten/ich";
  import { board, karte, stand } from "../../daten/stand.svelte";
  import { uhr } from "../../daten/uhr.svelte";
  import { ARTEN, fassungAm } from "../../regeln/arbeitszeit";
  import { montagVon, plusTage, tageVon } from "../../regeln/tage";
  import DauerFeld from "../../teile/DauerFeld.svelte";
  import type { Zeiteintrag } from "../../modell";
  import KartenName from "./KartenName.svelte";
  import Nachtragen from "./Nachtragen.svelte";
  import TagLeiste from "./TagLeiste.svelte";
  import TerminName from "./TerminName.svelte";

  type Leiste = { art: "tag"; tag: string } | { art: "nachtragen"; tag: string } | null;
  let montag = $state(montagVon(uhr.heute));
  let leiste = $state<Leiste>(null);
  let vorschau = $state<{ karte: string; tag: string; sek: number } | null>(null);

  const heute = $derived(uhr.heute);
  const tage = $derived(tageVon(montag, plusTage(montag, 6)));
  const timer = $derived(timerVon(ICH));
  const eintraege = $derived(stand.zeiteintraege.filter((e) => e.konto === ICH && e.datum >= montag && e.datum <= plusTage(montag, 6)));
  /** deine Zeit auf Karten, die es nicht mehr gibt, über alle Wochen */
  const entfernt = $derived(zeitAufEntferntenKarten(ICH));
  const entfernteNamen = $derived.by(() => {
    const namen = entfernt.karten.map((id) => kartenName(id).schluessel).filter(Boolean).sort();
    return namen.length > 4 ? `${namen.slice(0, 3).join(", ")} und ${namen.length - 3} weiteren` : namen.join(", ");
  });

  /** laufende Sekunden deines Timers an diesem Tag auf dieser Karte (über Mitternacht zählt jeder Tag seinen Teil) */
  function laufendAm(tag: string, karteId: string): number {
    return timer?.karte === karteId ? sitzungAm(timer, tag) : 0;
  }

  /** Eine Zeile: deine Zeit auf einer Karte oder für einen Termin, je Tag und in der Woche */
  interface Zeile { art: "karte" | "termin"; id: string; sek: Record<string, number>; woche: number }

  function zeile(art: Zeile["art"], id: string, gehoert: (e: Zeiteintrag) => boolean, laufend: (tag: string) => number): Zeile {
    const sek: Record<string, number> = {};
    for (const t of tage) sek[t] = eintraege.filter((e) => gehoert(e) && e.datum === t).reduce((s, e) => s + e.sekunden, 0) + laufend(t);
    return { art, id, sek, woche: Object.values(sek).reduce((a, x) => a + x, 0) };
  }

  const zeilen = $derived.by(() => {
    const karten = new Set(eintraege.flatMap((e) => (e.karte ? [e.karte] : [])));
    if (timer && tage.some((t) => sitzungAm(timer, t) > 0)) karten.add(timer.karte);
    if (vorschau && tage.includes(vorschau.tag)) karten.add(vorschau.karte);
    const termine = new Set(eintraege.flatMap((e) => (e.termin ? [e.termin] : [])));
    const out = [
      ...[...karten].map((id) => zeile("karte", id, (e) => e.karte === id, (t) => laufendAm(t, id))),
      ...[...termine].map((id) => zeile("termin", id, (e) => e.termin === id, () => 0)),
    ];
    // Karten nach Board und Nummer, dann die Termine nach ihrer Zeit; Karten, die nicht mehr im Board stehen (Papierkorb,
    // entfernt, archiviert), zuletzt
    const rang = (z: Zeile) => (z.art === "termin" ? 1 : karte(z.id) ? 0 : 2);
    const nummer = (id: string) => Number(karte(id)?.schluessel.split("-")[1] ?? 0);
    const boardName = (id: string) => { const k = karte(id); return k ? board(k.board).name : ""; };
    const terminZeit = (id: string) => { const t = stand.termine.find((x) => x.id === id); return t ? t.datum + t.von : ""; };
    return out.sort((a, b) => rang(a) - rang(b) || (a.art === "termin"
      ? terminZeit(a.id).localeCompare(terminZeit(b.id))
      : boardName(a.id).localeCompare(boardName(b.id)) || nummer(a.id) - nummer(b.id)));
  });

  const istTag = $derived(Object.fromEntries(tage.map((t) => [t, istAm(ICH, t)])));
  const sollTage = $derived(Object.fromEntries(tage.map((t) => [t, sollTag(ICH, t)])));
  const soll = (t: string) => sollTage[t]?.sollSek ?? 0;
  const istWoche = $derived(tage.reduce((s, t) => s + istTag[t], 0));
  const sollWoche = $derived(tage.reduce((s, t) => s + soll(t), 0));
  const bisHeute = $derived(tage.filter((t) => t <= heute));
  const diffBisHeute = $derived(bisHeute.reduce((s, t) => s + istTag[t] - soll(t), 0));
  const gestern = $derived(plusTage(heute, -1));
  /** Überstunden stehen nur mit Zeitkonto da (ohne wäre jede Stunde eine); zum Zeitkonto führen sie mit dem Modul Arbeitszeit */
  const mitZeitkonto = $derived(!!fassungAm(stand.zeitkonten, ICH, heute));
  const arbeitszeit = $derived(modulIrgendwo("arbeitszeit"));
  const ueberstunden = $derived(saldo(ICH, gestern));

  function artFarbe(art: string): string {
    return { urlaub: "himmel", krank: "koralle", frei: "sand", fortbildung: "violett", feiertag: "rose" }[art] ?? "";
  }

  /** Kopf einer Tagesspalte: in Worten, was das Soll ändert (das Soll selbst steht unten) */
  function sollText(t: string): { wort: string; farbe: string } {
    const s = sollTage[t];
    if (!s) return { wort: "", farbe: "" };
    if (s.grund === "feiertag") return { wort: s.feiertag ?? "Feiertag", farbe: "rose" };
    if (s.abwesenheit) {
      const name = s.abwesenheit.anteil === 0.5 ? `½ ${ARTEN[s.abwesenheit.art].knapp}` : ARTEN[s.abwesenheit.art].knapp;
      return { wort: `${name} ${s.sollSek ? dauer(s.sollSek) : ""}`.trim(), farbe: artFarbe(s.abwesenheit.art) };
    }
    if (s.grund === "halbtagsregel") return { wort: `${s.regel} ${dauer(s.sollSek)}`, farbe: "honig" };
    if (s.grund === "wochenende" || s.grund === "arbeitsfrei") return { wort: s.feiertag ?? (s.grund === "wochenende" ? "frei" : "arbeitsfrei"), farbe: s.feiertag ? "rose" : "" };
    return { wort: "", farbe: "" };
  }

  function frei(t: string): boolean {
    return soll(t) === 0;
  }

  function woche(n: number): void {
    montag = plusTage(montag, 7 * n);
    vorschau = null;
  }
</script>

{#snippet ueberstundenInhalt()}
  <span>Überstunden</span><b>{differenz(ueberstunden)}</b><small>Stand {datum(gestern, true)}</small>
{/snippet}

<div class="rahmen-kopf">
  <div class="seitenkopf pw-zeiten-kopf">
    <h1>Zeiten<Hilfepunkt thema="zeiterfassung" abschnitt="stundenzettel" /></h1>
    <div class="pw-zeiten-woche" aria-label="Woche wählen">
      <button class="knopf symbol klein" title="Vorige Woche" onclick={() => woche(-1)}><i class="fa-solid fa-chevron-left"></i></button>
      <span class="text"><b>{wocheText(montag).split(",")[0]}</b><span>{wocheText(montag).split(", ")[1]}</span></span>
      <button class="knopf symbol klein" title="Nächste Woche" onclick={() => woche(1)}><i class="fa-solid fa-chevron-right"></i></button>
      {#if montag !== montagVon(heute)}<button class="knopf klein" onclick={() => { montag = montagVon(heute); }}>Diese Woche</button>{/if}
    </div>
    <div class="aktionen">
      <button class="knopf haupt" onclick={() => (leiste = { art: "nachtragen", tag: heute })}><i class="fa-solid fa-plus"></i>Zeit nachtragen</button>
    </div>
    <div class="unterzeile">Deine gebuchte Zeit aus allen Boards; das Soll kommt aus deinem Zeitkonto. Zellen direkt ändern, ein Tag zeigt seine Einträge.</div>
  </div>
  <div class="kennzahlen">
    <div class="kennzahl"><span>Woche</span><b>{dauer(istWoche)}</b><small>von {dauer(sollWoche)} Soll</small></div>
    <div class="kennzahl" class:erfolg={bisHeute.length > 0 && diffBisHeute >= 0}>
      <span>{tage.includes(heute) ? "Bis heute" : "Differenz"}</span><b>{differenz(diffBisHeute)}</b>
      <small>{!bisHeute.length ? "Woche liegt noch vor dir" : tage.includes(heute) ? `Soll bis heute ${dauer(bisHeute.reduce((s, t) => s + soll(t), 0))}` : "Ist minus Soll der Woche"}</small></div>
    {#if mitZeitkonto && arbeitszeit}
      <a class="kennzahl pw-zeiten-verweis" href="/arbeitszeit" title="Zeitkonto öffnen">{@render ueberstundenInhalt()}</a>
    {:else if mitZeitkonto}
      <div class="kennzahl">{@render ueberstundenInhalt()}</div>
    {/if}
    {#if timer}
      {@const tk = karte(timer.karte)}
      <div class="kennzahl pw-zeiten-lauf" class:laeuft={!!timer.seit} title={timer.seit ? "Dein Timer (einer je Person) läuft; anhalten und stoppen oben im Kopf oder in seiner Zeile" : "Dein Timer ist angehalten"}>
        <span>{#if timer.seit}<i class="fa-solid fa-circle-play"></i> Läuft seit {timer.seit.slice(11, 16)}{:else}<i class="fa-solid fa-circle-pause"></i> Angehalten{/if}</span>
        <b>{timer.seit ? dauer(sitzungSek(timer), true) : tk?.schluessel ?? ""}</b>
        <small>{tk ? `${tk.schluessel} ${tk.titel}` : ""}</small>
      </div>
    {/if}
  </div>
</div>

<div class="pw-zeiten-raum" class:mit-leiste={!!leiste}>
  <div class="rollfeld">
    {#if entfernt.sekunden}
      <div class="hinweis pw-zeiten-entfernt"><i class="fa-solid fa-eraser"></i>
        <div><b>{dauer(entfernt.sekunden)} Stunden auf gelöschten Karten.</b> Deine Zeit auf {entfernteNamen || "gelöschten Karten"}
          zählt weiter in deine Arbeitszeit, obwohl es die Karten nicht mehr gibt. War es nur ein Versuch, löschst du sie
          hier aus allen Wochen; Rückgängig geht danach.</div>
        <span class="rechts"><button class="knopf klein" onclick={() => zeitAufKartenLoeschen(entfernt.karten)}><i class="fa-solid fa-trash-can"></i>Zeit löschen</button></span>
      </div>
    {/if}
    <div class="pw-zeiten-blatt">
      <table class="tabelle pw-zeiten-tabelle">
        <colgroup><col class="karte" />{#each tage as t (t)}<col class="tag" />{/each}<col class="summe" /></colgroup>
        <thead>
          <tr>
            <th>Karte</th>
            {#each tage as t (t)}
              {@const st = sollText(t)}
              <th class="tag" class:heute={t === heute} class:frei={frei(t)} class:offen={leiste?.art === "tag" && leiste.tag === t}>
                <button class="pw-zeiten-tagknopf" title="Einträge von {datum(t, true)} ansehen" onclick={() => (leiste = { art: "tag", tag: t })}>
                  <span class="wt">{datum(t, true)}</span>
                  {#if st.wort}<span class="soll" data-farbe={st.farbe || undefined} class:getoent={!!st.farbe}>{st.wort}</span>{/if}
                </button>
              </th>
            {/each}
            <th class="zahl">Woche</th>
          </tr>
        </thead>
        <tbody>
          {#each zeilen as z (`${z.art}-${z.id}`)}
            {#if z.art === "termin"}
            <tr>
              <td class="pw-zeiten-kartenzelle">
                <span class="pw-zeiten-ohne-timer" title="Termin: kein Timer; die Zeit kommt aus deiner Bestätigung"></span>
                <TerminName id={z.id} zeilen={2} />
              </td>
              {#each tage as t (t)}
                <td class="pw-zeiten-zelle" class:heute={t === heute} class:frei={frei(t)}>
                  {#if z.sek[t]}<span class="pw-zeiten-fest" title="Bestätigte Zeit des Termins; löschen geht in den Einträgen des Tags">{dauer(z.sek[t])}</span>{/if}
                </td>
              {/each}
              <td class="zahl pw-zeiten-woche-summe">{dauer(z.woche)}</td>
            </tr>
            {:else}
            {@const k = karte(z.id)}
            {@const setzbar = zeitSetzbar(z.id)}
            <tr>
              <td class="pw-zeiten-kartenzelle">
                {#if timer?.karte === z.id && timer.seit}
                  <button class="pw-timer laeuft" title="Dein Timer läuft: anhalten (die Sitzung wird gebucht)" onclick={anhalten}><i class="fa-solid fa-pause"></i></button>
                {:else if timer?.karte === z.id}
                  <button class="pw-timer" title="Dein Timer ist angehalten: fortsetzen" onclick={fortsetzen}><i class="fa-solid fa-play"></i></button>
                {:else if k && timerErlaubt(k)}
                  <button class="pw-timer" title="Timer starten (dein Timer auf einer anderen Karte endet dabei und bucht)" onclick={() => starten(z.id)}><i class="fa-solid fa-play"></i></button>
                {:else}
                  <span class="pw-zeiten-ohne-timer" title="Kein Timer: erledigt, Idee oder nicht mehr im Board; nachtragen geht"></span>
                {/if}
                <KartenName id={z.id} zeilen={2} />
              </td>
              {#each tage as t (t)}
                {@const laeuftHier = laufendAm(t, z.id) > 0}
                {@const neu = vorschau?.karte === z.id && vorschau.tag === t}
                <td class="pw-zeiten-zelle" class:heute={t === heute} class:frei={frei(t)} class:vorschau={neu}>
                  {#if laeuftHier}
                    <span class="pw-zeiten-laeuft" title="Timer läuft seit {timer!.seit!.slice(11, 16)}; zum Ändern erst anhalten">
                      <span class="punkt lebt"></span>{dauer(z.sek[t])}</span>
                  {:else if neu}
                    <span class="pw-zeiten-neu" title="Vorschau der Buchung">{dauer(z.sek[t] + vorschau!.sek)}</span>
                  {:else if !setzbar}
                    {#if z.sek[t]}<span class="pw-zeiten-fest" title="Die Karte steht in keinem deiner Boards mehr (Papierkorb, gelöscht oder Board verlassen); ihre Zeit bleibt fest">{dauer(z.sek[t])}</span>{/if}
                  {:else}
                    <DauerFeld sek={z.sek[t]} onwert={(s) => setzeTageszeit(z.id, t, s)}
                               titel="Deine Zeit auf {k?.schluessel ?? 'der Karte'} am {datum(t, true)}: mehr bucht die Differenz auf diesen Tag, weniger kürzt deine jüngsten Einträge des Tags" />
                  {/if}
                </td>
              {/each}
              <td class="zahl pw-zeiten-woche-summe">{dauer(z.woche)}</td>
            </tr>
            {/if}
          {/each}
          {#if !zeilen.length}
            <tr><td colspan="9" class="schwach">In dieser Woche ist noch keine Zeit gebucht.</td></tr>
          {/if}
        </tbody>
        <tfoot>
          <tr class="summe">
            <td>Summe</td>
            {#each tage as t (t)}<td class="zahl" class:heute={t === heute} class:frei={frei(t)}>{istTag[t] ? dauer(istTag[t]) : ""}</td>{/each}
            <td class="zahl">{dauer(istWoche)}</td>
          </tr>
          <tr class="soll">
            <td>Soll</td>
            {#each tage as t (t)}<td class="zahl" class:heute={t === heute} class:frei={frei(t)}>{dauer(soll(t))}</td>{/each}
            <td class="zahl">{dauer(sollWoche)}</td>
          </tr>
          <tr class="differenz">
            <td>Differenz</td>
            {#each tage as t (t)}
              {@const d = istTag[t] - soll(t)}
              <td class="zahl" class:heute={t === heute} class:frei={frei(t)} class:plus={t < heute && d > 0} class:minus={t < heute && d < 0}
                  title={t === heute ? "Der Tag läuft noch" : ""}>{t > heute || (!istTag[t] && !soll(t)) ? "" : t === heute ? (d < 0 ? `noch ${dauer(-d)}` : differenz(d)) : differenz(d)}</td>
            {/each}
            <td class="zahl" title="Differenz bis heute">{differenz(diffBisHeute)}</td>
          </tr>
        </tfoot>
      </table>
    </div>
  </div>

  {#if leiste?.art === "tag"}
    <TagLeiste tag={leiste.tag} schliessen={() => (leiste = null)}
               tagWechseln={(t) => { leiste = { art: "tag", tag: t }; montag = montagVon(t); }}
               nachtragen={(t) => (leiste = { art: "nachtragen", tag: t })} />
  {:else if leiste?.art === "nachtragen"}
    <Nachtragen tag={leiste.tag} schliessen={() => { leiste = null; vorschau = null; }}
                vorschauSetzen={(v) => { vorschau = v; if (v) montag = montagVon(v.tag); }} />
  {/if}
</div>
