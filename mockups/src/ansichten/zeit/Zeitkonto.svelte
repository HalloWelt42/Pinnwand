<script lang="ts">
  // Zeitkonto: Soll und Ist heute, in der Woche, im Monat und im Jahr, Überstunden und Resturlaub; darunter die Monate
  // mit laufendem Saldo und die Einstellungen des Kontos. Ist ist die gebuchte Zeit aus allen Boards, Soll entsteht je Tag
  // aus der dann gültigen Fassung des Zeitkontos (regeln/arbeitszeit.ts). Eine geänderte Einstellung ist eine neue
  // Fassung ab einem Tag; frühere Tage behalten ihr Soll.
  import { istAm, istBereich, saldo, sollBereich, sollTag, timerVon, urlaub } from "../../beispiel/abfragen";
  import { zeitkontoSpeichern } from "../../beispiel/anwendung/abwesenheiten.svelte";
  import { HEUTE, ICH } from "../../beispiel/daten";
  import { datum, datumJahr, dauer, differenz, tageZahl } from "../../beispiel/format";
  import { stand } from "../../beispiel/stand.svelte";
  import type { Halbtagsregel, Zeitkonto } from "../../modell";
  import { ARTEN, fassungAm } from "../../regeln/arbeitszeit";
  import { BUNDESLAENDER } from "../../regeln/feiertage";
  import { monatsende, MONATE, montagVon, plusTage, TAGE_KURZ, WOCHE_AB_MONTAG } from "../../regeln/tage";
  import DatumFeld from "../../teile/DatumFeld.svelte";

  let { entwurf: _entwurf = "" }: { entwurf?: string } = $props();

  const jahr = Number(HEUTE.slice(0, 4));
  const gestern = plusTage(HEUTE, -1);
  const montag = montagVon(HEUTE);
  const monat = Number(HEUTE.slice(5, 7));
  const k = $derived(fassungAm(stand.zeitkonten, ICH, HEUTE)!);
  const fassungen = $derived(stand.zeitkonten.filter((z) => z.konto === ICH).sort((a, b) => a.ab.localeCompare(b.ab)));
  const timer = $derived(timerVon(ICH));

  const heute = $derived({ ist: istAm(ICH, HEUTE), soll: sollTag(ICH, HEUTE)?.sollSek ?? 0 });
  const woche = $derived({ ist: istBereich(ICH, montag, plusTage(montag, 6)), soll: sollBereich(ICH, montag, plusTage(montag, 6)) });
  const imMonat = $derived({ ist: istBereich(ICH, HEUTE.slice(0, 8) + "01", monatsende(HEUTE)), soll: sollBereich(ICH, HEUTE.slice(0, 8) + "01", monatsende(HEUTE)) });
  const imJahr = $derived({ ist: istBereich(ICH, `${jahr}-01-01`, `${jahr}-12-31`), soll: sollBereich(ICH, `${jahr}-01-01`, `${jahr}-12-31`) });
  const ueber = $derived(saldo(ICH, gestern));
  const u = $derived(urlaub(ICH)!);

  /** Monate mit Soll, Ist und laufendem Saldo; der laufende Monat bis gestern, spätere nur mit Soll */
  const monate = $derived.by(() => {
    let lauf = 0;
    return MONATE.map((name, i) => {
      const von = `${jahr}-${String(i + 1).padStart(2, "0")}-01`;
      const ende = monatsende(von);
      const bis = ende < gestern ? ende : gestern;
      if (von > gestern) return { name, teil: "", sollSek: sollBereich(ICH, von, ende), ist: null, diff: null, saldo: null };
      const s = sollBereich(ICH, von, bis), ist = istBereich(ICH, von, bis);
      lauf += ist - s;
      return { name, teil: bis < ende ? `bis ${datum(bis)}` : "", sollSek: s, ist, diff: ist - s, saldo: lauf };
    });
  });

  // Einstellungen: der Entwurf einer neuen Fassung, ausgehend von der jüngsten; sie gilt ab dem gewählten Tag
  const jungste = $derived(fassungen[fassungen.length - 1]);
  // svelte-ignore state_referenced_locally
  let entwurfFassung = $state(neueFassung(fassungAm(stand.zeitkonten, ICH, "9999-12-31")!));
  let neuTag = $state("");
  let neuName = $state("");

  function neueFassung(z: Zeitkonto) {
    return { wochenstunden: String(z.wochenstunden), tage: [...z.tage], land: z.bundesland, anspruch: String(z.urlaubsanspruch),
             vorjahr: String(z.resturlaubVorjahr), halbe: z.halbtage.map((r) => ({ ...r })) as Halbtagsregel[],
             ab: plusTage(montag, 7) > z.ab ? plusTage(montag, 7) : plusTage(z.ab, 1) };
  }
  const zahl = (t: string) => Number(t.replace(",", "."));
  const jeTag = $derived(entwurfFassung.tage.length ? (zahl(entwurfFassung.wochenstunden) * 3600) / entwurfFassung.tage.length : 0);
  const gueltig = $derived(zahl(entwurfFassung.wochenstunden) >= 0 && zahl(entwurfFassung.anspruch) >= 0 && zahl(entwurfFassung.vorjahr) >= 0
    && !Number.isNaN(zahl(entwurfFassung.wochenstunden) + zahl(entwurfFassung.anspruch) + zahl(entwurfFassung.vorjahr)));
  const geaendert = $derived(!!jungste && (zahl(entwurfFassung.wochenstunden) !== jungste.wochenstunden || entwurfFassung.tage.join() !== jungste.tage.join()
    || entwurfFassung.land !== jungste.bundesland || zahl(entwurfFassung.anspruch) !== jungste.urlaubsanspruch
    || zahl(entwurfFassung.vorjahr) !== jungste.resturlaubVorjahr || JSON.stringify(entwurfFassung.halbe) !== JSON.stringify(jungste.halbtage)));

  function tagUmschalten(t: number): void {
    entwurfFassung.tage = entwurfFassung.tage.includes(t) ? entwurfFassung.tage.filter((x) => x !== t) : [...entwurfFassung.tage, t].sort();
  }
  function halbHinzu(): void {
    const m = neuTag.trim().match(/^(\d{1,2})\.(\d{1,2})\.?$/);
    if (!m) return;
    entwurfFassung.halbe = [...entwurfFassung.halbe, { tag: Number(m[1]), monat: Number(m[2]), name: neuName.trim() || "Halber Tag" }];
    neuTag = ""; neuName = "";
  }
  function speichern(): void {
    if (!gueltig) return;
    const f = $state.snapshot(entwurfFassung);
    zeitkontoSpeichern({ konto: ICH, ab: f.ab, wochenstunden: zahl(f.wochenstunden), tage: f.tage, bundesland: f.land,
      urlaubsanspruch: zahl(f.anspruch), resturlaubVorjahr: zahl(f.vorjahr), halbtage: f.halbe });
  }
</script>

<div class="rollfeld pw-arbeitszeit-konto">
  <div class="kennzahlen">
    <div class="kennzahl" class:laeuft={!!timer?.seit}><span>Heute</span><b>{dauer(heute.ist)}</b><small>von {dauer(heute.soll)} Soll{timer?.seit ? ", Timer läuft" : ""}</small></div>
    <div class="kennzahl"><span>Woche</span><b>{dauer(woche.ist)}</b><small>von {dauer(woche.soll)} Soll</small></div>
    <div class="kennzahl"><span>{MONATE[monat - 1]}</span><b>{dauer(imMonat.ist)}</b><small>von {dauer(imMonat.soll)} Soll</small></div>
    <div class="kennzahl"><span>{jahr}</span><b>{dauer(imJahr.ist)}</b><small>von {dauer(imJahr.soll)} Soll</small></div>
    <div class="kennzahl" class:erfolg={ueber >= 0} class:fehler={ueber < 0} title="Ist minus Soll vom 1. Januar bis gestern"><span>Überstunden</span><b>{differenz(ueber)}</b><small>Stand {datum(gestern, true)} abends</small></div>
    <a class="kennzahl pw-zeiten-verweis" href="/arbeitszeit/urlaub" title="Anspruch {k.urlaubsanspruch} plus {k.resturlaubVorjahr} aus {jahr - 1}, genommen {tageZahl(u.genommen)}">
      <span>Resturlaub</span><b>{tageZahl(u.anspruch - u.genommen)} Tage</b><small>davon {tageZahl(u.geplant)} geplant, {tageZahl(u.rest)} frei</small></a>
  </div>

  <div class="pw-arbeitszeit-paar">
    <section class="bereich">
      <h2 class="pw-arbeitszeit-titel">Monate {jahr}</h2>
      <div class="tabellen-raum">
        <table class="tabelle">
          <thead><tr><th>Monat</th><th class="zahl">Soll</th><th class="zahl">Ist</th><th class="zahl">Differenz</th><th class="zahl" title="Laufender Saldo seit Jahresbeginn">Überstunden</th></tr></thead>
          <tbody>
            {#each monate as m (m.name)}
              <tr class:spaeter={m.ist === null}>
                <td>{m.name} {#if m.teil}<span class="schwach">{m.teil}</span>{/if}{#if m.ist === null}<span class="schwach"> geplant</span>{/if}</td>
                <td class="zahl">{dauer(m.sollSek)}</td>
                <td class="zahl">{m.ist === null ? "" : dauer(m.ist)}</td>
                <td class="zahl pw-arbeitszeit-diff" class:plus={(m.diff ?? 0) > 0} class:minus={(m.diff ?? 0) < 0}>{m.diff === null ? "" : differenz(m.diff)}</td>
                <td class="zahl">{m.saldo === null ? "" : differenz(m.saldo)}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
      <p class="schwach klein pw-arbeitszeit-regel">Soll je Arbeitstag: Wochenstunden geteilt durch Arbeitstage. Feiertage in {k.bundesland}, Urlaub, Krank und
        Fortbildung 0, halbe Tage halb; {ARTEN.frei.name} lässt das Soll stehen und baut so Überstunden ab.</p>
    </section>

    <section class="bereich pw-arbeitszeit-einstellungen">
      <h2 class="pw-arbeitszeit-titel">Zeitkonto einstellen</h2>
      <div class="pw-arbeitszeit-fassungen" title="Jede Fassung gilt ab ihrem Tag bis zur nächsten">
        <span class="etikett">Fassungen</span>
        {#each fassungen as f (f.ab)}
          <span class="zustand" class:fertig={f.ab === k.ab}>ab {datumJahr(f.ab)}: {String(f.wochenstunden).replace(".", ",")} Std. an {f.tage.length} Tagen{f.ab === k.ab ? ", gilt heute" : ""}</span>
        {/each}
      </div>
      <div class="einstellung">
        <div><div class="name">Wochenstunden</div><div class="erklaerung">Soll der Woche, gleich verteilt auf die Arbeitstage</div></div>
        <div class="wert"><input class="eingabe" class:falsch={Number.isNaN(zahl(entwurfFassung.wochenstunden))} bind:value={entwurfFassung.wochenstunden} inputmode="decimal" /><span class="einheit">Std.</span></div>
      </div>
      <div class="einstellung">
        <div><div class="name">Arbeitstage</div><div class="erklaerung">Je Tag {dauer(jeTag)} Soll; andere Tage sind frei</div></div>
        <div class="wert"><div class="stufen" role="group" aria-label="Arbeitstage">
          {#each WOCHE_AB_MONTAG as t (t)}<button class:an={entwurfFassung.tage.includes(t)} aria-pressed={entwurfFassung.tage.includes(t)} onclick={() => tagUmschalten(t)}>{TAGE_KURZ[t]}</button>{/each}
        </div></div>
      </div>
      <div class="einstellung">
        <div><div class="name">Bundesland</div><div class="erklaerung">Bestimmt die Feiertage</div></div>
        <div class="wert"><select class="eingabe" bind:value={entwurfFassung.land}>{#each BUNDESLAENDER as b (b)}<option value={b}>{b}</option>{/each}</select></div>
      </div>
      <div class="einstellung">
        <div><div class="name">Urlaubsanspruch</div><div class="erklaerung">Tage im Jahr</div></div>
        <div class="wert"><input class="eingabe" class:falsch={Number.isNaN(zahl(entwurfFassung.anspruch))} bind:value={entwurfFassung.anspruch} inputmode="decimal" /><span class="einheit">Tage</span></div>
      </div>
      <div class="einstellung">
        <div><div class="name">Resturlaub {jahr - 1}</div><div class="erklaerung">Übertrag aus dem Vorjahr</div></div>
        <div class="wert"><input class="eingabe" class:falsch={Number.isNaN(zahl(entwurfFassung.vorjahr))} bind:value={entwurfFassung.vorjahr} inputmode="decimal" /><span class="einheit">Tage</span></div>
      </div>
      <div class="einstellung">
        <div><div class="name">Halbe Tage</div><div class="erklaerung">Jedes Jahr ein halber Arbeitstag; Urlaub zählt dort halb</div></div>
        <div class="wert pw-arbeitszeit-halbe">
          {#each entwurfFassung.halbe as r, i (`${r.monat}-${r.tag}`)}
            <span class="chip">{r.tag}.{r.monat}. {r.name}
              <button class="knopf ohne symbol klein" title="Entfernen" onclick={() => (entwurfFassung.halbe = entwurfFassung.halbe.filter((_, j) => j !== i))}><i class="fa-solid fa-xmark"></i></button></span>
          {/each}
          <span class="pw-arbeitszeit-neu">
            <input class="eingabe" bind:value={neuTag} placeholder="TT.MM." title="Tag und Monat, etwa 11.11." />
            <input class="eingabe" bind:value={neuName} placeholder="Name" />
            <button class="knopf klein" disabled={!neuTag.trim()} onclick={halbHinzu}><i class="fa-solid fa-plus"></i>Tag</button>
          </span>
        </div>
      </div>
      <div class="pw-arbeitszeit-speichern">
        <span class="schwach klein">Gilt ab</span><DatumFeld tag={entwurfFassung.ab} ontag={(t) => (entwurfFassung.ab = t)} breite="170px" />
        <button class="knopf haupt" disabled={!geaendert || !gueltig} onclick={speichern} title="Neue Fassung ab diesem Tag; frühere Tage behalten ihr Soll, das Saldo ändert sich nicht rückwirkend">Speichern</button>
      </div>
    </section>
  </div>
</div>
