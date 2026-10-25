<script lang="ts">
  // Zeiten: dein Stundenzettel der Woche aus allen Boards. Zeilen je Karte, Spalten Mo bis So; jede Zelle ist deine Zeit
  // auf der Karte an dem Tag und direkt änderbar (sekundengenau). Darunter Summe, Soll aus dem Zeitkonto und Differenz.
  // Ein Klick auf einen Tag öffnet seine Einträge rechts als Leiste (wie das Kartendetail über dem Board); "Zeit
  // nachtragen" öffnet dort die Buchung. Der laufende Timer zählt in seiner Zelle mit und lässt sich anhalten.
  import { untrack } from "svelte";
  import { HEUTE, ICH } from "../../beispiel/daten";
  import { datum, dauer } from "../../beispiel/format";
  import { board } from "../../beispiel/stand.svelte";
  import type { Karte } from "../../modell";
  import { differenz, wocheText } from "./anzeige";
  import DauerFeld from "./DauerFeld.svelte";
  import KartenName from "./KartenName.svelte";
  import Meldung from "./Meldung.svelte";
  import Nachtragen from "./Nachtragen.svelte";
  import { ARTEN, montagDer, plusTage, tageVonBis } from "./regeln";
  import { anhalten, eintraegeVon, istAm, karteVon, laufend, laufendAm, saldo, setzeTageszeit, soll, starten, zeit } from "./stand.svelte";
  import { TAGESREST } from "./daten";
  import TagLeiste from "./TagLeiste.svelte";

  let { entwurf = "" }: { entwurf?: string } = $props();

  type Leiste = { art: "tag"; tag: string } | { art: "nachtragen"; tag: string } | null;
  // vorgeführte Zustände: Einträge eines Tags (Fr der Vorwoche), Nachtragen, Rückfrage nach dem Deckel von 12 Stunden
  const START: Record<string, { montag: string; leiste: Leiste }> = {
    tag: { montag: "2026-10-19", leiste: { art: "tag", tag: "2026-10-23" } },
    deckel: { montag: "2026-10-19", leiste: { art: "tag", tag: "2026-10-22" } },
    nachtragen: { montag: montagDer(HEUTE), leiste: { art: "nachtragen", tag: plusTage(HEUTE, -1) } },
  };
  // svelte-ignore state_referenced_locally
  const start = START[entwurf] ?? { montag: montagDer(HEUTE), leiste: null };
  let montag = $state(start.montag);
  let leiste = $state<Leiste>(start.leiste);
  let vorschau = $state<{ karte: string; tag: string; sek: number } | null>(null);

  // Rückfrage nach dem Deckel vorführen: die Sitzung vom Do 22.10. lief 12:30 Std.; gebucht sind die ersten 12, bis
  // du das Ende angibst. Beim Verlassen des Zustands gilt wieder der Stand nach der Antwort (Ende 00:25).
  $effect(() => {
    if (entwurf !== "deckel") return;
    return untrack(() => {
      const fr = zeit.eintraege.find((e) => e.id === "m14"), dor = zeit.eintraege.find((e) => e.id === "m13");
      if (!fr || !dor) return;
      const alt = { bis: fr.bis, sekunden: fr.sekunden };
      const gedeckelt = { spanne: "von Do 22.10. 19:10 bis Fr 23.10. 07:40", sekunden: 12 * 3600 + 1800 };
      fr.bis = "07:10"; fr.sekunden = 7 * 3600 + 600; fr.gedeckelt = gedeckelt; dor.gedeckelt = gedeckelt;
      return () => untrack(() => {
        const f = zeit.eintraege.find((e) => e.id === "m14"), d = zeit.eintraege.find((e) => e.id === "m13");
        if (f?.gedeckelt) { f.bis = alt.bis; f.sekunden = alt.sekunden; f.gedeckelt = undefined; }
        if (d) d.gedeckelt = undefined;
      });
    });
  });

  const tage = $derived(tageVonBis(montag, plusTage(montag, 6)));
  const lauf = $derived(laufend(ICH));
  const eintraege = $derived(eintraegeVon(ICH, montag, plusTage(montag, 6)));

  interface Zeile { karte: Karte; sek: Record<string, number>; woche: number; offen: boolean }
  const zeilen = $derived.by(() => {
    const ids = new Set(eintraege.map((e) => e.karte));
    if (lauf && tage.includes(lauf.seit.slice(0, 10))) ids.add(lauf.karte.id);
    if (vorschau && tage.includes(vorschau.tag)) ids.add(vorschau.karte);
    const out: Zeile[] = [];
    for (const id of ids) {
      const k = karteVon(id);
      if (!k) continue;
      const sek: Record<string, number> = {};
      for (const t of tage) sek[t] = eintraege.filter((e) => e.karte === id && e.datum === t).reduce((s, e) => s + e.sekunden, 0) + laufendAm(ICH, t, id);
      const b = board(k.board);
      const offen = !b.spalten.find((s) => s.id === k.spalte)?.erledigt && k.art === "arbeit" && b.module.zeiterfassung;
      out.push({ karte: k, sek, woche: Object.values(sek).reduce((a, x) => a + x, 0), offen });
    }
    return out.sort((a, b) => board(a.karte.board).name.localeCompare(board(b.karte.board).name)
      || Number(a.karte.schluessel.split("-")[1]) - Number(b.karte.schluessel.split("-")[1]));
  });
  /** Zeit dieser Tage, die die Entwürfe nur als Tagessumme kennen (vor KW 43) */
  const rest = $derived(Object.fromEntries(tage.map((t) => [t, TAGESREST[ICH]?.[t] ?? 0])));
  const mitRest = $derived(Object.values(rest).some((s) => s > 0));

  const istTag = $derived(Object.fromEntries(tage.map((t) => [t, istAm(ICH, t)])));
  const sollTag = $derived(Object.fromEntries(tage.map((t) => [t, soll(ICH, t)!])));
  const istWoche = $derived(tage.reduce((s, t) => s + istTag[t], 0));
  const sollWoche = $derived(tage.reduce((s, t) => s + sollTag[t].sollSek, 0));
  const bisHeute = $derived(tage.filter((t) => t <= HEUTE));
  const diffBisHeute = $derived(bisHeute.reduce((s, t) => s + istTag[t] - sollTag[t].sollSek, 0));
  const gestern = plusTage(HEUTE, -1);
  const ueberstunden = $derived(saldo(ICH, gestern));

  /** Kopf einer Tagesspalte: Wochentag und Datum, darunter in Worten, was das Soll ändert (das Soll selbst steht unten) */
  function sollText(t: string): { wort: string; farbe: string } {
    const s = sollTag[t];
    if (s.grund === "feiertag") return { wort: s.feiertag ?? "Feiertag", farbe: "rose" };
    if (s.abwesenheit) return { wort: `${ARTEN[s.abwesenheit.art].knapp} ${s.sollSek ? dauer(s.sollSek) : ""}`.trim(), farbe: artFarbe(s.abwesenheit.art) };
    if (s.grund === "halbtagsregel") return { wort: `${s.regel} ${dauer(s.sollSek)}`, farbe: "honig" };
    if (s.grund === "wochenende" || s.grund === "arbeitsfrei") return { wort: s.feiertag ?? (s.grund === "wochenende" ? "frei" : "arbeitsfrei"), farbe: s.feiertag ? "rose" : "" };
    return { wort: "", farbe: "" };
  }

  function artFarbe(art: string): string {
    return { urlaub: "himmel", halbtag: "himmel", krank: "koralle", frei: "sand", fortbildung: "violett", feiertag: "rose" }[art] ?? "";
  }

  function frei(t: string): boolean {
    const s = sollTag[t];
    return s.sollSek === 0;
  }

  function woche(n: number): void {
    montag = plusTage(montag, 7 * n);
    vorschau = null;
  }

  function zelleGesetzt(karteId: string, t: string, sek: number): void {
    setzeTageszeit(karteId, t, sek);
  }
</script>

<div class="rahmen-kopf">
  <div class="seitenkopf pw-zeiten-kopf">
    <h1>Zeiten</h1>
    <div class="pw-zeiten-woche" aria-label="Woche wählen">
      <button class="knopf symbol klein" title="Vorige Woche" onclick={() => woche(-1)}><i class="fa-solid fa-chevron-left"></i></button>
      <span class="text"><b>{wocheText(montag).split(",")[0]}</b><span>{wocheText(montag).split(", ")[1]}</span></span>
      <button class="knopf symbol klein" title="Nächste Woche" onclick={() => woche(1)}><i class="fa-solid fa-chevron-right"></i></button>
      {#if montag !== montagDer(HEUTE)}<button class="knopf klein" onclick={() => { montag = montagDer(HEUTE); }}>Diese Woche</button>{/if}
    </div>
    <div class="aktionen">
      <button class="knopf haupt" onclick={() => (leiste = { art: "nachtragen", tag: HEUTE })}><i class="fa-solid fa-plus"></i>Zeit nachtragen</button>
    </div>
    <div class="unterzeile">Deine gebuchte Zeit aus allen Boards; das Soll kommt aus deinem Zeitkonto. Zellen direkt ändern, ein Tag zeigt seine Einträge.</div>
  </div>
  <div class="kennzahlen">
    <div class="kennzahl"><span>Woche</span><b>{dauer(istWoche)}</b><small>von {dauer(sollWoche)} Soll</small></div>
    <div class="kennzahl" class:erfolg={bisHeute.length > 0 && diffBisHeute >= 0}>
      <span>{tage.includes(HEUTE) ? "Bis heute" : "Differenz"}</span><b>{differenz(diffBisHeute)}</b>
      <small>{!bisHeute.length ? "Woche liegt noch vor dir" : tage.includes(HEUTE) ? `Soll bis heute ${dauer(bisHeute.reduce((s, t) => s + sollTag[t].sollSek, 0))}` : "Ist minus Soll der Woche"}</small></div>
    <a class="kennzahl pw-zeiten-verweis" href="/arbeitszeit" title="Zeitkonto öffnen"><span>Überstunden</span><b>{differenz(ueberstunden)}</b><small>Stand {datum(gestern, true)}</small></a>
    {#if lauf}
      <div class="kennzahl laeuft pw-zeiten-lauf" title="Dein Timer (einer je Person) läuft seit {lauf.seit.slice(11, 16)}">
        <span><i class="fa-solid fa-circle-play"></i> Läuft seit {lauf.seit.slice(11, 16)}</span>
        <b>{dauer(laufendAm(ICH, lauf.seit.slice(0, 10)), true)}</b>
        <small>{lauf.karte.schluessel} {lauf.karte.titel}</small>
        <button class="knopf klein" title="Anhalten und die Sitzung auf ihren Tag buchen" onclick={anhalten}><i class="fa-solid fa-stop"></i>Anhalten</button>
      </div>
    {/if}
  </div>
</div>

<div class="pw-zeiten-raum" class:mit-leiste={!!leiste}>
  <div class="rollfeld">
    <div class="pw-zeiten-blatt">
      <table class="tabelle pw-zeiten-tabelle">
        <colgroup><col class="karte" />{#each tage as t (t)}<col class="tag" />{/each}<col class="summe" /></colgroup>
        <thead>
          <tr>
            <th>Karte</th>
            {#each tage as t (t)}
              {@const st = sollText(t)}
              <th class="tag" class:heute={t === HEUTE} class:frei={frei(t)} class:offen={leiste?.art === "tag" && leiste.tag === t}>
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
          {#each zeilen as z (z.karte.id)}
            <tr>
              <td class="pw-zeiten-kartenzelle">
                {#if lauf?.karte.id === z.karte.id}
                  <button class="pw-timer laeuft" title="Dein Timer läuft: anhalten und buchen" onclick={anhalten}><i class="fa-solid fa-pause"></i></button>
                {:else if z.offen}
                  <button class="pw-timer" title="Timer starten (ein laufender Timer hält dabei an und bucht)" onclick={() => starten(z.karte.id)}><i class="fa-solid fa-play"></i></button>
                {:else}
                  <span class="pw-zeiten-ohne-timer" title="Erledigt: nachtragen geht, ein Timer nicht"></span>
                {/if}
                <KartenName karte={z.karte} zeilen={2} />
              </td>
              {#each tage as t (t)}
                {@const laeuftHier = lauf?.karte.id === z.karte.id && lauf.seit.slice(0, 10) === t}
                <td class="pw-zeiten-zelle" class:heute={t === HEUTE} class:frei={frei(t)}
                    class:vorschau={vorschau?.karte === z.karte.id && vorschau.tag === t}>
                  {#if laeuftHier}
                    <span class="pw-zeiten-laeuft" title="Timer läuft seit {lauf!.seit.slice(11, 16)}; zum Ändern erst anhalten">
                      <span class="punkt lebt"></span>{dauer(z.sek[t])}</span>
                  {:else if vorschau?.karte === z.karte.id && vorschau.tag === t}
                    <span class="pw-zeiten-neu" title="Vorschau der Buchung">{dauer(z.sek[t] + vorschau.sek)}</span>
                  {:else}
                    <DauerFeld sek={z.sek[t]} onwert={(s) => zelleGesetzt(z.karte.id, t, s)}
                               titel="Deine Zeit auf {z.karte.schluessel} am {datum(t, true)}: mehr bucht die Differenz auf diesen Tag, weniger kürzt deine jüngsten Einträge des Tags" />
                  {/if}
                </td>
              {/each}
              <td class="zahl pw-zeiten-woche-summe">{dauer(z.woche)}</td>
            </tr>
          {/each}
          {#if mitRest}
            <tr class="pw-zeiten-rest">
              <td title="Diese Tage führen die Entwürfe nur als Summe; in der App stehen hier die einzelnen Karten"><span class="schwach">Weitere Karten</span></td>
              {#each tage as t (t)}<td class="zahl" class:frei={frei(t)}>{rest[t] ? dauer(rest[t]) : ""}</td>{/each}
              <td class="zahl">{dauer(Object.values(rest).reduce((a, x) => a + x, 0))}</td>
            </tr>
          {/if}
          {#if !zeilen.length && !mitRest}
            <tr><td colspan="9" class="schwach">In dieser Woche ist noch keine Zeit gebucht.</td></tr>
          {/if}
        </tbody>
        <tfoot>
          <tr class="summe">
            <td>Summe</td>
            {#each tage as t (t)}<td class="zahl" class:heute={t === HEUTE} class:frei={frei(t)}>{istTag[t] ? dauer(istTag[t]) : ""}</td>{/each}
            <td class="zahl">{dauer(istWoche)}</td>
          </tr>
          <tr class="soll">
            <td>Soll</td>
            {#each tage as t (t)}<td class="zahl" class:heute={t === HEUTE} class:frei={frei(t)}>{dauer(sollTag[t].sollSek)}</td>{/each}
            <td class="zahl">{dauer(sollWoche)}</td>
          </tr>
          <tr class="differenz">
            <td>Differenz</td>
            {#each tage as t (t)}
              {@const d = istTag[t] - sollTag[t].sollSek}
              <td class="zahl" class:heute={t === HEUTE} class:frei={frei(t)} class:plus={t < HEUTE && d > 0} class:minus={t < HEUTE && d < 0}
                  title={t === HEUTE ? "Der Tag läuft noch" : ""}>{t > HEUTE || (!istTag[t] && !sollTag[t].sollSek) ? "" : t === HEUTE ? (d < 0 ? `noch ${dauer(-d)}` : differenz(d)) : differenz(d)}</td>
            {/each}
            <td class="zahl" title="Differenz bis heute">{differenz(diffBisHeute)}</td>
          </tr>
        </tfoot>
      </table>
    </div>
  </div>

  {#if leiste?.art === "tag"}
    <TagLeiste tag={leiste.tag} deckel={entwurf === "deckel"} schliessen={() => (leiste = null)}
               tagWechseln={(t) => { leiste = { art: "tag", tag: t }; montag = montagDer(t); }}
               nachtragen={(t) => (leiste = { art: "nachtragen", tag: t })} />
  {:else if leiste?.art === "nachtragen"}
    <Nachtragen tag={leiste.tag} vorfuehren={entwurf === "nachtragen"} schliessen={() => { leiste = null; vorschau = null; }}
                vorschauSetzen={(v) => { vorschau = v; if (v) montag = montagDer(v.tag); }} />
  {/if}
  <Meldung />
</div>
