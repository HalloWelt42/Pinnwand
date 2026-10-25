<script lang="ts">
  // Jahreskalender deines Zeitkontos: zwölf Monate mit Feiertagen deines Bundeslands, Urlaub, halben Tagen, krank, frei,
  // Fortbildung und Wochenenden; jeder Monat nennt seine Einträge in Worten. Eingeben per Klick auf einen Tag oder Ziehen
  // über mehrere Tage (auch über Monatsgrenzen); rechts steht die Auswahl mit ihrer Wirkung und wird dort eingetragen.
  import { untrack } from "svelte";
  import { HEUTE, ICH } from "../../beispiel/daten";
  import { dauer } from "../../beispiel/format";
  import type { Abwesenheit, AbwesenheitArt } from "../../modell";
  import { spanne, tageZahl } from "./anzeige";
  import { ARTEN, feiertage, kalenderwoche, MONATE, plusTage, tageImMonat, tageVonBis, urlaubstage, wirkung, wochentag } from "./regeln";
  import { abwesenheitEintragen, abwesenheitEntfernen, halbtage, kontoVon, soll, zeit } from "./stand.svelte";

  let { entwurf = "" }: { entwurf?: string } = $props();

  const k = kontoVon(ICH)!;
  let jahr = $state(Number(HEUTE.slice(0, 4)));
  // svelte-ignore state_referenced_locally
  let auswahl = $state<{ von: string; bis: string } | null>(entwurf === "auswahl" ? { von: "2026-11-16", bis: "2026-11-20" } : null);
  let ziehen = $state<string | null>(null);
  let art = $state<AbwesenheitArt>("urlaub");
  let halb = $state(false);
  let notiz = $state("");

  const WT = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"];
  const WAHL: AbwesenheitArt[] = ["urlaub", "krank", "frei", "fortbildung"];
  const LEGENDE: AbwesenheitArt[] = ["urlaub", "halbtag", "krank", "frei", "fortbildung"];

  interface Zelle { tag: string | null; kw?: number }
  function wochen(monat: number): Zelle[][] {
    const erster = `${jahr}-${String(monat).padStart(2, "0")}-01`;
    const versatz = (wochentag(erster) + 6) % 7;
    const zellen: Zelle[] = Array.from({ length: versatz }, () => ({ tag: null }));
    for (let t = 1; t <= tageImMonat(jahr, monat); t++) zellen.push({ tag: `${jahr}-${String(monat).padStart(2, "0")}-${String(t).padStart(2, "0")}` });
    while (zellen.length < 42) zellen.push({ tag: null });
    const out: Zelle[][] = [];
    for (let w = 0; w < 6; w++) out.push(zellen.slice(w * 7, w * 7 + 7));
    return out;
  }

  function klasse(t: string): string {
    const s = soll(ICH, t)!;
    const teile: string[] = [];
    if (s.grund === "wochenende" || s.grund === "arbeitsfrei") teile.push("we");
    if (s.feiertag) teile.push("ft");
    if (s.abwesenheit) teile.push(`art-${s.abwesenheit.art}`);
    if (s.regel) teile.push("halb");
    if (t === HEUTE) teile.push("heute");
    if (auswahl && t >= auswahl.von && t <= auswahl.bis) teile.push("gewaehlt");
    return teile.join(" ");
  }
  function titel(t: string): string {
    const s = soll(ICH, t)!;
    const was = s.feiertag ?? (s.abwesenheit ? ARTEN[s.abwesenheit.art].name : s.regel ? `${s.regel}, halber Tag` : s.grund === "wochenende" ? "Wochenende" : s.grund === "arbeitsfrei" ? "kein Arbeitstag" : "Arbeitstag");
    return `${spanne(t, t)}: ${was}, Soll ${dauer(s.sollSek)}`;
  }

  /** Einträge eines Monats in Worten: Feiertage, Abwesenheiten (auf den Monat geschnitten), halbe Tage */
  function eintraege(monat: number): { tag: number; text: string; klasse: string }[] {
    const vonM = `${jahr}-${String(monat).padStart(2, "0")}-01`, bisM = `${jahr}-${String(monat).padStart(2, "0")}-${tageImMonat(jahr, monat)}`;
    const out: { tag: number; text: string; klasse: string }[] = [];
    for (const [t, name] of feiertage(jahr, k.bundesland)) if (t >= vonM && t <= bisM) out.push({ tag: Number(t.slice(8)), text: `${Number(t.slice(8))}. ${name}`, klasse: "ft" });
    for (const a of zeit.abwesenheiten.filter((x) => x.konto === ICH && x.von <= bisM && x.bis >= vonM)) {
      const v = a.von < vonM ? vonM : a.von, b = a.bis > bisM ? bisM : a.bis;
      const tg = v === b ? `${Number(v.slice(8))}.` : `${Number(v.slice(8))}. bis ${Number(b.slice(8))}.`;
      out.push({ tag: Number(v.slice(8)), text: `${tg} ${ARTEN[a.art].name}${a.notiz ? `, ${a.notiz}` : ""}`, klasse: `art-${a.art}` });
    }
    for (const r of halbtage(ICH)) if (r.monat === monat) out.push({ tag: r.tag, text: `${r.tag}. ${r.name}, halber Tag`, klasse: "halb" });
    return out.sort((a, b) => a.tag - b.tag);
  }

  function runter(t: string, e: PointerEvent): void {
    if (e.button !== 0) return;
    e.preventDefault();
    ziehen = t;
    auswahl = { von: t, bis: t };
  }
  function ueber(t: string): void {
    if (ziehen) auswahl = ziehen <= t ? { von: ziehen, bis: t } : { von: t, bis: ziehen };
  }
  // eine beim Öffnen schon gewählte Auswahl einmal ins Bild rollen
  $effect(() => {
    untrack(() => {
      const tag = auswahl ? document.querySelector(".pw-arbeitszeit-monat .tag.gewaehlt") : null;
      const feld = tag?.closest(".rollfeld");
      if (tag && feld) feld.scrollTop += tag.getBoundingClientRect().top - feld.getBoundingClientRect().top - feld.clientHeight / 2;
    });
  });
  $effect(() => {
    const los = () => (ziehen = null);
    addEventListener("pointerup", los);
    return () => removeEventListener("pointerup", los);
  });

  const neu = $derived<Abwesenheit | null>(auswahl ? { konto: ICH, von: auswahl.von, bis: auswahl.bis, art: art === "urlaub" && halb ? "halbtag" : art, notiz: notiz || undefined } : null);
  const w = $derived(neu ? wirkung(k, halbtage(ICH), neu) : null);
  const vorhanden = $derived(auswahl ? zeit.abwesenheiten.filter((a) => a.konto === ICH && a.von <= auswahl!.bis && a.bis >= auswahl!.von) : []);
  const genommen = $derived(urlaubstage(k, halbtage(ICH), zeit.abwesenheiten, jahr, HEUTE));
  const geplant = $derived(urlaubstage(k, halbtage(ICH), zeit.abwesenheiten, jahr, HEUTE, true));
  const frei = $derived(k.urlaubsanspruch + (jahr === Number(HEUTE.slice(0, 4)) ? k.resturlaubVorjahr : 0) - genommen - geplant);
  /** Urlaubstage, die die Auswahl neu belegt (vorhandener Urlaub im Bereich wird ersetzt) */
  const ersetzt = $derived(vorhanden.reduce((s, a) => s + wirkung(k, halbtage(ICH), a).urlaubstage, 0));

  const jahresTage = $derived.by(() => {
    const zaehl: Record<string, number> = {};
    for (const t of tageVonBis(`${jahr}-01-01`, `${jahr}-12-31`)) {
      const s = soll(ICH, t)!;
      if (s.abwesenheit && s.basisSek > 0) zaehl[s.abwesenheit.art] = (zaehl[s.abwesenheit.art] ?? 0) + (s.regel ? 0.5 : 1);
      if (s.grund === "feiertag") zaehl.feiertag = (zaehl.feiertag ?? 0) + 1;
    }
    return zaehl;
  });

  function eintragen(): void {
    if (!neu) return;
    abwesenheitEintragen(neu);
    auswahl = null; notiz = ""; halb = false;
  }
  function leeren(): void {
    for (const a of vorhanden) abwesenheitEntfernen(a);
    auswahl = null;
  }
</script>

<div class="spalten pw-arbeitszeit-spalten">
  <div class="rollfeld">
    <div class="pw-arbeitszeit-jahr">
      <button class="knopf symbol klein" title="Voriges Jahr" onclick={() => (jahr -= 1)}><i class="fa-solid fa-chevron-left"></i></button>
      <b class="zahl">{jahr}</b>
      <button class="knopf symbol klein" title="Nächstes Jahr" onclick={() => (jahr += 1)}><i class="fa-solid fa-chevron-right"></i></button>
      <span class="schwach klein">Feiertage {k.bundesland}</span>
    </div>
    <div class="pw-arbeitszeit-monate" class:zieht={!!ziehen}>
      {#each MONATE as name, i (name)}
        <section class="pw-arbeitszeit-monat" aria-label="{name} {jahr}">
          <h3>{name}</h3>
          <div class="gitter" role="grid">
            <span class="kw">KW</span>{#each WT as t (t)}<span class="wt">{t}</span>{/each}
            {#each wochen(i + 1) as reihe, r (r)}
              {@const erster = reihe.find((z) => z.tag)?.tag}
              <span class="kw">{erster ? kalenderwoche(erster) : ""}</span>
              {#each reihe as z, c (c)}
                {#if z.tag}
                  {@const tg = z.tag}
                  <button class="tag {klasse(tg)}" title={titel(tg)} onpointerdown={(e) => runter(tg, e)} onpointerenter={() => ueber(tg)}>{Number(tg.slice(8))}</button>
                {:else}<span class="tag leer"></span>{/if}
              {/each}
            {/each}
          </div>
          <ul class="worte">
            {#each eintraege(i + 1) as e, j (j)}<li class={e.klasse}>{e.text}</li>{/each}
          </ul>
        </section>
      {/each}
    </div>
  </div>

  <div class="rollfeld pw-arbeitszeit-seite">
    {#if auswahl && neu && w}
      <section class="bereich pw-arbeitszeit-auswahl pw-arbeitszeit-vorn">
        <div class="etikett">Auswahl</div>
        <h2>{spanne(auswahl.von, auswahl.bis)}</h2>
        <p class="schwach klein">{tageZahl(w.arbeitstage)} {w.arbeitstage === 1 ? "Arbeitstag" : "Arbeitstage"}, {tageVonBis(auswahl.von, auswahl.bis).length} Kalendertage</p>
        <div class="stufen" role="group" aria-label="Art">
          {#each WAHL as a (a)}<button class:an={art === a} title={ARTEN[a].wirkung} onclick={() => (art = a)}><i class="fa-solid {ARTEN[a].symbol}"></i> {ARTEN[a].name}</button>{/each}
        </div>
        {#if art === "urlaub"}
          <label class="pw-arbeitszeit-schalter"><button class="schalter" class:an={halb} aria-pressed={halb} aria-label="Halber Tag" onclick={() => (halb = !halb)}></button>
            Halbe Tage <span class="schwach klein">Soll und Urlaub je Tag halb</span></label>
        {/if}
        <input class="eingabe" bind:value={notiz} placeholder="Notiz, etwa Messe oder Sommer" />
        <div class="pw-arbeitszeit-wirkung">
          <div class="zeile-wert"><span>Soll</span><b class="zahl">-{dauer(w.sollSek)}</b></div>
          {#if ARTEN[neu.art].urlaub > 0}
            <div class="zeile-wert"><span>Urlaubstage</span><b class="zahl">{tageZahl(w.urlaubstage)}</b></div>
            <div class="zeile-wert"><span>Frei verplanbar danach</span><b class="zahl" class:minus={frei + ersetzt - w.urlaubstage < 0}>{tageZahl(frei + ersetzt - w.urlaubstage)} von {tageZahl(frei)}</b></div>
          {/if}
          <p class="schwach klein">{ARTEN[neu.art].wirkung}.{vorhanden.length ? ` Ersetzt ${vorhanden.map((a) => ARTEN[a.art].name).join(", ")} in diesem Zeitraum.` : ""}</p>
        </div>
        <div class="knoepfe">
          <button class="knopf haupt" disabled={w.arbeitstage === 0} onclick={eintragen}><i class="fa-solid fa-check"></i>Eintragen</button>
          {#if vorhanden.length}<button class="knopf gefahr" onclick={leeren} title="Abwesenheiten in der Auswahl entfernen (Rückgängig möglich)">Leeren</button>{/if}
          <button class="knopf ohne" onclick={() => (auswahl = null)}>Aufheben</button>
        </div>
      </section>
    {:else}
      <div class="hinweis pw-arbeitszeit-vorn"><i class="fa-solid fa-hand-pointer"></i><div>Einen Tag anklicken oder mit gedrückter Maustaste über mehrere Tage ziehen; die Auswahl erscheint dann hier zum Eintragen.</div></div>
    {/if}

    <section class="bereich">
      <div class="etikett">Legende</div>
      <ul class="pw-arbeitszeit-legende">
        <li><span class="muster"></span>Arbeitstag</li>
        <li><span class="muster we"></span>Wochenende, frei</li>
        <li><span class="muster ft"></span>Feiertag</li>
        <li><span class="muster halb"></span>Halber Tag</li>
        {#each LEGENDE as a (a)}<li><span class="muster art-{a}"></span>{ARTEN[a].name}</li>{/each}
        <li><span class="muster heute"></span>Heute</li>
      </ul>
    </section>

    <section class="bereich">
      <div class="etikett">{jahr} in Tagen</div>
      <div class="pw-arbeitszeit-wirkung">
        <div class="zeile-wert"><span>Urlaub genommen</span><b class="zahl">{tageZahl(genommen)}</b></div>
        <div class="zeile-wert"><span>Urlaub geplant</span><b class="zahl">{tageZahl(geplant)}</b></div>
        <div class="zeile-wert"><span>Frei verplanbar</span><b class="zahl">{tageZahl(frei)}</b></div>
        <div class="zeile-wert"><span>Krank</span><b class="zahl">{tageZahl(jahresTage.krank ?? 0)}</b></div>
        <div class="zeile-wert"><span>Fortbildung</span><b class="zahl">{tageZahl(jahresTage.fortbildung ?? 0)}</b></div>
        <div class="zeile-wert"><span>{ARTEN.frei.name}</span><b class="zahl">{tageZahl(jahresTage.frei ?? 0)}</b></div>
        <div class="zeile-wert"><span>Feiertage an Arbeitstagen</span><b class="zahl">{jahresTage.feiertag ?? 0}</b></div>
      </div>
    </section>
  </div>
</div>
