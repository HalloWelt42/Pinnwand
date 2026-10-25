<script lang="ts">
  // Hinweise: je Art (zugewiesen, fällig, erwähnt, Kommentar, verschoben) und je Weg, den diese Pinnwand anbietet, ein
  // Schalter. Gilt am Konto, auf allen Geräten; jeder Schalter über den Anwendungsfall.
  import { artenDa, hinweisWegSetzen, wegAn, wegeDa } from "../../../daten/anwendung/hinweise.svelte";

  const arten = $derived(artenDa());
  const wege = wegeDa();
</script>

<div class="rollfeld">
  <div class="pw-verwaltung-flaeche">
    <section class="bereich">
      <h2 class="etikett">Welche Hinweise du bekommst</h2>
      <div class="tabellen-raum pw-verwaltung-tabelle">
        <table class="tabelle karten pw-verwaltung-hinweise">
          <thead><tr><th>Art</th>{#each wege as w (w.id)}<th class="haken" title={w.text}><i class="fa-solid {w.symbol}"></i> {w.name}</th>{/each}</tr></thead>
          <tbody>
            {#each arten as a (a.art)}
              <tr>
                <td><span class="pw-verwaltung-art"><i class="fa-solid {a.symbol}"></i><span><b>{a.name}</b><span class="pw-verwaltung-erklaerung">{a.text}</span></span></span></td>
                {#each wege as w (w.id)}
                  {@const an = wegAn(a.art, w.id)}
                  <td class="haken" data-titel={w.name}>
                    <button class="schalter" class:an aria-pressed={an} aria-label="{a.name}: {w.name}"
                            onclick={() => hinweisWegSetzen(a.art, w.id, !an)}></button>
                    <span class="pw-verwaltung-schalterwort">{an ? "an" : "aus"}</span>
                  </td>
                {/each}
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
      <p class="pw-verwaltung-satz">Gelesen gilt für dein Konto, auf allen Geräten.</p>
    </section>
  </div>
</div>
