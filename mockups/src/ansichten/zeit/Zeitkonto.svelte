<script lang="ts">
  // Zeitkonto: Soll und Ist heute, in der Woche, im Monat und im Jahr, Überstunden und Resturlaub; darunter die Monate
  // mit laufendem Saldo und die Einstellungen des Kontos. Ist ist die gebuchte Zeit aus allen Boards, Soll entsteht je Tag
  // aus Wochenstunden, Arbeitstagen, Feiertagen des Bundeslands, halben Tagen und Abwesenheiten (Regeln in regeln.ts).
  import { HEUTE, ICH } from "../../beispiel/daten";
  import { datum, dauer } from "../../beispiel/format";
  import { datumJahr, differenz, tageZahl } from "./anzeige";
  import DatumFeld from "./DatumFeld.svelte";
  import { BUNDESLAENDER, MONATE, montagDer, plusTage, TAGNAMEN, urlaubstage, ARTEN } from "./regeln";
  import { halbtage, istAm, istBereich, kontoVon, laufend, monatsende, saldo, soll, sollBereich, zeit } from "./stand.svelte";

  let { entwurf: _entwurf = "" }: { entwurf?: string } = $props();

  const k = kontoVon(ICH)!;
  const jahr = Number(HEUTE.slice(0, 4));
  const gestern = plusTage(HEUTE, -1);
  const montag = montagDer(HEUTE);
  const monat = Number(HEUTE.slice(5, 7));
  const lauf = $derived(laufend(ICH));

  const heute = $derived({ ist: istAm(ICH, HEUTE), soll: soll(ICH, HEUTE)?.sollSek ?? 0 });
  const woche = $derived({ ist: istBereich(ICH, montag, plusTage(montag, 6)), soll: sollBereich(ICH, montag, plusTage(montag, 6)) });
  const imMonat = $derived({ ist: istBereich(ICH, HEUTE.slice(0, 8) + "01", monatsende(jahr, monat)), soll: sollBereich(ICH, HEUTE.slice(0, 8) + "01", monatsende(jahr, monat)) });
  const imJahr = $derived({ ist: istBereich(ICH, `${jahr}-01-01`, `${jahr}-12-31`), soll: sollBereich(ICH, `${jahr}-01-01`, `${jahr}-12-31`) });
  const ueber = $derived(saldo(ICH, gestern));
  const genommen = $derived(urlaubstage(k, halbtage(ICH), zeit.abwesenheiten, jahr, HEUTE));
  const geplant = $derived(urlaubstage(k, halbtage(ICH), zeit.abwesenheiten, jahr, HEUTE, true));
  const rest = $derived(k.urlaubsanspruch + k.resturlaubVorjahr - genommen);

  /** Monate mit Soll, Ist und laufendem Saldo; der laufende Monat bis gestern, spätere nur mit Soll */
  const monate = $derived.by(() => {
    let lauf = 0;
    return MONATE.map((name, i) => {
      const von = `${jahr}-${String(i + 1).padStart(2, "0")}-01`;
      const ende = monatsende(jahr, i + 1);
      const bis = ende < gestern ? ende : gestern;
      if (von > gestern) return { name, teil: "", sollSek: sollBereich(ICH, von, ende), ist: null, diff: null, saldo: null };
      const s = sollBereich(ICH, von, bis), ist = istBereich(ICH, von, bis);
      lauf += ist - s;
      return { name, teil: bis < ende ? `bis ${datum(bis)}` : "", sollSek: s, ist, diff: ist - s, saldo: lauf };
    });
  });

  // Einstellungen: ein Entwurf des Kontos, der ab einem Tag gilt (frühere Tage behalten ihr Soll)
  let wochenstunden = $state(String(k.wochenstunden));
  let tage = $state([...k.tage]);
  let land = $state(k.bundesland);
  let anspruch = $state(String(k.urlaubsanspruch));
  let vorjahr = $state(String(k.resturlaubVorjahr));
  let halbe = $state(halbtage(ICH).map((r) => ({ ...r })));
  let giltAb = $state(plusTage(montag, 7));
  let neuTag = $state("");
  let neuName = $state("");
  const jeTag = $derived(tage.length ? (Number(wochenstunden.replace(",", ".")) * 3600) / tage.length : 0);
  const geaendert = $derived(Number(wochenstunden.replace(",", ".")) !== k.wochenstunden || tage.join() !== k.tage.join() || land !== k.bundesland
    || Number(anspruch) !== k.urlaubsanspruch || Number(vorjahr) !== k.resturlaubVorjahr || halbe.length !== halbtage(ICH).length);
  const WOCHE = [1, 2, 3, 4, 5, 6, 0];

  function tagUmschalten(t: number): void {
    tage = tage.includes(t) ? tage.filter((x) => x !== t) : [...tage, t].sort();
  }
  function halbHinzu(): void {
    const m = neuTag.trim().match(/^(\d{1,2})\.(\d{1,2})\.?$/);
    if (!m) return;
    halbe = [...halbe, { tag: Number(m[1]), monat: Number(m[2]), name: neuName.trim() || "Halber Tag" }];
    neuTag = ""; neuName = "";
  }
  function speichern(): void {
    zeit.meldung = { text: `Zeitkonto gespeichert, gilt ab ${datumJahr(giltAb, true)}; frühere Tage behalten ihr Soll` };
  }
</script>

<div class="rollfeld pw-arbeitszeit-konto">
  <div class="kennzahlen">
    <div class="kennzahl" class:laeuft={!!lauf}><span>Heute</span><b>{dauer(heute.ist)}</b><small>von {dauer(heute.soll)} Soll{lauf ? ", Timer läuft" : ""}</small></div>
    <div class="kennzahl"><span>Woche</span><b>{dauer(woche.ist)}</b><small>von {dauer(woche.soll)} Soll</small></div>
    <div class="kennzahl"><span>{MONATE[monat - 1]}</span><b>{dauer(imMonat.ist)}</b><small>von {dauer(imMonat.soll)} Soll</small></div>
    <div class="kennzahl"><span>{jahr}</span><b>{dauer(imJahr.ist)}</b><small>von {dauer(imJahr.soll)} Soll</small></div>
    <div class="kennzahl" class:erfolg={ueber >= 0} class:fehler={ueber < 0} title="Ist minus Soll vom 1. Januar bis gestern"><span>Überstunden</span><b>{differenz(ueber)}</b><small>Stand {datum(gestern, true)} abends</small></div>
    <a class="kennzahl pw-zeiten-verweis" href="/arbeitszeit/urlaub" title="Anspruch {k.urlaubsanspruch} plus {k.resturlaubVorjahr} aus {jahr - 1}, genommen {tageZahl(genommen)}">
      <span>Resturlaub</span><b>{tageZahl(rest)} Tage</b><small>davon {tageZahl(geplant)} geplant, {tageZahl(rest - geplant)} frei</small></a>
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
                <td class="zahl" data-titel="Soll">{dauer(m.sollSek)}</td>
                <td class="zahl" data-titel="Ist">{m.ist === null ? "" : dauer(m.ist)}</td>
                <td class="zahl pw-arbeitszeit-diff" data-titel="Differenz" class:plus={(m.diff ?? 0) > 0} class:minus={(m.diff ?? 0) < 0}>{m.diff === null ? "" : differenz(m.diff)}</td>
                <td class="zahl" data-titel="Überstunden">{m.saldo === null ? "" : differenz(m.saldo)}</td>
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
      <div class="einstellung">
        <div><div class="name">Wochenstunden</div><div class="erklaerung">Soll der Woche, gleich verteilt auf die Arbeitstage</div></div>
        <div class="wert"><input class="eingabe" bind:value={wochenstunden} inputmode="decimal" /><span class="einheit">Std.</span></div>
      </div>
      <div class="einstellung">
        <div><div class="name">Arbeitstage</div><div class="erklaerung">Je Tag {dauer(jeTag)} Soll; andere Tage sind frei</div></div>
        <div class="wert"><div class="stufen" role="group" aria-label="Arbeitstage">
          {#each WOCHE as t (t)}<button class:an={tage.includes(t)} aria-pressed={tage.includes(t)} onclick={() => tagUmschalten(t)}>{TAGNAMEN[t]}</button>{/each}
        </div></div>
      </div>
      <div class="einstellung">
        <div><div class="name">Bundesland</div><div class="erklaerung">Bestimmt die Feiertage</div></div>
        <div class="wert"><select class="eingabe" bind:value={land}>{#each BUNDESLAENDER as b (b)}<option value={b}>{b}</option>{/each}</select></div>
      </div>
      <div class="einstellung">
        <div><div class="name">Urlaubsanspruch</div><div class="erklaerung">Tage im Jahr</div></div>
        <div class="wert"><input class="eingabe" bind:value={anspruch} inputmode="decimal" /><span class="einheit">Tage</span></div>
      </div>
      <div class="einstellung">
        <div><div class="name">Resturlaub {jahr - 1}</div><div class="erklaerung">Übertrag aus dem Vorjahr</div></div>
        <div class="wert"><input class="eingabe" bind:value={vorjahr} inputmode="decimal" /><span class="einheit">Tage</span></div>
      </div>
      <div class="einstellung">
        <div><div class="name">Halbe Tage</div><div class="erklaerung">Jedes Jahr ein halber Arbeitstag; Urlaub zählt dort halb</div></div>
        <div class="wert pw-arbeitszeit-halbe">
          {#each halbe as r, i (`${r.monat}-${r.tag}`)}
            <span class="chip">{r.tag}.{r.monat}. {r.name}
              <button class="knopf ohne symbol klein" title="Entfernen" onclick={() => (halbe = halbe.filter((_, j) => j !== i))}><i class="fa-solid fa-xmark"></i></button></span>
          {/each}
          <span class="pw-arbeitszeit-neu">
            <input class="eingabe" bind:value={neuTag} placeholder="TT.MM." title="Tag und Monat, etwa 11.11." />
            <input class="eingabe" bind:value={neuName} placeholder="Name" />
            <button class="knopf klein" disabled={!neuTag.trim()} onclick={halbHinzu}><i class="fa-solid fa-plus"></i>Tag</button>
          </span>
        </div>
      </div>
      <div class="pw-arbeitszeit-speichern">
        <span class="schwach klein">Gilt ab</span><DatumFeld tag={giltAb} ontag={(t) => (giltAb = t)} breite="170px" />
        <button class="knopf haupt" disabled={!geaendert} onclick={speichern} title="Frühere Tage behalten ihr Soll; das Saldo ändert sich nicht rückwirkend">Speichern</button>
      </div>
    </section>
  </div>
</div>
