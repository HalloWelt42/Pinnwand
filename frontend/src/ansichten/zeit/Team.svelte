<script lang="ts">
  // Team: Anwesenheit und Auslastung der Mitglieder eines Boards als Matrix Personen mal Tage, mit umschaltbaren Ebenen.
  // Nur Boards mit dem Modul Arbeitszeit; wen du siehst, sagt der Server: mit dem Recht "Abwesenheiten sehen" in diesem
  // Board alle Mitglieder, sonst nur dich. Stunden sind die Tagessummen der Person aus allen Boards, wie der Server sie
  // liefert, ohne Einzelheiten; das Soll rechnet die Ansicht aus den Zeitkonten und Abwesenheiten im Zustand. Geladen
  // wird beim Öffnen und beim Wechsel von Board oder Zeitraum.
  import { seitenFehler } from "appkern-oberflaeche";
  import { darf, sollTag, teamTage, type TeamTage } from "../../daten/abfragen";
  import { datum, dauer, spanne, tageZahl } from "../../daten/format";
  import { ICH } from "../../daten/ich";
  import { konto, stand } from "../../daten/stand.svelte";
  import { uhr } from "../../daten/uhr.svelte";
  import Person from "../../board/Person.svelte";
  import type { AbwesenheitArt } from "../../modell";
  import { ARTEN, artName, fassungAm } from "../../regeln/arbeitszeit";
  import { modulAn } from "../../regeln/board";
  import { istWochenende, kalenderwoche, montagVon, plusTage, tageVon } from "../../regeln/tage";
  import { boardPfad } from "../../weg.svelte";

  const heute = $derived(uhr.heute);
  const boards = $derived(stand.boards.filter((b) => b.mitglieder.some((m) => m.konto === ICH) && modulAn(b, "arbeitszeit", stand.moduleDa)));
  // svelte-ignore state_referenced_locally
  let boardId = $state(boards[0]?.id ?? "");
  const b = $derived(boards.find((x) => x.id === boardId) ?? boards[0]);
  const recht = $derived(!!b && darf(b, "abwesenheit.sehen"));
  const rolleName = $derived(b?.rollen.find((r) => r.id === b.mitglieder.find((m) => m.konto === ICH)?.rolle)?.name ?? "");

  let start = $state(plusTage(montagVon(uhr.heute), -14));
  const WOCHEN = 4;
  const tage = $derived(tageVon(start, plusTage(start, WOCHEN * 7 - 1)));
  const kws = $derived(Array.from({ length: WOCHEN }, (_, i) => plusTage(start, i * 7)));

  // Tagessummen vom Server; eine noch laufende Anfrage gilt nach einem Wechsel nicht mehr
  let team = $state<TeamTage | null>(null);
  let fehler = $state("");
  $effect(() => {
    const id = b?.id, von = tage[0], bis = tage[tage.length - 1];
    if (!id) return;
    const halt = new AbortController();
    teamTage(id, von, bis, halt.signal).then(
      (t) => { team = t; fehler = ""; },
      (f) => { if (!halt.signal.aborted) fehler = seitenFehler(f); },
    );
    return () => halt.abort();
  });
  /** gebuchte Sekunden einer Person an einem Tag, aus allen Boards */
  const ist = (p: string, t: string): number => team?.ist[p]?.[t] ?? 0;

  const LEGENDE: AbwesenheitArt[] = ["urlaub", "krank", "frei", "fortbildung"];
  let ebenen = $state({ anwesenheit: true, feiertage: true, stunden: false, auslastung: false });
  const EBENEN = [
    ["anwesenheit", "Anwesenheit", "fa-user-check", "Wer da ist und wer fehlt, mit Art der Abwesenheit"],
    ["feiertage", "Feiertage", "fa-star", "Feiertage im Bundesland jeder Person"],
    ["stunden", "Stunden", "fa-clock", "Gebuchte Stunden je Tag aus allen Boards"],
    ["auslastung", "Auslastung", "fa-gauge", "Gebuchte Stunden im Verhältnis zum Soll des Tags"],
  ] as const;
  function umschalten(e: keyof typeof ebenen): void {
    const an = !ebenen[e];
    ebenen = { ...ebenen, [e]: an, ...(an && e === "stunden" ? { auslastung: false } : {}), ...(an && e === "auslastung" ? { stunden: false } : {}) };
  }

  const hatKonto = (id: string) => !!fassungAm(stand.zeitkonten, id, heute);
  /** wen der Server zeigt, mit Zeitkonto; ohne Recht nur du */
  const personen = $derived((team?.personen ?? []).filter(hatKonto));
  const ohneKonto = $derived((team?.personen ?? []).filter((id) => !hatKonto(id)).map((id) => konto(id).name));

  interface ZelleInfo { klasse: string; text: string; titel: string; anteil?: number }
  function zelle(p: string, t: string): ZelleInfo {
    const s = sollTag(p, t);
    const was = `${konto(p).name}, ${spanne(t, t)}`;
    if (!s) return { klasse: "frei", text: "", titel: was };
    const gebucht = t <= heute ? ist(p, t) : 0;
    if (ebenen.feiertage && s.feiertag) return { klasse: "ft", text: "FT", titel: `${was}: ${s.feiertag}` };
    if (ebenen.anwesenheit && s.abwesenheit && (s.basisSek > 0 || s.abwesenheit.art !== "frei")) {
      const a = s.abwesenheit;
      const halb = a.anteil === 0.5;
      return { klasse: `art-${a.art}${halb ? " halbtag" : ""}`, text: `${halb ? "½" : ""}${ARTEN[a.art].kurz}`,
               titel: `${was}: ${artName(a)}${a.notiz ? `, ${a.notiz}` : ""}${gebucht ? `, gebucht ${dauer(gebucht)}` : ""}` };
    }
    if (s.basisSek === 0 && !gebucht) return { klasse: "frei", text: "", titel: `${was}: ${s.grund === "wochenende" ? "Wochenende" : s.feiertag ?? "kein Arbeitstag"}` };
    if (ebenen.stunden && t <= heute) return { klasse: "stunden", text: gebucht ? dauer(gebucht) : "0:00", titel: `${was}: ${dauer(gebucht)} gebucht`, anteil: Math.min(1, gebucht / (8 * 3600)) };
    if (ebenen.auslastung && t <= heute && s.sollSek > 0) {
      const r = gebucht / s.sollSek;
      return { klasse: r > 1.05 ? "ueber" : r < 0.9 ? "unter" : "imsoll", text: `${Math.round(r * 100)}`, titel: `${was}: ${Math.round(r * 100)} % vom Soll (${dauer(gebucht)} von ${dauer(s.sollSek)})` };
    }
    if (ebenen.anwesenheit && s.basisSek > 0) return { klasse: t <= heute ? "da" : "geplant", text: "", titel: `${was}: ${t <= heute ? "anwesend" : "eingeplant"}, Soll ${dauer(s.sollSek)}` };
    return { klasse: "", text: "", titel: was };
  }

  function summe(p: string): { ist: number; soll: number; weg: number } {
    let gebucht = 0, sl = 0, weg = 0;
    for (const t of tage) {
      const s = sollTag(p, t);
      if (!s) continue;
      if (s.abwesenheit && s.basisSek > 0) weg += (s.abwesenheit.anteil ?? 1) * (s.regel ? 0.5 : 1);
      if (t <= heute) { gebucht += ist(p, t); sl += s.sollSek; }
    }
    return { ist: gebucht, soll: sl, weg };
  }
</script>

<div class="pw-werkzeuge pw-arbeitszeit-werkzeuge">
  <span class="etikett">Board</span>
  {#each boards as x (x.id)}
    <button class="chip" class:aktiv={x.id === b?.id} onclick={() => (boardId = x.id)}><span class="pw-farbpunkt" data-farbe={x.farbe}></span>{x.name}</button>
  {/each}
  <span class="pw-arbeitszeit-trenner"></span>
  <button class="knopf symbol klein" title="Vier Wochen früher" onclick={() => (start = plusTage(start, -7 * WOCHEN))}><i class="fa-solid fa-chevron-left"></i></button>
  <span class="pw-arbeitszeit-zeitraum zahl">{datum(tage[0])} bis {datum(tage[tage.length - 1])}{tage[tage.length - 1].slice(0, 4)}</span>
  <button class="knopf symbol klein" title="Vier Wochen später" onclick={() => (start = plusTage(start, 7 * WOCHEN))}><i class="fa-solid fa-chevron-right"></i></button>
  {#if !tage.includes(heute)}<button class="knopf klein" onclick={() => (start = plusTage(montagVon(heute), -14))}>Heute</button>{/if}
  <div class="rechts">
    <span class="etikett">Ebenen</span>
    {#each EBENEN as [id, name, symbol, titel] (id)}
      <button class="chip" class:aktiv={ebenen[id]} aria-pressed={ebenen[id]} title={titel} onclick={() => umschalten(id)}><i class="fa-solid {symbol}"></i>{name}</button>
    {/each}
  </div>
</div>

<div class="rollfeld">
  {#if b && !recht}
    <div class="hinweis warnung pw-arbeitszeit-recht"><i class="fa-solid fa-user-lock"></i>
      <div><b>Nur deine Zeile.</b> In {b.name} hast du die Rolle {rolleName}; ihr fehlt das Recht "Abwesenheiten sehen". Besitzer des Boards
        vergeben es unter Rollen und Rechte.</div>
      <span class="rechts"><a class="knopf klein" href={boardPfad(b.kuerzel, "einstellungen/rollen")}>Rollen ansehen</a></span>
    </div>
  {/if}
  {#if fehler}
    <div class="hinweis warnung"><i class="fa-solid fa-triangle-exclamation"></i><div>Die Stunden des Teams ließen sich nicht laden: {fehler}</div></div>
  {/if}
  <div class="pw-arbeitszeit-matrix-raum">
    <table class="pw-arbeitszeit-matrix">
      <colgroup><col class="person" />{#each tage as t (t)}<col />{/each}</colgroup>
      <thead>
        <tr class="kw">
          <th></th>
          {#each kws as m (m)}<th colspan="7">KW {kalenderwoche(m)}</th>{/each}
        </tr>
        <tr class="tage">
          <th class="person">Person</th>
          {#each tage as t (t)}
            <th class:heute={t === heute} class:we={istWochenende(t)} title={spanne(t, t)}>
              <span>{datum(t, true).slice(0, 2)}</span><b class="zahl">{Number(t.slice(8))}</b></th>
          {/each}
        </tr>
      </thead>
      <tbody>
        {#each personen as p (p)}
          {@const sm = summe(p)}
          <tr>
            <th class="person" scope="row">
              <span class="wer"><Person id={p} /><span class="name">{konto(p).name}</span></span>
              <small class="zahl" title="Gebucht bis heute im Zeitraum, dazu das Soll bis heute">{dauer(sm.ist)} von {dauer(sm.soll)}</small>
              {#if sm.weg}<small title="Tage mit Abwesenheit im ganzen Zeitraum">{tageZahl(sm.weg)} {sm.weg === 1 ? "Tag" : "Tage"} abwesend</small>{/if}
            </th>
            {#each tage as t (t)}
              {@const z = zelle(p, t)}
              <td class="{z.klasse}" class:heute={t === heute} title={z.titel} style={z.anteil !== undefined ? `--anteil: ${Math.round(12 + z.anteil * 50)}%` : ""}>{z.text}</td>
            {/each}
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
  <ul class="pw-arbeitszeit-legende waagerecht">
    {#if ebenen.anwesenheit}
      <li><span class="muster da"></span>anwesend</li>
      {#each LEGENDE as a (a)}<li><span class="muster art-{a}">{ARTEN[a].kurz}</span>{ARTEN[a].name}</li>{/each}
      <li><span class="muster art-urlaub halbtag">½U</span>{artName({ art: "urlaub", anteil: 0.5 })}</li>
    {/if}
    {#if ebenen.feiertage}<li><span class="muster ft">FT</span>Feiertag</li>{/if}
    {#if ebenen.stunden}<li><span class="muster stunden"></span>gebuchte Stunden (kräftiger ist mehr)</li>{/if}
    {#if ebenen.auslastung}
      <li><span class="muster unter">%</span>unter 90 % vom Soll</li><li><span class="muster imsoll">%</span>im Soll</li><li><span class="muster ueber">%</span>über 105 %</li>
    {/if}
    <li><span class="muster frei"></span>Wochenende, kein Arbeitstag</li>
  </ul>
  {#if ohneKonto.length}<p class="schwach klein">Ohne Zeitkonto und darum nicht in der Matrix: {ohneKonto.join(", ")}.</p>{/if}
</div>
