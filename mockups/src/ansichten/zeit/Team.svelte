<script lang="ts">
  // Team: Anwesenheit und Auslastung der Mitglieder eines Boards als Matrix Personen mal Tage, mit umschaltbaren Ebenen.
  // Nur Boards mit dem Modul Arbeitszeit, in denen deine Rolle das Recht "Abwesenheiten sehen" hat; ohne das Recht siehst
  // du nur dich. Stunden sind die Summe je Tag aus dem Zeitkonto der Person (alle Boards), ohne Einzelheiten.
  import { HEUTE, ICH } from "../../beispiel/daten";
  import { datum, dauer } from "../../beispiel/format";
  import { board, konto, stand } from "../../beispiel/stand.svelte";
  import Person from "../../board/Person.svelte";
  import type { Board } from "../../modell";
  import { boardPfad } from "../../weg.svelte";
  import { spanne, tageZahl } from "./anzeige";
  import type { AbwesenheitArt } from "../../modell";
  import { ARTEN, kalenderwoche, montagDer, plusTage, tageVonBis, wochentag } from "./regeln";
  import { istAm, kontoVon, soll } from "./stand.svelte";

  let { entwurf = "" }: { entwurf?: string } = $props();

  function rolleVon(b: Board): string {
    return b.mitglieder.find((m) => m.konto === ICH)?.rolle ?? "";
  }
  /** vorgeführt: dieselbe Ansicht mit einer Rolle ohne das Recht (Werkstatt) */
  // svelte-ignore state_referenced_locally
  const ohneRecht = entwurf === "ohne-recht";
  function darfSehen(b: Board): boolean {
    const rolle = ohneRecht ? "r-kunde" : rolleVon(b);
    return !!b.rollen.find((r) => r.id === rolle)?.rechte.includes("abwesenheit.sehen");
  }
  const boards = $derived(stand.boards.filter((b) => b.module.arbeitszeit && b.mitglieder.some((m) => m.konto === ICH)));
  let boardId = $state("b-prod");
  const b = $derived(board(boardId));
  const recht = $derived(darfSehen(b));
  const rolleName = $derived(b.rollen.find((r) => r.id === (ohneRecht ? "r-kunde" : rolleVon(b)))?.name ?? "");

  let start = $state(plusTage(montagDer(HEUTE), -14));
  const WOCHEN = 4;
  const tage = $derived(tageVonBis(start, plusTage(start, WOCHEN * 7 - 1)));
  const kws = $derived(Array.from({ length: WOCHEN }, (_, i) => plusTage(start, i * 7)));

  const LEGENDE: AbwesenheitArt[] = ["urlaub", "halbtag", "krank", "frei", "fortbildung"];
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

  /** Mitglieder mit Zeitkonto; ohne Recht nur du */
  const personen = $derived(b.mitglieder.map((m) => m.konto).filter((id) => kontoVon(id) && (recht || id === ICH)));
  const ohneKonto = $derived(b.mitglieder.filter((m) => !kontoVon(m.konto)).map((m) => konto(m.konto).name));

  interface ZelleInfo { klasse: string; text: string; titel: string; anteil?: number }
  function zelle(p: string, t: string): ZelleInfo {
    const s = soll(p, t)!;
    const ist = t <= HEUTE ? istAm(p, t) : 0;
    const was = `${konto(p).name}, ${spanne(t, t)}`;
    if (ebenen.feiertage && s.feiertag) return { klasse: "ft", text: "FT", titel: `${was}: ${s.feiertag}` };
    if (ebenen.anwesenheit && s.abwesenheit && (s.basisSek > 0 || s.abwesenheit.art !== "frei")) {
      const a = ARTEN[s.abwesenheit.art];
      return { klasse: `art-${s.abwesenheit.art}`, text: a.kurz, titel: `${was}: ${a.name}${s.abwesenheit.notiz ? `, ${s.abwesenheit.notiz}` : ""}${ist ? `, gebucht ${dauer(ist)}` : ""}` };
    }
    if (s.basisSek === 0 && !ist) return { klasse: "frei", text: "", titel: `${was}: ${s.grund === "wochenende" ? "Wochenende" : s.feiertag ?? "kein Arbeitstag"}` };
    if (ebenen.stunden && t <= HEUTE) return { klasse: "stunden", text: ist ? dauer(ist) : "0:00", titel: `${was}: ${dauer(ist)} gebucht`, anteil: Math.min(1, ist / (8 * 3600)) };
    if (ebenen.auslastung && t <= HEUTE && s.sollSek > 0) {
      const r = ist / s.sollSek;
      return { klasse: r > 1.05 ? "ueber" : r < 0.9 ? "unter" : "imsoll", text: `${Math.round(r * 100)}`, titel: `${was}: ${Math.round(r * 100)} % vom Soll (${dauer(ist)} von ${dauer(s.sollSek)})` };
    }
    if (ebenen.anwesenheit && s.basisSek > 0) return { klasse: t <= HEUTE ? "da" : "geplant", text: "", titel: `${was}: ${t <= HEUTE ? "anwesend" : "eingeplant"}, Soll ${dauer(s.sollSek)}` };
    return { klasse: "", text: "", titel: was };
  }

  function summe(p: string): { ist: number; soll: number; weg: number } {
    let ist = 0, sl = 0, weg = 0;
    for (const t of tage) {
      const s = soll(p, t)!;
      if (s.abwesenheit && s.basisSek > 0) weg += s.regel ? 0.5 : 1;
      if (t <= HEUTE) { ist += istAm(p, t); sl += s.sollSek; }
    }
    return { ist, soll: sl, weg };
  }
</script>

<div class="pw-werkzeuge pw-arbeitszeit-werkzeuge">
  <span class="etikett">Board</span>
  {#each boards as x (x.id)}
    <button class="chip" class:aktiv={x.id === boardId} onclick={() => (boardId = x.id)}><span class="pw-farbpunkt" data-farbe={x.farbe}></span>{x.name}</button>
  {/each}
  <span class="pw-arbeitszeit-trenner"></span>
  <button class="knopf symbol klein" title="Vier Wochen früher" onclick={() => (start = plusTage(start, -7 * WOCHEN))}><i class="fa-solid fa-chevron-left"></i></button>
  <span class="pw-arbeitszeit-zeitraum zahl">{datum(tage[0])} bis {datum(tage[tage.length - 1])}{tage[tage.length - 1].slice(0, 4)}</span>
  <button class="knopf symbol klein" title="Vier Wochen später" onclick={() => (start = plusTage(start, 7 * WOCHEN))}><i class="fa-solid fa-chevron-right"></i></button>
  {#if !tage.includes(HEUTE)}<button class="knopf klein" onclick={() => (start = plusTage(montagDer(HEUTE), -14))}>Heute</button>{/if}
  <div class="rechts">
    <span class="etikett">Ebenen</span>
    {#each EBENEN as [id, name, symbol, titel] (id)}
      <button class="chip" class:aktiv={ebenen[id]} aria-pressed={ebenen[id]} title={titel} onclick={() => umschalten(id)}><i class="fa-solid {symbol}"></i>{name}</button>
    {/each}
  </div>
</div>

<div class="rollfeld">
  {#if !recht}
    <div class="hinweis warnung pw-arbeitszeit-recht"><i class="fa-solid fa-user-lock"></i>
      <div><b>Nur deine Zeile.</b> In {b.name} hast du die Rolle {rolleName}; ihr fehlt das Recht "Abwesenheiten sehen". Besitzer des Boards
        vergeben es unter Rollen und Rechte.</div>
      <span class="rechts"><a class="knopf klein" href={boardPfad(b.kuerzel, "einstellungen/rollen")}>Rollen ansehen</a></span>
    </div>
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
            <th class:heute={t === HEUTE} class:we={wochentag(t) === 0 || wochentag(t) === 6} title={spanne(t, t)}>
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
              <td class="{z.klasse}" class:heute={t === HEUTE} title={z.titel} style={z.anteil !== undefined ? `--anteil: ${Math.round(12 + z.anteil * 50)}%` : ""}>{z.text}</td>
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
    {/if}
    {#if ebenen.feiertage}<li><span class="muster ft">FT</span>Feiertag</li>{/if}
    {#if ebenen.stunden}<li><span class="muster stunden"></span>gebuchte Stunden (kräftiger ist mehr)</li>{/if}
    {#if ebenen.auslastung}
      <li><span class="muster unter">%</span>unter 90 % vom Soll</li><li><span class="muster imsoll">%</span>im Soll</li><li><span class="muster ueber">%</span>über 105 %</li>
    {/if}
    <li><span class="muster frei"></span>Wochenende, kein Arbeitstag</li>
  </ul>
  {#if recht && ohneKonto.length}<p class="schwach klein">Ohne Zeitkonto und darum nicht in der Matrix: {ohneKonto.join(", ")}.</p>{/if}
</div>
