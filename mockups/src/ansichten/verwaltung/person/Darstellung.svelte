<script lang="ts">
  // Darstellung auf diesem Gerät: Thema (hell, dunkel, wie das System) und Schriftstufe (Klein ist die Vorgabe) mit
  // Vorschau einer echten Karte in jeder Stufe. Die Wahl gilt sofort für die ganze Seite; in der App merkt sie sich die
  // Anzeige des Appkerns im Browser, hier gilt sie bis zum Neuladen.
  import { onMount } from "svelte";
  import { board, karte } from "../../../beispiel/stand.svelte";
  import Karte from "../../../board/Karte.svelte";

  type Thema = "hell" | "dunkel" | "system";
  const THEMEN: [Thema, string, string][] = [["hell", "Hell", "fa-sun"], ["dunkel", "Dunkel", "fa-moon"], ["system", "Wie das System", "fa-desktop"]];
  const STUFEN = [
    ["klein", "Klein", "Vorgabe: viel auf einen Blick"],
    ["mittel", "Mittel", "Etwas größer, auch Etiketten und Zähler"],
    ["gross", "Groß", "Für Abstand zum Bildschirm"],
  ] as const;

  const wurzel = document.documentElement;
  let thema = $state<Thema>(wurzel.dataset.theme === "hell" ? "hell" : "dunkel");
  let schrift = $state(wurzel.dataset.schrift ?? "klein");
  const probe = karte("c-131")!;
  const probeBoard = board("b-prod");

  // Thema und Stufe können sich auch anderswo ändern (Leiste der Entwürfe): die Wahl hier folgt
  onMount(() => {
    const beobachter = new MutationObserver(() => {
      const t = wurzel.dataset.theme;
      if (thema !== "system" && (t === "hell" || t === "dunkel")) thema = t;
      schrift = wurzel.dataset.schrift ?? "klein";
    });
    beobachter.observe(wurzel, { attributes: true, attributeFilter: ["data-theme", "data-schrift"] });
    return () => beobachter.disconnect();
  });

  function themaSetzen(t: Thema): void {
    thema = t;
    const dunkel = t === "dunkel" || (t === "system" && matchMedia("(prefers-color-scheme: dark)").matches);
    wurzel.dataset.theme = dunkel ? "dunkel" : "hell";
  }
</script>

<div class="rollfeld">
  <div class="pw-verwaltung-flaeche">
    <section class="bereich">
      <h2 class="etikett">Thema</h2>
      <span class="stufen" role="radiogroup" aria-label="Thema">
        {#each THEMEN as [t, name, symbol] (t)}
          <button role="radio" aria-checked={thema === t} class:an={thema === t} onclick={() => themaSetzen(t)}><i class="fa-solid {symbol}"></i> {name}</button>
        {/each}
      </span>
      <p class="pw-verwaltung-satz">Gilt auf diesem Gerät. Wie das System folgt der Einstellung des Rechners, auch wenn sie abends wechselt.</p>
    </section>

    <section class="bereich">
      <h2 class="etikett">Schriftstufe</h2>
      <p class="pw-verwaltung-satz">Ändert alle Schriften und Abstände zusammen, nie einzeln. Die Vorschau zeigt dieselbe Karte in jeder Stufe.</p>
      <div class="wahl pw-verwaltung-wahl pw-verwaltung-stufenwahl" role="radiogroup" aria-label="Schriftstufe">
        {#each STUFEN as [s, name, text] (s)}
          <label class:an={schrift === s}>
            <input type="radio" name="schriftstufe" value={s} checked={schrift === s} onchange={() => { schrift = s; wurzel.dataset.schrift = s; }} />
            <span class="kreis"></span>
            <div><b>{name}</b><span>{text}</span>
              <div class="pw-verwaltung-probe" data-schrift={s} inert><Karte karte={probe} board={probeBoard} /></div></div>
          </label>
        {/each}
      </div>
    </section>
  </div>
</div>
