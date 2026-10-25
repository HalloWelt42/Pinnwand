<script lang="ts">
  // Hinweise: je Art (zugewiesen, fällig, erwähnt, Termin, Kommentar, verschoben) und je Weg (in der Pinnwand, Push aufs
  // Telefon, über den Assistenten) ein Schalter. Push braucht das Telefon: das Einrichten steht als Schritte darüber.
  // Gilt am Konto, auf allen Geräten; jeder Schalter über den Anwendungsfall.
  import { HINWEIS_ARTEN, HINWEIS_WEGE } from "../../../anzeige";
  import { hinweisWegSetzen } from "../../../daten/anwendung/hinweise.svelte";
  import { stand } from "../../../daten/stand.svelte";
</script>

<div class="rollfeld">
  <div class="pw-verwaltung-flaeche">
    <section class="bereich">
      <h2 class="etikett">Push aufs Telefon einrichten</h2>
      <div class="kette" aria-label="Schritte">
        <span class="schritt erledigt"><i class="fa-solid fa-circle-check"></i>Pinnwand als Web-App aufs Telefon</span>
        <span class="pfeil erledigt"></span>
        <span class="schritt jetzt"><i class="fa-solid fa-bell"></i>Dort Mitteilungen erlauben</span>
        <span class="pfeil"></span>
        <span class="schritt offen"><i class="fa-solid fa-paper-plane"></i>Testmitteilung</span>
      </div>
      <div class="pw-verwaltung-formular">
        <p class="pw-verwaltung-satz">Öffne die Pinnwand auf dem Telefon vom Home-Bildschirm, dann Einstellungen, Hinweise, "Mitteilungen erlauben".
          Danach steht das Telefon hier, und eine Testmitteilung zeigt, dass es ankommt.</p>
        <button class="knopf" disabled title="Erst, wenn ein Telefon Mitteilungen erlaubt"><i class="fa-solid fa-paper-plane"></i>Testmitteilung senden</button>
      </div>
      <div class="pw-verwaltung-geraete"><i class="fa-solid fa-mobile-screen"></i>Noch kein Telefon eingerichtet; bis dahin kommen Hinweise in der
        Pinnwand und über den Assistenten.</div>
    </section>

    <section class="bereich">
      <h2 class="etikett">Welche Hinweise wohin</h2>
      <div class="tabellen-raum pw-verwaltung-tabelle">
        <table class="tabelle karten pw-verwaltung-hinweise">
          <thead><tr><th>Art</th>{#each HINWEIS_WEGE as w (w.id)}<th class="haken" title={w.text}><i class="fa-solid {w.symbol}"></i> {w.name}</th>{/each}</tr></thead>
          <tbody>
            {#each HINWEIS_ARTEN as a (a.art)}
              <tr>
                <td><span class="pw-verwaltung-art"><i class="fa-solid {a.symbol}"></i><span><b>{a.name}</b><span class="pw-verwaltung-erklaerung">{a.text}</span></span></span></td>
                {#each HINWEIS_WEGE as w (w.id)}
                  {@const an = stand.einstellungen.hinweise[a.art][w.id]}
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
      <p class="pw-verwaltung-satz">Gelesen gilt für dein Konto, auf allen Geräten. Push gilt erst, wenn ein Telefon eingerichtet ist.</p>
    </section>
  </div>
</div>
