<script lang="ts">
  // Darstellung auf diesem Gerät: Thema (hell, dunkel, wie das System), Vorlage des Aussehens (aus dem Appkern, nur auf
  // dem Rechner) und Schriftstufe (Klein ist die Vorgabe) mit Vorschau einer deiner Karten in jeder Stufe (ohne Karten
  // keine Vorschau). Thema und Schrift in darstellung.svelte.ts, die Vorlage im Baustein vorlage des Appkerns; jede
  // Wahl gilt sofort für die ganze Seite und bleibt im Browser gemerkt.
  import { VORLAGEN, vorlage, vorlageSetzen } from "appkern-oberflaeche";
  import { ICH } from "../../../daten/ich";
  import { board, stand } from "../../../daten/stand.svelte";
  import Karte from "../../../board/Karte.svelte";
  import { darstellung, darstellungSetzen, type Schrift, type Thema } from "../../../darstellung.svelte";

  const THEMEN: [Thema, string, string][] = [["hell", "Hell", "fa-sun"], ["dunkel", "Dunkel", "fa-moon"], ["system", "Wie das System", "fa-desktop"]];
  const STUFEN: [Schrift, string, string][] = [
    ["klein", "Klein", "Vorgabe: viel auf einen Blick"],
    ["mittel", "Mittel", "Etwas größer, auch Etiketten und Zähler"],
    ["gross", "Groß", "Für Abstand zum Bildschirm"],
  ];
  /** eine Karte, für die du zuständig bist, sonst irgendeine aus deinen Boards */
  const probe = $derived(stand.karten.find((k) => k.zustaendig.includes(ICH)) ?? stand.karten[0]);
  const probeBoard = $derived(probe ? board(probe.board) : undefined);
</script>

<div class="rollfeld">
  <div class="pw-verwaltung-flaeche">
    <section class="bereich">
      <h2 class="etikett">Thema</h2>
      <span class="stufen" role="radiogroup" aria-label="Thema">
        {#each THEMEN as [t, name, symbol] (t)}
          <button role="radio" aria-checked={darstellung.thema === t} class:an={darstellung.thema === t} onclick={() => darstellungSetzen({ thema: t })}>
            <i class="fa-solid {symbol}"></i> {name}</button>
        {/each}
      </span>
      <p class="pw-verwaltung-satz">Gilt auf diesem Gerät. Wie das System folgt der Einstellung des Rechners, auch wenn sie abends wechselt.</p>
    </section>

    <section class="bereich">
      <h2 class="etikett">Vorlage</h2>
      <p class="pw-verwaltung-satz">Ändert das ganze Aussehen: Flächen, Linien, Ecken und Schriften. Gilt auf diesem Gerät und nur auf dem
        Rechner ab 1000 Pixel Breite; am Telefon bleibt Klassisch.</p>
      <div class="wahl pw-verwaltung-wahl" role="radiogroup" aria-label="Vorlage">
        {#each VORLAGEN as v (v.id)}
          <label class:an={vorlage.wahl === v.id}>
            <input type="radio" name="vorlage" value={v.id} checked={vorlage.wahl === v.id} onchange={() => vorlageSetzen(v.id)} />
            <span class="kreis"></span>
            <div><b><i class="fa-solid {v.symbol}"></i> {v.name}</b><span>{v.text}</span></div>
          </label>
        {/each}
      </div>
    </section>

    <section class="bereich">
      <h2 class="etikett">Schriftstufe</h2>
      <p class="pw-verwaltung-satz">Ändert alle Schriften und Abstände zusammen, nie einzeln.{probe ? " Die Vorschau zeigt dieselbe Karte in jeder Stufe." : ""}</p>
      <div class="wahl pw-verwaltung-wahl pw-verwaltung-stufenwahl" role="radiogroup" aria-label="Schriftstufe">
        {#each STUFEN as [s, name, text] (s)}
          <label class:an={darstellung.schrift === s}>
            <input type="radio" name="schriftstufe" value={s} checked={darstellung.schrift === s} onchange={() => darstellungSetzen({ schrift: s })} />
            <span class="kreis"></span>
            <div><b>{name}</b><span>{text}</span>
              {#if probe && probeBoard}<div class="pw-verwaltung-probe" data-schrift={s} inert><Karte karte={probe} board={probeBoard} /></div>{/if}</div>
          </label>
        {/each}
      </div>
    </section>
  </div>
</div>
