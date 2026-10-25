<script lang="ts">
  // Einstieg der Entwürfe: alle Zustände nach Stufe, je ein Verweis; Rechner und Telefon getrennt.
  import { adresse, STUFEN, ZUSTAENDE } from "../zustaende";
</script>

<div class="pw-galerie">
  <div class="pw-galerie-innen">
    <div class="seitenkopf" style="margin: 0">
      <h1 style="display: flex; gap: var(--a3); align-items: center"><span class="pw-marke-symbol"><i class="fa-solid fa-thumbtack"></i></span>Pinnwand: Entwürfe zur Freigabe</h1>
      <div class="unterzeile">Gebaut im echten Stack (Svelte, Bausteine und Marken des Appkerns) mit Beispieldaten; nach der Freigabe werden diese
        Ansichten die Oberfläche der App. Jeder Entwurf hat seinen echten Pfad wie später in der App; ?entwurf= wählt einen vorgeführten Zustand. Unten in der Mitte schaltet eine Leiste hell und dunkel, die Schriftstufe (Vorgabe Klein) und blättert.
        Ziehen, Abhaken und Umschalten gehen echt. Personen und Firmen sind erfunden.</div>
    </div>
    {#each Object.entries(STUFEN) as [stufe, name] (stufe)}
      {@const liste = ZUSTAENDE.filter((z) => z.stufe === Number(stufe))}
      {#if liste.length}
        <div class="etikett">{name}</div>
        <div class="pw-galerie-gruppe">
          {#each liste as z, i (adresse(z))}
            <a class="karte klickbar" href={adresse(z)}>
              <span class="kopf-zeile"><i class="fa-solid {z.symbol}"></i><b>{i + 1}. {z.titel}</b>
                {#if z.geraet === "telefon"}<span class="zaehler info" style="margin-left: auto">Telefon</span>{/if}</span>
              <p>{z.text}</p><span class="pw-schluessel">{adresse(z)}</span>
            </a>
          {/each}
        </div>
      {/if}
    {/each}
  </div>
</div>
