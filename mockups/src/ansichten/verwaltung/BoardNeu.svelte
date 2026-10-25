<script lang="ts">
  // Board anlegen (/boards/neu) als sichtbare Schritte: links wählen, rechts die Vorschau des Boards. Vorlage (eigene
  // zuerst, dazu leer anfangen), Name und Kürzel (Vorschlag aus dem Namen, sofort auf Eindeutigkeit geprüft, über alle
  // Boards), Ordner, Mitglieder (freiwillig). Am Ende "Board anlegen"; wer anlegt, ist Besitzer.
  import { untrack } from "svelte";
  import { ICH, ORDNER, VORLAGEN } from "../../beispiel/daten";
  import { konto, stand } from "../../beispiel/stand.svelte";
  import Person from "../../board/Person.svelte";
  import type { Farbe } from "../../modell";
  import BoardVorschau from "./BoardVorschau.svelte";
  import { KENNUNGEN, KUERZEL_ANDERER, LEER_SPALTEN, VORLAGE_FELDER, type Vorschlag } from "./daten";
  import { pruefen, saeubern, vorschlag, type Belegung } from "./kuerzel";
  import Personenwahl from "./Personenwahl.svelte";

  let { entwurf = "" }: { entwurf?: string } = $props();

  const LEER = "leer";
  const vorlagen = [...VORLAGEN].sort((a, b) => Number(!!b.eigen) - Number(!!a.eigen));
  const belegt: Belegung = $derived({ boards: stand.boards, anderer: KUERZEL_ANDERER });
  /** ein neues Board bekommt die erste Farbe, die noch kein Board trägt (unterscheidbar in der Seitenleiste) */
  const NEU_FARBEN: Farbe[] = ["tuerkis", "himmel", "honig", "violett", "rose", "sand", "stahl", "koralle", "petrol", "minze", "flieder"];
  const farbe = $derived(NEU_FARBEN.find((f) => !stand.boards.some((b) => b.farbe === f)) ?? "tuerkis");
  const ICH_VORSCHLAG: Vorschlag = { kennung: KENNUNGEN[ICH], name: konto(ICH).name, konto: ICH };

  let vorlage = $state("v-werkstatt");
  let name = $state("");
  let kuerzelEigen = $state<string | null>(null);
  let ordner = $state("o-firma");
  let einladungen = $state<{ p: Vorschlag; rolle: string }[]>([]);
  let suche = $state("");

  // vorgeführte Zustände: Kürzel frei (Vorgabe) oder von Hand auf ein vergebenes gesetzt
  $effect(() => {
    const e = entwurf;
    untrack(() => {
      const vergeben = e === "kuerzel-vergeben";
      vorlage = vergeben ? "v-projekt" : "v-werkstatt";
      name = vergeben ? "Produktion Halle 2" : "Werkstatt Halle 2";
      kuerzelEigen = vergeben ? "PROD" : null;
      ordner = "o-firma";
      einladungen = [{ p: { kennung: KENNUNGEN["k-anna"], name: konto("k-anna").name, konto: "k-anna" }, rolle: "mitglied" }];
      suche = "";
    });
  });

  const gewaehlt = $derived(VORLAGEN.find((v) => v.id === vorlage));
  const spalten = $derived(gewaehlt?.spalten ?? LEER_SPALTEN);
  const module = $derived(gewaehlt?.module ?? []);
  const felder = $derived(VORLAGE_FELDER[vorlage] ?? []);
  const vorgeschlagen = $derived(vorschlag(name, belegt));
  const kuerzel = $derived(kuerzelEigen ?? vorgeschlagen);
  const pruefung = $derived(pruefen(kuerzel, name, belegt));
  const nameOk = $derived(!!name.trim());
  const fertig = $derived(nameOk && pruefung.stand === "frei");
  const fehlt = $derived(!nameOk ? "ein Name" : pruefung.stand !== "frei" ? "ein freies Kürzel" : "");
  const ordnerName = $derived(ORDNER.find((o) => o.id === ordner)?.name ?? "Ohne Ordner");
  const mitglieder = $derived([ICH_VORSCHLAG, ...einladungen.map((x) => x.p)]);

  function kuerzelTippen(e: Event): void {
    const feld = e.currentTarget as HTMLInputElement;
    const k = saeubern(feld.value);
    feld.value = k;
    kuerzelEigen = k === vorgeschlagen ? null : k;
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
            <label class:an={vorlage === v.id}>
              <input type="radio" name="vorlage" value={v.id} bind:group={vorlage} /><span class="kreis"></span>
              <div><b><i class="fa-solid {v.symbol}"></i>{v.name}{#if v.eigen}<span class="zustand wartet">Eigene Vorlage</span>{/if}</b>
                <span>{v.beschreibung}</span>
                <span class="pw-verwaltung-reihe">{v.spalten.join(", ")}</span></div>
            </label>
          {/each}
          <label class:an={vorlage === LEER}>
            <input type="radio" name="vorlage" value={LEER} bind:group={vorlage} /><span class="kreis"></span>
            <div><b><i class="fa-regular fa-square"></i>Leer anfangen</b>
              <span>Drei Spalten, ohne Module und Felder; alles Weitere stellst du selbst ein.</span>
              <span class="pw-verwaltung-reihe">{LEER_SPALTEN.join(", ")}</span></div>
          </label>
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
          {#each ORDNER as o (o.id)}
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
          {#each einladungen as x, i (x.p.kennung)}
            <div class="zeile">
              {#if x.p.konto}<Person id={x.p.konto} />{:else}<span class="pw-verwaltung-neuperson"><i class="fa-solid fa-user"></i></span>{/if}
              <span class="wer"><b>{x.p.name}</b><span class="pw-schluessel">{x.p.kennung}</span></span>
              <select class="eingabe" bind:value={einladungen[i].rolle} aria-label="Rolle von {x.p.name}">
                <option value="besitzer">Besitzer</option><option value="mitglied">Mitglied</option><option value="leser">Leser</option>
              </select>
              <button class="knopf ohne symbol klein" title="{x.p.name} nicht einladen" aria-label="{x.p.name} nicht einladen"
                      onclick={() => (einladungen = einladungen.filter((y) => y.p.kennung !== x.p.kennung))}><i class="fa-solid fa-xmark"></i></button>
            </div>
          {/each}
        </div>
        <Personenwahl bind:text={suche} ausser={[ICH, ...einladungen.map((x) => x.p.konto ?? "")]}
                      waehlen={(p) => { if (!einladungen.some((x) => x.p.kennung === p.kennung)) einladungen = [...einladungen, { p, rolle: "mitglied" }]; }} />
        <p class="pw-verwaltung-satz">Eingeladene sehen das Board sofort und bekommen einen Hinweis. Weitere Rollen legst du danach in den Einstellungen an.</p>
      </li>
    </ol>

    <div class="pw-verwaltung-abschluss">
      <span class="klein leise">{nameOk ? name.trim() : "Das Board"} mit {spalten.length} Spalten, {module.length} {module.length === 1 ? "Modul" : "Modulen"}
        und {mitglieder.length} {mitglieder.length === 1 ? "Mitglied" : "Mitgliedern"}{fehlt ? `; es fehlt noch ${fehlt}.` : "."}</span>
      <a class="knopf ohne" href="/heute">Abbrechen</a>
      <button class="knopf haupt" disabled={!fertig}><i class="fa-solid fa-plus"></i>Board anlegen</button>
    </div>
  </div>
  <aside class="rollfeld" aria-label="Vorschau">
    <BoardVorschau name={name} kuerzel={kuerzel} {farbe} ordner={ordnerName} {spalten} {module} {felder} {mitglieder} />
  </aside>
</div>
