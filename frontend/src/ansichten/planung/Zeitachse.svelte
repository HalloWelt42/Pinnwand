<script lang="ts">
  // Zeitachse eines Boards (/board/<kürzel>/zeitachse) unter Kopf und Werkzeugleiste des Boards: Karten mit Start und
  // Fällig als Balken über die Tage, gruppiert nach Spalte oder Person, Linie für heute, Wochenenden und Feiertage der
  // Bundesländer der Mitglieder gekennzeichnet, Maßstab Woche oder Monat. Ziehen verschiebt, Ziehen am Rand ändert Start
  // oder Fällig (M-50, M-51), Klick öffnet die Karte; mit der Tastatur Pfeile (mit Umschalt: Fällig, mit Alt: Start).
  // Karten ohne Datum stehen daneben und landen beim Ablegen mit Start und Fällig auf dem Tag. Eine eigene Fläche
  // rollt in beide Richtungen; Kopf und Namen bleiben stehen.
  import { onMount } from "svelte";
  import { darf as darfIm } from "../../daten/abfragen";
  import { bearbeiten } from "../../daten/anwendung/karten.svelte";
  import { uhr } from "../../daten/uhr.svelte";
  import { datum, monatText } from "../../daten/format";
  import { konto, mitKonto, stand } from "../../daten/stand.svelte";
  import Person from "../../board/Person.svelte";
  import type { BoardAnsichtWerte } from "../../board/ansichten";
  import type { Karte, Kennung } from "../../modell";
  import { istWochenende, kalenderwoche, monatsanfang, MONATE, montagVon, plusMonate, plusTage, TAGE_LANG, tageVon, tageZwischen, wochentag } from "../../regeln/tage";
  import { gehe } from "../../weg.svelte";
  import OhneDatum from "./OhneDatum.svelte";
  import { abwesenheitenSichtbar, abwesenheitSymbol, artName, farbeDerSpalte, feiertageAm, feiertagTitel, istErledigt, kartenDesBoards, kartenPfad } from "./lesen";

  let { board, filter, ziehenGesperrt = false }: BoardAnsichtWerte = $props();

  let gruppierung = $state<"spalte" | "person">("spalte");
  let massstab = $state<"woche" | "monat">("woche");
  let versatz = $state(0);
  let gezogen = $state<string | null>(null);

  // Spalte der Namen: schmaler, wenn die Seitenleiste zur Symbolleiste wird (unter 1240 Pixeln, wie der Leitstand)
  let nameBreite = $state(280);
  onMount(() => {
    const schmal = matchMedia("(max-width: 1240px)");
    const setzen = (): void => { nameBreite = schmal.matches ? 210 : 280; };
    setzen();
    schmal.addEventListener("change", setzen);
    return () => schmal.removeEventListener("change", setzen);
  });
  /** schmaler als das passt, steht die Beschriftung neben dem Balken */
  const BESCHRIFTUNG_INNEN = 110;
  const breite = $derived(massstab === "woche" ? 30 : 11);
  const anfang = $derived(massstab === "woche" ? plusTage(montagVon(uhr.heute), -7 + versatz * 28) : plusMonate(monatsanfang(uhr.heute), versatz));
  const ende = $derived(massstab === "woche" ? plusTage(anfang, 69) : plusTage(plusMonate(anfang, 4), -1));
  const tage = $derived(tageVon(anfang, ende));
  const pos = (tag: string): number => tageZwischen(anfang, tag);

  const karten = $derived(kartenDesBoards(board, filter));
  const mitDatum = $derived(karten.filter((k) => k.start || k.faellig));
  const ohneDatum = $derived(karten.filter((k) => !k.start && !k.faellig && !istErledigt(board, k)));
  const mitglieder = $derived(mitKonto(board).map((m) => m.konto));
  const abwSichtbar = $derived(abwesenheitenSichtbar(board));
  const darf = $derived(darfIm(board, "karten.bearbeiten") && !ziehenGesperrt);

  interface Zeile { k: Karte; s: number; e: number; warnung: string; mit: Kennung[] }
  interface Gruppe {
    id: string; name: string; farbe?: string; konto?: Kennung; zeilen: Zeile[];
    abwesend: { s: number; e: number; text: string; symbol: string; titel: string }[];
  }

  function zeile(k: Karte, person?: Kennung): Zeile {
    const von = k.start ?? k.faellig!;
    const bis = k.faellig ?? k.start!;
    const treffer = abwSichtbar && !istErledigt(board, k)
      ? stand.abwesenheiten.filter((a) => k.zustaendig.includes(a.konto) && a.von <= bis && von <= a.bis && (a.anteil ?? 1) >= 1) : [];
    const warnung = treffer.map((a) => `fällt in ${artName(a)} von ${konto(a.konto).name} (${datum(a.von)} bis ${datum(a.bis)})`).join("; ");
    return { k, s: pos(von), e: pos(bis), warnung, mit: k.zustaendig.filter((p) => p !== person) };
  }
  const nachStart = (a: Zeile, b: Zeile): number => a.s - b.s || a.e - b.e;

  const gruppen = $derived.by((): Gruppe[] => {
    if (gruppierung === "spalte") {
      return board.spalten.map((sp) => ({ id: sp.id, name: sp.name, farbe: sp.farbe, abwesend: [],
        zeilen: mitDatum.filter((k) => k.spalte === sp.id).map((k) => zeile(k)).sort(nachStart) }));
    }
    const g: Gruppe[] = mitglieder.filter((p) => mitDatum.some((k) => k.zustaendig.includes(p))).map((p) => ({
      id: p, name: konto(p).name, konto: p,
      zeilen: mitDatum.filter((k) => k.zustaendig.includes(p)).map((k) => zeile(k, p)).sort(nachStart),
      abwesend: abwSichtbar ? stand.abwesenheiten.filter((a) => a.konto === p && a.bis >= anfang && a.von <= ende).map((a) => ({
        s: Math.max(0, pos(a.von)), e: Math.min(tage.length - 1, pos(a.bis)), text: artName(a), symbol: abwesenheitSymbol(a),
        titel: `${konto(p).name}: ${artName(a)} ${datum(a.von)} bis ${datum(a.bis)}${a.notiz ? ` (${a.notiz})` : ""}` })) : [],
    }));
    const niemand = mitDatum.filter((k) => !k.zustaendig.length);
    if (niemand.length) g.push({ id: "niemand", name: "Ohne Zuständige", zeilen: niemand.map((k) => zeile(k)).sort(nachStart), abwesend: [] });
    return g;
  });

  // Skala: Monate, Wochen, im Wochenmaßstab die Tage; Streifen für Wochenenden und Feiertage
  const monate = $derived.by(() => {
    const m: { name: string; s: number; n: number }[] = [];
    tage.forEach((t, i) => {
      const name = `${MONATE[Number(t.slice(5, 7)) - 1]} ${t.slice(0, 4)}`;
      if (m[m.length - 1]?.name === name) m[m.length - 1].n++;
      else m.push({ name, s: i, n: 1 });
    });
    return m;
  });
  const wochen = $derived.by(() => {
    const w: { kw: number; s: number; n: number }[] = [];
    tage.forEach((t, i) => {
      if (i === 0 || wochentag(t) === 1) w.push({ kw: kalenderwoche(t), s: i, n: 1 });
      else w[w.length - 1].n++;
    });
    return w;
  });
  const besondere = $derived(tage.map((t, i) => ({ t, i, wochenende: istWochenende(t), feiertage: feiertageAm(t, mitglieder) }))
    .filter((x) => x.wochenende || x.feiertage.length));
  const heute = $derived(pos(uhr.heute));
  const titel = $derived(anfang.slice(0, 4) === ende.slice(0, 4)
    ? `${MONATE[Number(anfang.slice(5, 7)) - 1]} bis ${monatText(ende)}` : `${monatText(anfang)} bis ${monatText(ende)}`);

  // Ziehen der Balken: Zeiger mit Fangen; ohne Bewegung ist es ein Klick und öffnet die Karte
  type Art = "ganz" | "start" | "ende";
  let zug = $state<{ id: string; art: Art; x0: number; delta: number; bewegt: boolean } | null>(null);

  function verschoben(z: Zeile, art: Art, d: number): { s: number; e: number } {
    if (art === "ganz") return { s: z.s + d, e: z.e + d };
    if (art === "start") return { s: Math.min(z.s + d, z.e), e: z.e };
    return { s: z.s, e: Math.max(z.e + d, z.s) };
  }
  function lage(z: Zeile): { s: number; e: number } {
    return zug && zug.id === z.k.id ? verschoben(z, zug.art, zug.delta) : z;
  }
  function uebernehmen(z: Zeile, art: Art, d: number): void {
    if (d === 0) return;
    const l = verschoben(z, art, d);
    const k = z.k;
    const start = k.start || art === "start" ? plusTage(anfang, l.s) : undefined;
    const faellig = k.faellig || art === "ende" ? plusTage(anfang, l.e) : undefined;
    const text = [start ? `Start ${datum(start, true)}` : "", faellig ? `fällig ${datum(faellig, true)}` : ""].filter((x) => x).join(", ");
    bearbeiten(k.id, { start, faellig }, text);
  }
  function greifen(e: PointerEvent, z: Zeile): void {
    if (e.button !== 0) return;
    if (!darf) return;
    const ziel = e.target as HTMLElement;
    const art: Art = ziel.closest(".rand.start") ? "start" : ziel.closest(".rand.ende") ? "ende" : "ganz";
    (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
    zug = { id: z.k.id, art, x0: e.clientX, delta: 0, bewegt: false };
  }
  function bewegen(e: PointerEvent): void {
    if (!zug) return;
    const dx = e.clientX - zug.x0;
    if (Math.abs(dx) > 3) zug.bewegt = true;
    zug.delta = Math.round(dx / breite);
  }
  function loslassen(z: Zeile): void {
    if (!zug) return;
    const { bewegt, art, delta } = zug;
    zug = null;
    if (bewegt) uebernehmen(z, art, delta);
    else gehe(kartenPfad(board, z.k));
  }
  function taste(e: KeyboardEvent, z: Zeile): void {
    if (e.key === "Enter") { gehe(kartenPfad(board, z.k)); return; }
    if ((e.key !== "ArrowLeft" && e.key !== "ArrowRight") || !darf) return;
    e.preventDefault();
    uebernehmen(z, e.shiftKey ? "ende" : e.altKey ? "start" : "ganz", e.key === "ArrowLeft" ? -1 : 1);
  }

  // Ablegen aus der Leiste: Start und Fällig auf den Tag unter dem Zeiger
  let spuren = $state<HTMLElement>();
  let zielTag = $state<number | null>(null);
  function tagUnter(e: DragEvent): number {
    const r = spuren!.getBoundingClientRect();
    return Math.max(0, Math.min(tage.length - 1, Math.floor((e.clientX - r.left) / breite)));
  }
  function ueber(e: DragEvent): void {
    if (!gezogen || !darf) return;
    e.preventDefault();
    zielTag = tagUnter(e);
  }
  function fallen(e: DragEvent): void {
    e.preventDefault();
    const id = e.dataTransfer?.getData("text/plain") || gezogen;
    const k = karten.find((x) => x.id === id);
    if (k && darf) { const t = plusTage(anfang, tagUnter(e)); bearbeiten(k.id, { start: t, faellig: t }, `Start und fällig ${datum(t, true)}`); }
    zielTag = null;
    gezogen = null;
  }

  function balkenText(z: Zeile, l: { s: number; e: number }): string {
    const s = plusTage(anfang, l.s);
    const e = plusTage(anfang, l.e);
    if (!z.k.start) return `fällig ${datum(e)}`;
    if (!z.k.faellig) return `ab ${datum(s)}`;
    return l.s === l.e ? datum(s) : `${datum(s)} bis ${datum(e)}`;
  }
</script>

<div class="pw-planung-raum pw-zeitachse">
  <div class="pw-planung-haupt">
    <div class="pw-planung-steuer">
      <button class="knopf symbol klein" title={massstab === "woche" ? "Vier Wochen zurück" : "Einen Monat zurück"} onclick={() => versatz--}><i class="fa-solid fa-chevron-left"></i></button>
      <button class="knopf klein" onclick={() => (versatz = 0)}>Heute</button>
      <button class="knopf symbol klein" title={massstab === "woche" ? "Vier Wochen weiter" : "Einen Monat weiter"} onclick={() => versatz++}><i class="fa-solid fa-chevron-right"></i></button>
      <h2>{titel}</h2>
      <span class="pw-umschalter" role="group" aria-label="Gruppieren">
        <button class:an={gruppierung === "spalte"} onclick={() => (gruppierung = "spalte")}><i class="fa-solid fa-table-columns"></i>Nach Spalte</button>
        <button class:an={gruppierung === "person"} onclick={() => (gruppierung = "person")}><i class="fa-solid fa-user-group"></i>Nach Person</button>
      </span>
      <span class="stufen" role="group" aria-label="Maßstab" title="Maßstab: ein Tag je Spalte (Woche) oder vier Monate im Überblick (Monat)">
        <button class:an={massstab === "woche"} onclick={() => { massstab = "woche"; versatz = 0; }}>Woche</button>
        <button class:an={massstab === "monat"} onclick={() => { massstab = "monat"; versatz = 0; }}>Monat</button>
      </span>
      <div class="rechts pw-planung-legende">
        <span><i class="muster wochenende"></i>Wochenende</span>
        <span><i class="muster feiertag"></i>Feiertag</span>
        {#if gruppierung === "person" && abwSichtbar}<span><i class="muster abwesend"></i>Abwesend</span>{/if}
        <span><i class="muster heute"></i>Heute</span>
      </div>
    </div>

    <div class="pw-zeitachse-raum">
      <div class="pw-zeitachse-flaeche" style="--name: {nameBreite}px; --tag: {breite}px; width: {nameBreite + tage.length * breite}px" class:monat={massstab === "monat"}>
        <div class="pw-zeitachse-kopf">
          <div class="ecke">{gruppierung === "spalte" ? "Spalte und Karte" : "Person und Karte"}</div>
          <div class="skala" style="width: {tage.length * breite}px">
            <div class="reihe">{#each monate as m (m.s)}<span style="left: {m.s * breite}px; width: {m.n * breite}px">{m.name}</span>{/each}</div>
            <div class="reihe">{#each wochen as w (w.s)}<span class="zahl" style="left: {w.s * breite}px; width: {w.n * breite}px"
              title="Kalenderwoche {w.kw}">{w.n * breite >= 70 ? `Woche ${w.kw}` : w.kw}</span>{/each}</div>
            {#if massstab === "woche"}
              <div class="reihe tage">
                {#each tage as t, i (t)}
                  {@const f = feiertageAm(t, mitglieder)}
                  <span class="zahl" class:wochenende={istWochenende(t)} class:feiertag={f.length > 0} class:heute={t === uhr.heute} style="left: {i * breite}px; width: {breite}px"
                        title="{TAGE_LANG[wochentag(t)]}, {datum(t)}{f.map((x) => `; ${feiertagTitel(x)}`).join('')}">{Number(t.slice(8, 10))}</span>
                {/each}
              </div>
            {/if}
          </div>
        </div>

        <div class="pw-zeitachse-koerper" role="grid" aria-label="Karten über die Zeit" tabindex="-1"
             ondragover={ueber} ondragleave={() => (zielTag = null)} ondrop={fallen}>
          <div class="streifen" bind:this={spuren} aria-hidden="true">
            {#each besondere as x (x.t)}
              <span class:feiertag={x.feiertage.length > 0} style="left: {x.i * breite}px; width: {breite}px"
                    title={x.feiertage.map((f) => feiertagTitel(f)).join("; ") || "Wochenende"}></span>
            {/each}
            {#if zielTag !== null}<span class="ziel" style="left: {zielTag * breite}px; width: {breite}px"></span>{/if}
            {#if heute >= 0 && heute < tage.length}<span class="heute-linie" style="left: {heute * breite + breite / 2 - 1}px"></span>{/if}
          </div>

          {#each gruppen as g (g.id)}
            <div class="pw-zeitachse-gruppe" data-farbe={g.farbe}>
              <div class="name">
                {#if g.konto}<Person id={g.konto} />{:else if g.farbe}<span class="pw-farbpunkt"></span>{:else}<i class="fa-solid fa-user-slash schwach"></i>{/if}
                <b>{g.name}</b><span class="zaehler">{g.zeilen.length}</span>
              </div>
              <div class="spur">
                {#each g.abwesend as a (a.s)}
                  <span class="abwesend" style="left: {a.s * breite}px; width: {(a.e - a.s + 1) * breite}px" title={a.titel}>
                    <i class="fa-solid {a.symbol}"></i>{#if (a.e - a.s + 1) * breite >= 80}<span>{a.text}</span>{/if}</span>
                {/each}
              </div>
            </div>
            {#each g.zeilen as z (z.k.id)}
              {@const l = lage(z)}
              {@const erledigt = istErledigt(board, z.k)}
              {@const ueberfaellig = !erledigt && !!z.k.faellig && z.k.faellig < uhr.heute}
              {@const vs = Math.max(0, l.s)}
              {@const ve = Math.min(tage.length - 1, l.e)}
              {@const px = (ve - vs + 1) * breite - 4}
              {@const text = ueberfaellig && !z.k.start ? `überfällig, ${balkenText(z, l)}` : balkenText(z, l)}
              <div class="pw-zeitachse-zeile">
                <a class="name" href={kartenPfad(board, z.k)} data-farbe={farbeDerSpalte(board, z.k)} title="{z.k.schluessel} {z.k.titel}: öffnen">
                  <span class="pw-farbpunkt"></span><span class="pw-schluessel">{z.k.schluessel}</span><span class="titel">{z.k.titel}</span>
                  {#if z.mit.length}<span class="pw-personen" title="Auch zuständig: {z.mit.map((p) => konto(p).name).join(', ')}">{#each z.mit as p (p)}<Person id={p} />{/each}</span>{/if}
                </a>
                <div class="spur">
                  {#each g.abwesend as a (a.s)}<span class="abwesend leise" style="left: {a.s * breite}px; width: {(a.e - a.s + 1) * breite}px"></span>{/each}
                  {#if ve < vs}
                    <span class="ausserhalb" class:rechts={l.s >= tage.length} title="Außerhalb des gezeigten Zeitraums">
                      <i class="fa-solid {l.s >= tage.length ? 'fa-angles-right' : 'fa-angles-left'}"></i>{balkenText(z, l)}</span>
                  {:else}
                    <div class="pw-zeitachse-balken" class:nur-faellig={!z.k.start} class:erledigt class:ueberfaellig class:gezogen={zug?.id === z.k.id}
                         class:abgeschnitten-links={l.s < 0} class:abgeschnitten-rechts={l.e >= tage.length} class:gesperrt={!darf}
                         data-farbe={farbeDerSpalte(board, z.k)} style="left: {vs * breite + 2}px; width: {px}px"
                         role="button" tabindex="0" aria-label="{z.k.schluessel} {z.k.titel}, {balkenText(z, l)}"
                         title="{z.k.schluessel} {z.k.titel}: {balkenText(z, l)}{ueberfaellig ? ', überfällig' : ''}{erledigt ? ', erledigt' : ''}{!z.k.start ? '. Nur Fällig gesetzt; am linken Rand ziehen setzt den Start' : ''}{z.warnung ? `. Achtung: ${z.warnung}` : ''}"
                         onpointerdown={(e) => greifen(e, z)} onpointermove={bewegen} onpointerup={() => loslassen(z)} onpointercancel={() => (zug = null)}
                         onkeydown={(e) => taste(e, z)}>
                      {#if darf}<span class="rand start" title="Start ändern"></span>{/if}
                      {#if erledigt}<i class="fa-solid fa-check zeichen"></i>{:else if ueberfaellig}<i class="fa-solid fa-triangle-exclamation zeichen"></i>{/if}
                      {#if z.warnung}<i class="fa-solid fa-umbrella-beach warnzeichen"></i>{/if}
                      {#if px >= BESCHRIFTUNG_INNEN}<span class="text zahl">{text}</span>{/if}
                      {#if darf}<span class="rand ende" title="Fällig ändern"></span>{/if}
                    </div>
                    {#if px < BESCHRIFTUNG_INNEN}
                      <span class="pw-zeitachse-beschriftung zahl" class:ueberfaellig style="left: {vs * breite + px + 8}px">{text}</span>
                    {/if}
                  {/if}
                </div>
              </div>
            {:else}
              <div class="pw-zeitachse-zeile ohne-karten"><span class="name schwach">keine Karte mit Datum</span><div class="spur"></div></div>
            {/each}
          {/each}
        </div>
      </div>
    </div>
  </div>
  <OhneDatum {board} karten={ohneDatum} titel="Ohne Datum" bind:gezogen gesperrt={ziehenGesperrt}
             erklaerung="Auf einen Tag ziehen setzt Start und Fällig auf diesen Tag; am Rand des Balkens ziehen verlängert ihn." />
</div>
