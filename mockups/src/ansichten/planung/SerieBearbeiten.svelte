<script lang="ts">
  // Eine Serie anlegen oder bearbeiten: links tun (Karte, Rhythmus, Teilnehmer, Vorbuchen), rechts das Ergebnis (die
  // Tage der Serie mit ihrem Stand). Ändern zieht nur unberührte Vorbuchungen nach; angefasste Karten, vergangene und
  // bewusst gelöschte Tage bleiben, wie sie sind (M-108, M-109). Pause räumt unberührte Zukunftskarten, Löschen legt
  // unberührte in den Papierkorb und löst Karten mit Zeit von der Serie (M-110). Rückfragen stehen in der Fläche.
  import { untrack } from "svelte";
  import { HEUTE, ICH } from "../../beispiel/daten";
  import { datum, dauer } from "../../beispiel/format";
  import { konto } from "../../beispiel/stand.svelte";
  import Person from "../../board/Person.svelte";
  import type { Board, Kennung, Rhythmus, Serie } from "../../modell";
  import { gehe } from "../../weg.svelte";
  import { STAND } from "./anzeige";
  import PersonenFeld from "./PersonenFeld.svelte";
  import { boardsMitSerien, boardVon, hatRecht, istPausiert, naechstes, plan, regel, rhythmusText, vorkommenListe } from "./plan.svelte";
  import { kalenderwoche, montagVon, plusTage, TAGE_KURZ, TAGE_LANG, tagLang, WOCHE_AB_MONTAG } from "./tage";
  import type { Monatsregel, SerienRegel, Vorkommen } from "./typen";

  let { serieId = "", neu = false, entwurf = "" }: { serieId?: string; neu?: boolean; entwurf?: string } = $props();

  const original = $derived(neu ? undefined : plan.serien.find((x) => x.id === serieId));

  /** Vorschlag einer neuen Serie (in der App: leer bis auf dich als Teilnehmer und die erste Spalte) */
  function neueSerie(): Serie {
    return { id: "neu", board: "b-prod", titel: "Wochenplanung Werkstatt", rhythmus: "woechentlich", tage: [4], uhrzeit: "15:00", dauerMin: 30,
             zielspalte: "s-geplant", teilnehmer: [ICH, "k-jonas"], naechste: "" };
  }
  function neueRegel(): SerienRegel {
    return { serie: "neu", beschreibung: "Aufträge der nächsten Woche, Maschinenbelegung, Material.", labels: ["l-intern"], ab: HEUTE,
             vorlaufTage: 14, wochenendenUeberspringen: false, feiertageUeberspringen: true, auslass: [], beruehrt: [], verworfen: [] };
  }

  let s = $state<Serie>(neueSerie());
  let r = $state<SerienRegel>(neueRegel());
  let dauerText = $state("");
  let abText = $state("");
  let bisText = $state("");
  let loeschenFrage = $state(false);
  let bericht = $state("");

  function laden(): void {
    s = original ? $state.snapshot(original) as Serie : neueSerie();
    r = original ? $state.snapshot(regel(original)) as SerienRegel : neueRegel();
    if (entwurf === "aendern") { s.uhrzeit = "07:45"; s.dauerMin = 20; }
    dauerText = dauer(s.dauerMin * 60);
    abText = tagLang(r.ab);
    bisText = r.bis ? tagLang(r.bis) : "";
    loeschenFrage = entwurf === "loeschen";
    bericht = "";
  }
  // neu laden, wenn Serie oder Entwurf wechseln; was laden() selbst liest und schreibt, zählt nicht als Abhängigkeit
  $effect(() => { void serieId; void neu; void entwurf; untrack(laden); });

  const b = $derived(boardVon(s.board) as Board);
  const darf = $derived(!!b && hatRecht(b, "serien.verwalten"));
  const pausiert = $derived(istPausiert(r));
  const liste = $derived(vorkommenListe(s, r));
  const naechster = $derived(naechstes(s, r));
  const spalten = $derived(b?.spalten.filter((x) => !x.erledigt) ?? []);
  const kandidaten = $derived((b?.mitglieder ?? []).map((m) => ({
    konto: m.konto,
    gesperrt: hatRecht(b, "zeit.buchen", m.konto) ? undefined : `${b.rollen.find((x) => x.id === m.rolle)?.name ?? "Rolle"}: bucht keine Zeit`,
  })));

  function textDauer(t: string): number | undefined {
    const m = t.trim().match(/^(\d{1,2}):(\d{2})$/);
    return m ? Number(m[1]) * 60 + Number(m[2]) : undefined;
  }
  function textTag(t: string): string | undefined {
    const m = t.trim().match(/^(\d{1,2})\.(\d{1,2})\.(\d{4})$/);
    return m ? `${m[3]}-${m[2].padStart(2, "0")}-${m[1].padStart(2, "0")}` : undefined;
  }

  /** Was sich gegenüber der gespeicherten Fassung geändert hat, als kurze Sätze */
  const aenderungen = $derived.by(() => {
    if (!original) return [] as string[];
    const o = original;
    const or = regel(o);
    const a: string[] = [];
    if (s.titel !== o.titel) a.push(`Titel "${s.titel}"`);
    if (s.rhythmus !== o.rhythmus || JSON.stringify(s.tage ?? []) !== JSON.stringify(o.tage ?? []) || r.monatsregel !== or.monatsregel
        || r.monatstag !== or.monatstag || r.wochenendenUeberspringen !== or.wochenendenUeberspringen) a.push(`Rhythmus ${rhythmusText(s, r)}`);
    if (s.uhrzeit !== o.uhrzeit) a.push(`Uhrzeit ${s.uhrzeit || "ganztägig"} statt ${o.uhrzeit || "ganztägig"}`);
    if (s.dauerMin !== o.dauerMin) a.push(`Dauer ${dauer(s.dauerMin * 60)} statt ${dauer(o.dauerMin * 60)}`);
    if (s.zielspalte !== o.zielspalte) a.push(`Zielspalte ${spalten.find((x) => x.id === s.zielspalte)?.name}`);
    if (JSON.stringify(s.teilnehmer) !== JSON.stringify(o.teilnehmer)) a.push(`Teilnehmer ${s.teilnehmer.map((k) => konto(k).name).join(", ")}`);
    if (r.vorlaufTage !== or.vorlaufTage) a.push(`Vorlauf ${r.vorlaufTage} Tage`);
    if (r.feiertageUeberspringen !== or.feiertageUeberspringen) a.push(r.feiertageUeberspringen ? "Feiertage auslassen" : "Feiertage nicht auslassen");
    if (r.ab !== or.ab || r.bis !== or.bis) a.push("Zeitraum");
    if ((r.beschreibung ?? "") !== (or.beschreibung ?? "")) a.push("Beschreibung");
    return a;
  });
  const geaendert = $derived(aenderungen.length > 0);
  const zaehle = (st: Vorkommen["stand"]): number => liste.filter((v) => v.stand === st).length;

  function anzeige(v: Vorkommen): { text: string; symbol: string; klasse: string; erklaerung: string } {
    if (neu && (v.stand === "vorgebucht" || v.stand === "heute")) {
      return { text: "wird vorgebucht", symbol: "fa-thumbtack", klasse: "wartet", erklaerung: "Anlegen legt für diesen Tag eine Karte in die Zielspalte" };
    }
    if (geaendert && v.stand === "vorgebucht") {
      return { text: "wird angepasst", symbol: "fa-arrows-rotate", klasse: "wartet", erklaerung: "Unberührte Vorbuchung: Speichern passt die Karte an" };
    }
    return STAND[v.stand];
  }
  /** Uhrzeit eines Tages: unberührte und künftige folgen dem Entwurf, alle anderen bleiben bei der gespeicherten */
  function uhrzeitAm(v: Vorkommen): string {
    const folgt = neu || ["vorgebucht", "geplant"].includes(v.stand);
    return (folgt ? s.uhrzeit : original?.uhrzeit) || "ganztägig";
  }

  const wochen = $derived.by(() => {
    const g: { kw: number; von: string; tage: Vorkommen[] }[] = [];
    for (const v of liste) {
      const kw = kalenderwoche(v.tag);
      if (g[g.length - 1]?.kw !== kw) g.push({ kw, von: montagVon(v.tag), tage: [] });
      g[g.length - 1].tage.push(v);
    }
    return g;
  });

  const RHYTHMEN: [Rhythmus, string][] = [["taeglich", "Täglich"], ["werktags", "Werktags"], ["woechentlich", "Wöchentlich"], ["monatlich", "Monatlich"]];
  const MONATSREGELN: [Monatsregel, string][] = [["tag", "am Tag"], ["erster-werktag", "erster Werktag"], ["letzter-werktag", "letzter Werktag"]];

  function tagUmschalten(t: number): void {
    const tage = s.tage ?? [];
    s.tage = tage.includes(t) ? tage.filter((x) => x !== t) : [...tage, t];
  }
  function boardWaehlen(id: Kennung): void {
    s.board = id;
    const nb = boardVon(id);
    s.zielspalte = nb?.spalten.find((x) => !x.erledigt)?.id ?? "";
    s.teilnehmer = s.teilnehmer.filter((k) => nb?.mitglieder.some((m) => m.konto === k));
    r.labels = [];
  }

  function speichern(): void {
    const kopie = $state.snapshot(s) as Serie;
    const regelKopie = $state.snapshot(r) as SerienRegel;
    if (neu) {
      const id = `se-${crypto.randomUUID().slice(0, 8)}`;
      plan.serien.push({ ...kopie, id });
      plan.regeln[id] = { ...regelKopie, serie: id };
      gehe(`/serien/${id}`);
      return;
    }
    if (!original) return;
    const angepasst = zaehle("vorgebucht");
    Object.assign(original, kopie);
    plan.regeln[original.id] = regelKopie;
    bericht = `Gespeichert: ${angepasst} unberührte ${angepasst === 1 ? "Vorbuchung" : "Vorbuchungen"} angepasst; angefasste, vergangene und gelöschte Tage bleiben.`;
  }

  function pauseUmschalten(): void {
    if (!original) return;
    const echt = (plan.regeln[original.id] ??= $state.snapshot(r) as SerienRegel);
    if (istPausiert(echt)) {
      echt.fortgesetzt = HEUTE;
      original.pausiert = false;
      bericht = "Fortgesetzt: ab heute wird wieder vorgebucht; gelöschte Tage bleiben gelöscht.";
    } else {
      const entfernt = zaehle("vorgebucht");
      echt.pausiertSeit = HEUTE;
      echt.fortgesetzt = undefined;
      original.pausiert = true;
      bericht = `Pausiert: ${entfernt} unberührte ${entfernt === 1 ? "Vorbuchung" : "Vorbuchungen"} entfernt; angefasste Karten bleiben stehen.`;
    }
    r.pausiertSeit = echt.pausiertSeit;
    r.fortgesetzt = echt.fortgesetzt;
  }

  function loeschen(): void {
    if (!original) return;
    plan.serien.splice(plan.serien.indexOf(original), 1);
    gehe("/serien");
  }
</script>

<div class="rahmen-kopf">
  <div class="seitenkopf">
    <h1><i class="fa-solid fa-repeat pw-serien-kopfsymbol"></i>{neu ? "Neue Serie" : original?.titel}</h1>
    {#if !neu}
      {#if pausiert}<span class="zustand pausiert"><i class="fa-solid fa-circle-pause"></i>pausiert seit {datum(r.pausiertSeit ?? HEUTE, true)}</span>
      {:else}<span class="zustand fertig"><i class="fa-solid fa-circle-play"></i>aktiv</span>{/if}
    {/if}
    <div class="aktionen">
      {#if neu}
        <a class="knopf ohne" href="/serien">Abbrechen</a>
        <button class="knopf haupt" onclick={speichern} disabled={!s.titel.trim() || !s.teilnehmer.length}
                title="Legt die Serie an und bucht die Tage im Vorlauf als Karten vor"><i class="fa-solid fa-check"></i>Anlegen und vorbuchen</button>
      {:else if darf}
        <button class="knopf" onclick={pauseUmschalten} title={pausiert ? "Ab heute wieder vorbuchen" : "Keine neuen Vorbuchungen; unberührte Zukunftskarten werden entfernt"}>
          <i class="fa-solid {pausiert ? 'fa-play' : 'fa-pause'}"></i>{pausiert ? "Fortsetzen" : "Pausieren"}</button>
        <button class="knopf ohne gefahr" onclick={() => (loeschenFrage = true)}><i class="fa-solid fa-trash-can"></i>Löschen</button>
      {/if}
    </div>
    <div class="unterzeile"><a class="pw-serien-zurueck" href="/serien"><i class="fa-solid fa-chevron-left"></i> Serien und Termine</a>
      {#if b}<span class="schwach"> · {b.name} · {rhythmusText(s, r)}{s.uhrzeit ? ` um ${s.uhrzeit}` : ""}</span>{/if}</div>
  </div>

  {#if loeschenFrage && original}
    <div class="hinweis gefahr"><i class="fa-solid fa-trash-can"></i>
      <div><b>Serie "{original.titel}" löschen?</b> {zaehle("vorgebucht")} unberührte Vorbuchungen gehen in den Papierkorb.
        {#if zaehle("beruehrt")}{zaehle("beruehrt")} angefasste {zaehle("beruehrt") === 1 ? "Karte bleibt" : "Karten bleiben"} stehen.{/if}
        Karten mit erfasster Zeit und erledigte bleiben als Verlauf und werden von der Serie gelöst; bestätigte Zeiten zählen weiter.</div>
      <span class="rechts"><button class="knopf klein" onclick={() => (loeschenFrage = false)}>Behalten</button>
        <button class="knopf gefahr-voll klein" onclick={loeschen}><i class="fa-solid fa-trash-can"></i>Löschen</button></span>
    </div>
  {:else if geaendert && darf}
    <div class="hinweis"><i class="fa-solid fa-arrows-rotate"></i>
      <div><b>Nicht gespeichert: {aenderungen.join(", ")}.</b> Speichern passt {zaehle("vorgebucht")} unberührte Vorbuchungen an;
        {zaehle("beruehrt") === 0 ? "" : zaehle("beruehrt") === 1 ? "die angefasste Karte, " : "angefasste Karten, "}vergangene und gelöschte Tage bleiben, wie sie sind.</div>
      <span class="rechts"><button class="knopf klein" onclick={laden}>Verwerfen</button>
        <button class="knopf haupt klein" onclick={speichern}><i class="fa-solid fa-check"></i>Speichern</button></span>
    </div>
  {:else if bericht}
    <div class="hinweis erfolg"><i class="fa-solid fa-circle-check"></i><div>{bericht}</div>
      <span class="rechts"><button class="knopf ohne klein" onclick={() => (bericht = "")}>Ausblenden</button></span></div>
  {:else if pausiert}
    <div class="hinweis warnung"><i class="fa-solid fa-circle-pause"></i>
      <div>Pausiert: es entstehen keine neuen Karten, unberührte Zukunftskarten sind entfernt, angefasste bleiben. Fortsetzen bucht ab
        heute wieder vor; gelöschte Tage bleiben gelöscht.</div></div>
  {/if}
</div>

<div class="spalten pw-serien-spalten">
  <div class="rollfeld pw-serien-formular">
    {#if !darf && b}
      <div class="hinweis"><i class="fa-solid fa-lock"></i><div>Nur ansehen: dir fehlt im Board {b.name} das Recht "Serien und Termine verwalten".</div></div>
    {/if}
    <fieldset disabled={!darf}>
      <section class="bereich">
        <h2>Karte</h2>
        <div class="pw-felder">
          <span class="name"><i class="fa-solid fa-heading"></i>Titel</span>
          <span class="wert"><input class="eingabe" bind:value={s.titel} placeholder="Titel jeder Karte; die Uhrzeit steht davor" /></span>
          <span class="name"><i class="fa-solid fa-table-columns"></i>Board</span>
          <span class="wert">
            {#if neu}
              <span class="stufen">{#each boardsMitSerien().filter((x) => hatRecht(x, "serien.verwalten")) as x (x.id)}
                <button class:an={s.board === x.id} onclick={() => boardWaehlen(x.id)}>{x.name}</button>{/each}</span>
            {:else if b}
              <span class="pw-serien-ort" title="Das Board einer Serie steht nach dem Anlegen fest"><span class="pw-farbpunkt" data-farbe={b.farbe}></span>{b.name}</span>
            {/if}
          </span>
          <span class="name" title="Hier legt die Serie ihre Karten an"><i class="fa-solid fa-inbox"></i>Zielspalte</span>
          <span class="wert"><span class="stufen">{#each spalten as x (x.id)}
            <button class:an={s.zielspalte === x.id} onclick={() => (s.zielspalte = x.id)}><span class="pw-farbpunkt" data-farbe={x.farbe}></span>{x.name}</button>{/each}</span></span>
          <span class="name"><i class="fa-solid fa-tag"></i>Labels</span>
          <span class="wert">
            {#each r.labels as l (l)}{@const lab = b?.labels.find((x) => x.id === l)}{#if lab}<span class="pw-label" data-farbe={lab.farbe}>{lab.name}</span>{/if}{/each}
            <button class="knopf ohne symbol klein" title="Label wählen"><i class="fa-solid fa-plus"></i></button>
          </span>
        </div>
        <textarea class="eingabe" rows="2" bind:value={r.beschreibung} placeholder="Beschreibung jeder Karte (Markdown)"></textarea>
      </section>

      <section class="bereich">
        <h2>Rhythmus</h2>
        <div class="pw-felder">
          <span class="name"><i class="fa-solid fa-repeat"></i>Wie oft</span>
          <span class="wert"><span class="stufen">{#each RHYTHMEN as [w, n] (w)}<button class:an={s.rhythmus === w} onclick={() => (s.rhythmus = w)}>{n}</button>{/each}</span></span>
          {#if s.rhythmus === "woechentlich"}
            <span class="name"><i class="fa-solid fa-calendar-week"></i>An Tagen</span>
            <span class="wert"><span class="stufen">{#each WOCHE_AB_MONTAG as t (t)}
              <button class:an={(s.tage ?? []).includes(t)} title={TAGE_LANG[t]} onclick={() => tagUmschalten(t)}>{TAGE_KURZ[t]}</button>{/each}</span></span>
          {:else if s.rhythmus === "monatlich"}
            <span class="name"><i class="fa-solid fa-calendar-day"></i>Im Monat</span>
            <span class="wert">
              <span class="stufen">{#each MONATSREGELN as [w, n] (w)}<button class:an={(r.monatsregel ?? "tag") === w} onclick={() => (r.monatsregel = w)}>{n}</button>{/each}</span>
              {#if (r.monatsregel ?? "tag") === "tag"}
                <input class="eingabe pw-serien-kurz" value={r.monatstag ?? Number(r.ab.slice(8, 10))} title="Tag im Monat; hat ein Monat weniger Tage, gilt sein letzter"
                       oninput={(e) => { const n = Number(e.currentTarget.value); if (n >= 1 && n <= 31) r.monatstag = n; }} />.
              {/if}
            </span>
          {:else if s.rhythmus === "taeglich"}
            <span class="name"><i class="fa-solid fa-calendar-week"></i>Wochenende</span>
            <span class="wert"><button class="schalter" class:an={r.wochenendenUeberspringen} aria-label="Samstag und Sonntag auslassen"
              onclick={() => (r.wochenendenUeberspringen = !r.wochenendenUeberspringen)}></button><span class="leise klein">Samstag und Sonntag auslassen</span></span>
          {/if}
          <span class="name"><i class="fa-regular fa-clock"></i>Uhrzeit</span>
          <span class="wert"><input class="eingabe pw-serien-kurz" bind:value={s.uhrzeit} placeholder="ganztägig" title="Steht vor dem Titel jeder Karte; leer: ganztägig" />
            <span class="name-neben"><i class="fa-solid fa-hourglass-half"></i>Dauer</span>
            <input class="eingabe pw-serien-kurz" bind:value={dauerText} title="Stunden:Minuten; Schätzung jeder Karte und vorgebuchte Zeit je Teilnehmer"
                   oninput={() => { const m = textDauer(dauerText); if (m !== undefined) s.dauerMin = m; }} /></span>
          <span class="name"><i class="fa-regular fa-calendar"></i>Zeitraum</span>
          <span class="wert"><input class="eingabe pw-serien-tag" bind:value={abText} title="Erster möglicher Tag, TT.MM.JJJJ"
                                    oninput={() => { const t = textTag(abText); if (t) r.ab = t; }} />
            <span class="schwach">bis</span>
            <input class="eingabe pw-serien-tag" bind:value={bisText} placeholder="ohne Ende" title="Letzter möglicher Tag, TT.MM.JJJJ; leer: ohne Ende"
                   oninput={() => { r.bis = bisText.trim() ? textTag(bisText) ?? r.bis : undefined; }} /></span>
        </div>
      </section>

      <section class="bereich">
        <h2>Teilnehmer</h2>
        <PersonenFeld bind:konten={s.teilnehmer} {kandidaten} vorschlagOffen={neu} />
        <p class="leise klein">Jeder Teilnehmer bekommt die Zeit vorgebucht und bestätigt sie am Folgetag selbst. Wer an einem Tag fehlt
          (Urlaub, Abwesenheit, Feiertag seines Bundeslands), bekommt nichts vorgebucht; fehlen alle, entfällt der Tag.</p>
      </section>

      <section class="bereich">
        <h2>Vorbuchen</h2>
        <div class="einstellung">
          <div><div class="name">Vorlauf</div><div class="erklaerung">So viele Tage im Voraus liegen die Karten in der Zielspalte; 0: nur heute</div></div>
          <div class="wert"><input class="eingabe" value={r.vorlaufTage}
            oninput={(e) => { const n = Number(e.currentTarget.value); if (Number.isInteger(n) && n >= 0 && n <= 90) r.vorlaufTage = n; }} /><span class="einheit">Tage</span></div>
        </div>
        <div class="einstellung">
          <div><div class="name">Feiertage auslassen</div><div class="erklaerung">Nach dem Bundesland jedes Teilnehmers aus seinem Zeitkonto</div></div>
          <div class="wert"><button class="schalter" class:an={r.feiertageUeberspringen} aria-label="Feiertage auslassen"
            onclick={() => (r.feiertageUeberspringen = !r.feiertageUeberspringen)}></button></div>
        </div>
      </section>
    </fieldset>
  </div>

  <div class="rollfeld pw-serien-tage">
    <div class="pw-serien-tage-kopf">
      <h2>{neu ? "So bucht die Serie vor" : "Tage der Serie"}</h2>
      <p class="leise klein">
        {#if pausiert}Pausiert: keine Vorbuchungen.
        {:else}Karten liegen bis {datum(plusTage(HEUTE, r.vorlaufTage), true)} in {spalten.find((x) => x.id === s.zielspalte)?.name ?? "der ersten Spalte"};
          {#if naechster}nächster Tag {datum(naechster.tag, true)}{:else}kein weiterer Tag{/if}{/if}</p>
    </div>
    {#each wochen as w (w.von)}
      <div class="etikett">Woche {w.kw} <span class="zahl">{datum(w.von)} bis {datum(plusTage(w.von, 6))}</span></div>
      <div class="pw-serien-tagliste">
        {#each w.tage as v (v.tag)}
          {@const a = anzeige(v)}
          <div class="pw-serien-tagzeile {v.stand}" class:heute={v.tag === HEUTE}>
            <span class="wann"><b class="zahl">{datum(v.tag, true)}</b><span class="zahl">{uhrzeitAm(v)}</span></span>
            <span class="zustand {a.klasse}" title={a.erklaerung}><i class="fa-solid {a.symbol}"></i>{a.text}</span>
            {#if v.stand === "wartet" || v.notiz || (v.ohne.length && v.stand !== "ausgelassen")}
            <span class="notiz">
              {#if v.stand === "wartet"}<span class="schwach">wartet auf</span>{#each v.offen as k (k)}<span class="pw-serien-mini" title={konto(k).name}><Person id={k} /></span>{/each}
              {:else if v.notiz}<span class="schwach">{v.notiz}</span>{/if}
              {#if v.ohne.length && v.stand !== "ausgelassen"}
                <span class="schwach">ohne</span>{#each v.ohne as o (o.konto)}<span class="pw-serien-mini" title="{konto(o.konto).name}: {o.grund}"><Person id={o.konto} /><span class="klein schwach">{o.grund}</span></span>{/each}
              {/if}
            </span>
            {/if}
          </div>
        {/each}
      </div>
    {:else}
      <div class="leer"><i class="fa-regular fa-calendar"></i><p>Kein Tag im Zeitraum; Rhythmus oder Tage wählen.</p></div>
    {/each}
  </div>
</div>
