<script lang="ts">
  // Board anlegen (/boards/neu) als sichtbare Schritte: links wählen, rechts die Vorschau des Boards. Vorlage (eigene
  // zuerst, dazu leer anfangen), Name und Kürzel (Vorschlag aus dem Namen, sofort auf Eindeutigkeit über alle Boards
  // geprüft), Ordner, Mitglieder (freiwillig). "Board anlegen" ruft den Anwendungsfall; wer anlegt, ist Besitzer.
  import { untrack } from "svelte";
  import { kellerwolkePersonen, kuerzelPruefen, kuerzelVorschlag } from "../../beispiel/abfragen";
  import { boardAnlegen, LEER_VORLAGE, neueBoardFarbe, type Einladung } from "../../beispiel/anwendung/boards.svelte";
  import { kuerzelSaeubern } from "../../regeln/kuerzel";
  import { ICH } from "../../beispiel/daten";
  import { konto, stand } from "../../beispiel/stand.svelte";
  import Person from "../../board/Person.svelte";
  import type { KellerwolkePerson } from "../../modell";
  import Personenwahl from "../../teile/Personenwahl.svelte";
  import { boardPfad, gehe } from "../../weg.svelte";
  import BoardVorschau from "./BoardVorschau.svelte";

  let { entwurf = "" }: { entwurf?: string } = $props();

  const vorlagen = $derived([...[...stand.vorlagen].sort((a, b) => Number(!!b.eigen) - Number(!!a.eigen)), LEER_VORLAGE]);
  const person = (id: string): KellerwolkePerson => ({ kennung: konto(id).kellerwolke, name: konto(id).name, konto: id });

  let vorlageId = $state("v-werkstatt");
  let name = $state("");
  let kuerzelEigen = $state<string | null>(null);
  let ordner = $state("o-firma");
  let einladungen = $state<Einladung[]>([]);
  let suche = $state("");

  // vorgeführte Zustände: Kürzel frei (Vorgabe) oder von Hand auf ein vergebenes gesetzt (einmal je Entwurf)
  $effect(() => {
    const e = entwurf;
    untrack(() => {
      const vergeben = e === "kuerzel-vergeben";
      vorlageId = vergeben ? "v-projekt" : "v-werkstatt";
      name = vergeben ? "Produktion Halle 2" : "Werkstatt Halle 2";
      kuerzelEigen = vergeben ? "PROD" : null;
      ordner = "o-firma";
      einladungen = [{ person: person("k-anna"), rolle: "mitglied" }];
      suche = "";
    });
  });

  const vorlage = $derived(vorlagen.find((v) => v.id === vorlageId) ?? LEER_VORLAGE);
  const vorgeschlagen = $derived(kuerzelVorschlag(name));
  const kuerzel = $derived(kuerzelEigen ?? vorgeschlagen);
  const pruefung = $derived(kuerzelPruefen(kuerzel, name));
  const nameOk = $derived(!!name.trim());
  const fertig = $derived(nameOk && pruefung.stand === "frei");
  const fehlt = $derived(!nameOk ? "ein Name" : pruefung.stand !== "frei" ? "ein freies Kürzel" : "");
  const ordnerName = $derived(stand.ordner.find((o) => o.id === ordner)?.name ?? "Ohne Ordner");
  const mitglieder = $derived([person(ICH), ...einladungen.map((x) => x.person)]);

  function kuerzelTippen(e: Event): void {
    const feld = e.currentTarget as HTMLInputElement;
    const k = kuerzelSaeubern(feld.value);
    feld.value = k;
    kuerzelEigen = k === vorgeschlagen ? null : k;
  }
  function anlegen(): void {
    const b = boardAnlegen({ vorlage, name, kuerzel, ordner, einladungen });
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
              <span class="wer"><b>{x.person.name}</b><span class="pw-schluessel">{x.person.kennung}</span></span>
              <select class="eingabe" bind:value={einladungen[i].rolle} aria-label="Rolle von {x.person.name}">
                <option value="besitzer">Besitzer</option><option value="mitglied">Mitglied</option><option value="leser">Leser</option>
              </select>
              <button class="knopf ohne symbol klein" title="{x.person.name} nicht einladen" aria-label="{x.person.name} nicht einladen"
                      onclick={() => (einladungen = einladungen.filter((y) => y.person.kennung !== x.person.kennung))}><i class="fa-solid fa-xmark"></i></button>
            </div>
          {/each}
        </div>
        <Personenwahl bind:text={suche} kandidaten={kellerwolkePersonen().filter((p) => !einladungen.some((x) => x.person.kennung === p.kennung))}
                      ausser={[ICH]} waehlen={(p) => (einladungen = [...einladungen, { person: p, rolle: "mitglied" }])} />
        <p class="pw-verwaltung-satz">Eingeladene sehen das Board sofort und bekommen einen Hinweis. Weitere Rollen legst du danach in den Einstellungen an.</p>
      </li>
    </ol>

    <div class="pw-verwaltung-abschluss">
      <span class="klein leise">{nameOk ? name.trim() : "Das Board"} mit {vorlage.spalten.length} Spalten, {vorlage.module.length}
        {vorlage.module.length === 1 ? "Modul" : "Modulen"} und {mitglieder.length} {mitglieder.length === 1 ? "Mitglied" : "Mitgliedern"}{fehlt ? `; es fehlt noch ${fehlt}.` : "."}</span>
      <a class="knopf ohne" href="/heute">Abbrechen</a>
      <button class="knopf haupt" disabled={!fertig} onclick={anlegen}><i class="fa-solid fa-plus"></i>Board anlegen</button>
    </div>
  </div>
  <aside class="rollfeld" aria-label="Vorschau">
    <BoardVorschau {name} {kuerzel} farbe={neueBoardFarbe()} ordner={ordnerName} {vorlage} {mitglieder} />
  </aside>
</div>
