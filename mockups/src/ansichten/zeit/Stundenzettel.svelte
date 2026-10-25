<script lang="ts">
  // Zeiten: dein Stundenzettel der Woche aus allen Boards. Zeilen je Karte, Spalten Mo bis So; jede Zelle ist deine Zeit
  // auf der Karte an dem Tag und direkt änderbar (sekundengenau). Darunter Summe, Soll aus dem Zeitkonto und Differenz.
  // Ein Klick auf einen Tag öffnet seine Einträge rechts als Leiste (wie das Kartendetail über dem Board); "Zeit
  // nachtragen" öffnet dort die Buchung. Gelesen wird über die Abfragen, geändert nur über die Anwendungsfälle.
  import { untrack } from "svelte";
  import { istAm, saldo, sitzungSek, sollTag, timerErlaubt, timerVon } from "../../beispiel/abfragen";
  import { anhalten, fortsetzen, starten } from "../../beispiel/anwendung/timer.svelte";
  import { setzeTageszeit } from "../../beispiel/anwendung/zeiten.svelte";
  import { HEUTE, ICH } from "../../beispiel/daten";
  import { deckelOffen } from "../../beispiel/daten-zeit";
  import { datum, dauer, differenz, wocheText } from "../../beispiel/format";
  import { board, karte, stand, zuruecksetzen } from "../../beispiel/stand.svelte";
  import { ARTEN } from "../../regeln/arbeitszeit";
  import { montagVon, plusTage, tageVon } from "../../regeln/tage";
  import DauerFeld from "../../teile/DauerFeld.svelte";
  import KartenName from "./KartenName.svelte";
  import Nachtragen from "./Nachtragen.svelte";
  import TagLeiste from "./TagLeiste.svelte";

  let { entwurf = "" }: { entwurf?: string } = $props();

  type Leiste = { art: "tag"; tag: string } | { art: "nachtragen"; tag: string } | null;
  let montag = $state(montagVon(HEUTE));
  let leiste = $state<Leiste>(null);
  let vorschau = $state<{ karte: string; tag: string; sek: number } | null>(null);

  // Vorgeführte Zustände richten sich nach dem Ausgangsstand ein, einmal je Entwurf: Einträge eines Tags (Fr der
  // Vorwoche), Nachtragen, und die offene Rückfrage nach dem Deckel (Ausgangsstand mit der Abwandlung deckelOffen).
  $effect(() => {
    const e = entwurf;
    untrack(() => {
      vorschau = null;
      if (e === "tag") { montag = "2026-10-19"; leiste = { art: "tag", tag: "2026-10-23" }; }
      else if (e === "deckel") {
        montag = "2026-10-19"; leiste = { art: "tag", tag: "2026-10-22" };
        zuruecksetzen(deckelOffen);
      } else if (e === "nachtragen") { montag = montagVon(HEUTE); leiste = { art: "nachtragen", tag: plusTage(HEUTE, -1) }; }
      else { montag = montagVon(HEUTE); leiste = null; }
    });
  });

  const tage = $derived(tageVon(montag, plusTage(montag, 6)));
  const timer = $derived(timerVon(ICH));
  const eintraege = $derived(stand.zeiteintraege.filter((e) => e.konto === ICH && e.datum >= montag && e.datum <= plusTage(montag, 6)));

  /** laufende Sekunden deines Timers an diesem Tag auf dieser Karte (der Timer läuft in den Entwürfen nie über Mitternacht) */
  function laufendAm(tag: string, karteId: string): number {
    return timer?.seit && timer.karte === karteId && timer.seit.slice(0, 10) === tag ? sitzungSek(timer) : 0;
  }

  interface Zeile { id: string; sek: Record<string, number>; woche: number }
  const zeilen = $derived.by(() => {
    const ids = new Set(eintraege.map((e) => e.karte));
    if (timer?.seit && tage.includes(timer.seit.slice(0, 10))) ids.add(timer.karte);
    if (vorschau && tage.includes(vorschau.tag)) ids.add(vorschau.karte);
    const out: Zeile[] = [...ids].map((id) => {
      const sek: Record<string, number> = {};
      for (const t of tage) sek[t] = eintraege.filter((e) => e.karte === id && e.datum === t).reduce((s, e) => s + e.sekunden, 0) + laufendAm(t, id);
      return { id, sek, woche: Object.values(sek).reduce((a, x) => a + x, 0) };
    });
    // nach Board und Nummer; Karten, die nicht mehr im Board stehen (Papierkorb, entfernt), zuletzt
    const nummer = (id: string) => Number(karte(id)?.schluessel.split("-")[1] ?? 0);
    const boardName = (id: string) => { const k = karte(id); return k ? board(k.board).name : ""; };
    return out.sort((a, b) => Number(!karte(a.id)) - Number(!karte(b.id)) || boardName(a.id).localeCompare(boardName(b.id)) || nummer(a.id) - nummer(b.id));
  });

  const istTag = $derived(Object.fromEntries(tage.map((t) => [t, istAm(ICH, t)])));
  const sollTage = $derived(Object.fromEntries(tage.map((t) => [t, sollTag(ICH, t)])));
  /** Zeit dieser Tage, die nicht als einzelne Karte im Zettel steht (die Entwürfe führen sie vor KW 43 nur als Summe) */
  const rest = $derived(Object.fromEntries(tage.map((t) => [t, istTag[t] - zeilen.reduce((s, z) => s + z.sek[t], 0)])));
  const mitRest = $derived(Object.values(rest).some((s) => s > 0));
  const soll = (t: string) => sollTage[t]?.sollSek ?? 0;
  const istWoche = $derived(tage.reduce((s, t) => s + istTag[t], 0));
  const sollWoche = $derived(tage.reduce((s, t) => s + soll(t), 0));
  const bisHeute = $derived(tage.filter((t) => t <= HEUTE));
  const diffBisHeute = $derived(bisHeute.reduce((s, t) => s + istTag[t] - soll(t), 0));
  const gestern = plusTage(HEUTE, -1);
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

<div class="rahmen-kopf">
  <div class="seitenkopf pw-zeiten-kopf">
    <h1>Zeiten</h1>
    <div class="pw-zeiten-woche" aria-label="Woche wählen">
      <button class="knopf symbol klein" title="Vorige Woche" onclick={() => woche(-1)}><i class="fa-solid fa-chevron-left"></i></button>
      <span class="text"><b>{wocheText(montag).split(",")[0]}</b><span>{wocheText(montag).split(", ")[1]}</span></span>
      <button class="knopf symbol klein" title="Nächste Woche" onclick={() => woche(1)}><i class="fa-solid fa-chevron-right"></i></button>
      {#if montag !== montagVon(HEUTE)}<button class="knopf klein" onclick={() => { montag = montagVon(HEUTE); }}>Diese Woche</button>{/if}
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
      <small>{!bisHeute.length ? "Woche liegt noch vor dir" : tage.includes(HEUTE) ? `Soll bis heute ${dauer(bisHeute.reduce((s, t) => s + soll(t), 0))}` : "Ist minus Soll der Woche"}</small></div>
    <a class="kennzahl pw-zeiten-verweis" href="/arbeitszeit" title="Zeitkonto öffnen"><span>Überstunden</span><b>{differenz(ueberstunden)}</b><small>Stand {datum(gestern, true)}</small></a>
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
          {#each zeilen as z (z.id)}
            {@const k = karte(z.id)}
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
                <td class="pw-zeiten-zelle" class:heute={t === HEUTE} class:frei={frei(t)} class:vorschau={neu}>
                  {#if laeuftHier}
                    <span class="pw-zeiten-laeuft" title="Timer läuft seit {timer!.seit!.slice(11, 16)}; zum Ändern erst anhalten">
                      <span class="punkt lebt"></span>{dauer(z.sek[t])}</span>
                  {:else if neu}
                    <span class="pw-zeiten-neu" title="Vorschau der Buchung">{dauer(z.sek[t] + vorschau!.sek)}</span>
                  {:else}
                    <DauerFeld sek={z.sek[t]} onwert={(s) => setzeTageszeit(z.id, t, s)}
                               titel="Deine Zeit auf {k?.schluessel ?? 'der Karte'} am {datum(t, true)}: mehr bucht die Differenz auf diesen Tag, weniger kürzt deine jüngsten Einträge des Tags" />
                  {/if}
                </td>
              {/each}
              <td class="zahl pw-zeiten-woche-summe">{dauer(z.woche)}</td>
            </tr>
          {/each}
          {#if mitRest}
            <tr class="pw-zeiten-rest">
              <td title="Diese Tage führen die Entwürfe nur als Summe; in der App stehen hier die einzelnen Karten"><span class="schwach">Weitere Karten</span></td>
              {#each tage as t (t)}<td class="zahl" class:frei={frei(t)}>{rest[t] > 0 ? dauer(rest[t]) : ""}</td>{/each}
              <td class="zahl">{dauer(Object.values(rest).reduce((a, x) => a + Math.max(0, x), 0))}</td>
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
            {#each tage as t (t)}<td class="zahl" class:heute={t === HEUTE} class:frei={frei(t)}>{dauer(soll(t))}</td>{/each}
            <td class="zahl">{dauer(sollWoche)}</td>
          </tr>
          <tr class="differenz">
            <td>Differenz</td>
            {#each tage as t (t)}
              {@const d = istTag[t] - soll(t)}
              <td class="zahl" class:heute={t === HEUTE} class:frei={frei(t)} class:plus={t < HEUTE && d > 0} class:minus={t < HEUTE && d < 0}
                  title={t === HEUTE ? "Der Tag läuft noch" : ""}>{t > HEUTE || (!istTag[t] && !soll(t)) ? "" : t === HEUTE ? (d < 0 ? `noch ${dauer(-d)}` : differenz(d)) : differenz(d)}</td>
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
    <Nachtragen tag={leiste.tag} vorfuehren={entwurf === "nachtragen"} schliessen={() => { leiste = null; vorschau = null; }}
                vorschauSetzen={(v) => { vorschau = v; if (v) montag = montagVon(v.tag); }} />
  {/if}
</div>
