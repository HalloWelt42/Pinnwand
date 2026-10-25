<script lang="ts">
  // Board anlegen (/boards/neu) als sichtbare Schritte: links wählen, rechts die Vorschau des Boards. Vorlage (eigene
  // zuerst, dazu leer anfangen), Name und Kürzel (Vorschlag aus dem Namen; beim Tippen sofort gegen deine Boards geprüft
  // und nach einer kurzen Pause am Server gegen alle, auch die, die du nicht siehst), Ordner, Mitglieder (freiwillig,
  // per Kontoname der Kellerwolke). "Board anlegen" ruft den Anwendungsfall; wer anlegt, ist Besitzer.
  import { kellerwolkePersonen, kuerzelPruefen, kuerzelVorschlag } from "../../daten/abfragen";
  import {
    boardAnlegen, kontonameOk, kuerzelAmServer, neueBoardFarbe, personAusText, type Einladung, type KuerzelAntwort,
  } from "../../daten/anwendung/boards.svelte";
  import { kuerzelSaeubern } from "../../regeln/kuerzel";
  import { ICH } from "../../daten/ich";
  import { konto, stand } from "../../daten/stand.svelte";
  import Person from "../../board/Person.svelte";
  import type { KellerwolkePerson, Vorlage } from "../../modell";
  import Personenwahl from "../../teile/Personenwahl.svelte";
  import { boardPfad, gehe } from "../../weg.svelte";
  import BoardVorschau from "./BoardVorschau.svelte";

  /** die mitgelieferte Vorlage "Leer anfangen" (Kennung im Server) */
  const LEER = "v-leer";
  /** so lange Ruhe beim Tippen, bis das Kürzel am Server geprüft wird (Millisekunden) */
  const PAUSE_MS = 350;

  /** eigene Vorlagen zuerst, dann die mitgelieferten, "Leer anfangen" zuletzt (alle vom Server) */
  const rang = (v: Vorlage) => (v.id === LEER ? 2 : v.eigen ? 0 : 1);
  const geordnet = (liste: Vorlage[]) => [...liste].sort((a, b) => rang(a) - rang(b));
  const vorlagen = $derived(geordnet(stand.vorlagen));
  const person = (id: string): KellerwolkePerson => ({ kennung: konto(id).kellerwolke, name: konto(id).name, konto: id });

  /** vorgewählt: die erste der Liste */
  let vorlageId = $state(geordnet(stand.vorlagen)[0]?.id ?? "");
  let name = $state("");
  let kuerzelEigen = $state<string | null>(null);
  /** persönlicher Ordner, leer: ohne Ordner */
  let ordner = $state("");
  let einladungen = $state<Einladung[]>([]);
  let suche = $state("");

  const gewaehlt = $derived(vorlagen.find((v) => v.id === vorlageId) ?? vorlagen[0]);
  /** die Vorlage, wie das Board entsteht: nur mit den Modulen, die diese Fassung anbietet (wie der Server) */
  const vorlage = $derived({ ...gewaehlt, module: gewaehlt.module.filter((m) => stand.moduleDa.includes(m)) });
  const vorgeschlagen = $derived(kuerzelVorschlag(name));
  const kuerzel = $derived(kuerzelEigen ?? vorgeschlagen);
  const lokal = $derived(kuerzelPruefen(kuerzel, name));
  // frei unter deinen Boards: nach einer Pause fragt der Server, ob ein Board, das du nicht siehst, es schon trägt
  let amServer = $state<KuerzelAntwort | null>(null);
  $effect(() => {
    if (lokal.stand !== "frei") return;
    const k = kuerzel;
    const zeit = setTimeout(async () => {
      const a = await kuerzelAmServer(k);
      if (a) amServer = a;
    }, PAUSE_MS);
    return () => clearTimeout(zeit);
  });
  /** die Antwort des Servers gilt nur für das Kürzel, nach dem gefragt wurde */
  const pruefung = $derived(lokal.stand === "frei" && amServer?.kuerzel === kuerzel ? amServer : lokal);
  const nameOk = $derived(!!name.trim());
  const fertig = $derived(nameOk && pruefung.stand === "frei");
  const fehlt = $derived(!nameOk ? "ein Name" : pruefung.stand !== "frei" ? "ein freies Kürzel" : "");
  const ordnerName = $derived(stand.ordner.find((o) => o.id === ordner)?.name ?? "Ohne Ordner");
  const mitglieder = $derived([person(ICH), ...einladungen.map((x) => x.person)]);
  const mitModulen = $derived(stand.moduleDa.length > 0);
  // einladen: aus den Vorschlägen oder der Kontoname, wie er im Feld steht
  const getippt = $derived(suche.trim());
  const nameFalsch = $derived(!!getippt && !kontonameOk(getippt));
  const schonDabei = $derived(!!getippt && (getippt === konto(ICH).kellerwolke || einladungen.some((x) => x.person.kennung === getippt)));
  function hinzu(p: KellerwolkePerson): void {
    if (p.kennung === konto(ICH).kellerwolke || einladungen.some((x) => x.person.kennung === p.kennung)) return;
    einladungen = [...einladungen, { person: p, rolle: "mitglied" }];
  }
  function getipptHinzu(): void {
    if (!getippt || nameFalsch) return;
    hinzu(personAusText(getippt, kellerwolkePersonen()));
    suche = "";
  }

  function kuerzelTippen(e: Event): void {
    const feld = e.currentTarget as HTMLInputElement;
    const k = kuerzelSaeubern(feld.value);
    feld.value = k;
    kuerzelEigen = k === vorgeschlagen ? null : k;
  }
  async function anlegen(): Promise<void> {
    const b = await boardAnlegen({ vorlage, name, kuerzel, ordner, einladungen });
    if (b) gehe(boardPfad(b.kuerzel));
  }
</script>

<div class="rahmen-kopf">
  <div class="seitenkopf">
    <h1>Board anlegen</h1>
    <div class="unterzeile">Links wählen, rechts entsteht das Board. Alles außer dem Kürzel änderst du später in den Einstellungen des Boards.</div>
  </div>
</div>
<div class="spalten breit-rechts pw-verwaltung-anlegen">
  <div class="rollfeld">
    <ol class="pw-verwaltung-schritte">
      <li class="bereich">
        <h2><span class="pw-verwaltung-nr fertig" aria-label="erledigt"><i class="fa-solid fa-check"></i></span>Vorlage</h2>
        <div class="wahl pw-verwaltung-wahl pw-verwaltung-vorlagen" role="radiogroup" aria-label="Vorlage">
          {#each vorlagen as v (v.id)}
            <label class:an={vorlageId === v.id}>
              <input type="radio" name="vorlage" value={v.id} bind:group={vorlageId} /><span class="kreis"></span>
              <div><b><i class="fa-solid {v.symbol}"></i>{v.name}{#if v.eigen}<span class="zustand wartet">Eigene Vorlage</span>{/if}</b>
                <span>{v.beschreibung}</span>
                <span class="pw-verwaltung-reihe">{v.spalten.map((s) => s.name).join(", ")}</span></div>
            </label>
          {/each}
        </div>
      </li>

      <li class="bereich">
        <h2><span class="pw-verwaltung-nr" class:fertig aria-label={fertig ? "erledigt" : "offen"}>{#if fertig}<i class="fa-solid fa-check"></i>{:else}2{/if}</span>Name und Kürzel</h2>
        <div class="pw-verwaltung-raster">
          <label for="neu-name">Name</label>
          <input id="neu-name" class="eingabe" bind:value={name} placeholder="etwa Werkstatt Halle 2" />
          <label for="neu-kuerzel">Kürzel</label>
          <div class="pw-verwaltung-formular">
            <input id="neu-kuerzel" class="eingabe pw-verwaltung-kuerzelfeld" value={kuerzel} oninput={kuerzelTippen} maxlength="6"
                   aria-invalid={pruefung.stand !== "frei"} aria-describedby="neu-kuerzel-meldung" />
            {#if kuerzelEigen !== null && vorgeschlagen && kuerzelEigen !== vorgeschlagen}
              <button class="knopf ohne klein" onclick={() => (kuerzelEigen = null)}><i class="fa-solid fa-rotate-left"></i>Vorschlag {vorgeschlagen}</button>
            {/if}
          </div>
        </div>
        <div id="neu-kuerzel-meldung" class="hinweis {pruefung.stand === 'frei' ? 'erfolg' : pruefung.stand === 'vergeben' ? 'gefahr' : 'warnung'}" aria-live="polite">
          <i class="fa-solid {pruefung.stand === 'frei' ? 'fa-circle-check' : 'fa-triangle-exclamation'}"></i>
          <div>{pruefung.text}{pruefung.frei.length ? " Frei wären:" : ""}</div>
          {#if pruefung.frei.length}
            <span class="rechts">{#each pruefung.frei as f (f)}<button class="chip pw-verwaltung-kuerzelchip" onclick={() => (kuerzelEigen = f)}>{f}</button>{/each}</span>
          {/if}
        </div>
        <p class="pw-verwaltung-satz">Das Kürzel steht vor jeder Kartennummer und in der Adresse; es bleibt fest, auch wenn du das Board umbenennst, und ist
          über alle Boards eindeutig. Nur Großbuchstaben und Ziffern, Umlaute werden ausgeschrieben: aus Übergabe wird UEBE.</p>
      </li>

      <li class="bereich">
        <h2><span class="pw-verwaltung-nr fertig" aria-label="erledigt"><i class="fa-solid fa-check"></i></span>Ordner</h2>
        <span class="stufen" role="radiogroup" aria-label="Ordner">
          {#each stand.ordner as o (o.id)}
            <button role="radio" aria-checked={ordner === o.id} class:an={ordner === o.id} onclick={() => (ordner = o.id)}><i class="fa-solid fa-folder"></i> {o.name}</button>
          {/each}
          <button role="radio" aria-checked={ordner === ""} class:an={ordner === ""} onclick={() => (ordner = "")}>Ohne Ordner</button>
        </span>
        <p class="pw-verwaltung-satz">Ein Ordner ordnet nur deine Seitenleiste; er trägt keine Rechte, die anderen sortieren für sich.</p>
      </li>

      <li class="bereich">
        <h2><span class="pw-verwaltung-nr">4</span>Mitglieder einladen <span class="schwach pw-verwaltung-frei">freiwillig</span></h2>
        <div class="pw-verwaltung-eingeladen">
          <div class="zeile"><Person id={ICH} /><span class="wer"><b>{konto(ICH).name} (du)</b></span><span class="zustand"><i class="fa-solid fa-crown"></i>Besitzer</span></div>
          {#each einladungen as x, i (x.person.kennung)}
            <div class="zeile">
              {#if x.person.konto}<Person id={x.person.konto} />{:else}<span class="pw-personenwahl-neu"><i class="fa-solid fa-user"></i></span>{/if}
              <span class="wer"><b>{x.person.name}</b><span class="pw-schluessel">{x.person.kennung}</span>
                {#if !x.person.konto}<span class="zustand wartet"><i class="fa-solid fa-user-clock"></i>sieht es ab der ersten Anmeldung</span>{/if}</span>
              <select class="eingabe" bind:value={einladungen[i].rolle} aria-label="Rolle von {x.person.name}">
                <option value="besitzer">Besitzer</option><option value="mitglied">Mitglied</option><option value="leser">Leser</option>
              </select>
              <button class="knopf ohne symbol klein" title="{x.person.name} nicht einladen" aria-label="{x.person.name} nicht einladen"
                      onclick={() => (einladungen = einladungen.filter((y) => y.person.kennung !== x.person.kennung))}><i class="fa-solid fa-xmark"></i></button>
            </div>
          {/each}
        </div>
        <div class="pw-verwaltung-formular">
          <Personenwahl bind:text={suche} kandidaten={kellerwolkePersonen().filter((p) => !einladungen.some((x) => x.person.kennung === p.kennung))}
                        ausser={[ICH]} platzhalter="Kontoname in der Kellerwolke" waehlen={hinzu} />
          <button class="knopf" title={nameFalsch ? "Das ist kein Kontoname der Kellerwolke; wähle die Person aus den Vorschlägen" : undefined}
                disabled={!getippt || nameFalsch || schonDabei} onclick={getipptHinzu}><i class="fa-solid fa-user-plus"></i>Hinzufügen</button>
        </div>
        {#if nameFalsch && !/\s/.test(getippt)}
          <span class="pw-verwaltung-fehler" role="alert">"{getippt}" ist kein Kontoname der Kellerwolke: nur Buchstaben, Ziffern, Punkt, Bindestrich,
            Unterstrich und @, ohne Leerzeichen.</span>
        {/if}
        <p class="pw-verwaltung-satz">Eingeladen wird mit dem Kontonamen der Kellerwolke; bekannte Personen erscheinen beim Tippen als Vorschlag.
          Wer schon angemeldet war, sieht das Board sofort, alle anderen ab ihrer ersten Anmeldung. Weitere Rollen legst du danach in den
          Einstellungen an.</p>
      </li>
    </ol>

    <div class="pw-verwaltung-abschluss">
      <span class="klein leise">{nameOk ? name.trim() : "Das Board"} mit {vorlage.spalten.length} Spalten{#if mitModulen}, {vorlage.module.length}
        {vorlage.module.length === 1 ? "Modul" : "Modulen"}{/if} und {mitglieder.length} {mitglieder.length === 1 ? "Mitglied" : "Mitgliedern"}{fehlt ? `; es fehlt noch ${fehlt}.` : "."}</span>
      <a class="knopf ohne" href="/heute">Abbrechen</a>
      <button class="knopf haupt" disabled={!fertig} onclick={anlegen}><i class="fa-solid fa-plus"></i>Board anlegen</button>
    </div>
  </div>
  <aside class="rollfeld" aria-label="Vorschau">
    <BoardVorschau {name} {kuerzel} farbe={neueBoardFarbe()} ordner={ordnerName} {vorlage} {mitglieder} />
  </aside>
</div>
