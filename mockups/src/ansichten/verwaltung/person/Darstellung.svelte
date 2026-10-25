<script lang="ts">
  // Darstellung auf diesem Gerät: Thema (hell, dunkel, wie das System) und Schriftstufe (Klein ist die Vorgabe) mit
  // Vorschau einer echten Karte in jeder Stufe. Eine Wahrheit mit der Leiste der Entwürfe (darstellung.svelte.ts); die
  // Wahl gilt sofort für die ganze Seite und bleibt im Browser gemerkt.
  import { board, karte } from "../../../beispiel/stand.svelte";
  import Karte from "../../../board/Karte.svelte";
  import { darstellung, darstellungSetzen, type Schrift, type Thema } from "../../../darstellung.svelte";

  const THEMEN: [Thema, string, string][] = [["hell", "Hell", "fa-sun"], ["dunkel", "Dunkel", "fa-moon"], ["system", "Wie das System", "fa-desktop"]];
  const STUFEN: [Schrift, string, string][] = [
    ["klein", "Klein", "Vorgabe: viel auf einen Blick"],
    ["mittel", "Mittel", "Etwas größer, auch Etiketten und Zähler"],
    ["gross", "Groß", "Für Abstand zum Bildschirm"],
  ];
  const probe = $derived(karte("c-131"));
  const probeBoard = $derived(board("b-prod"));
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
      <h2 class="etikett">Schriftstufe</h2>
      <p class="pw-verwaltung-satz">Ändert alle Schriften und Abstände zusammen, nie einzeln. Die Vorschau zeigt dieselbe Karte in jeder Stufe.</p>
      <div class="wahl pw-verwaltung-wahl pw-verwaltung-stufenwahl" role="radiogroup" aria-label="Schriftstufe">
        {#each STUFEN as [s, name, text] (s)}
          <label class:an={darstellung.schrift === s}>
            <input type="radio" name="schriftstufe" value={s} checked={darstellung.schrift === s} onchange={() => darstellungSetzen({ schrift: s })} />
            <span class="kreis"></span>
            <div><b>{name}</b><span>{text}</span>
              {#if probe}<div class="pw-verwaltung-probe" data-schrift={s} inert><Karte karte={probe} board={probeBoard} /></div>{/if}</div>
          </label>
        {/each}
      </div>
    </section>
  </div>
</div>
