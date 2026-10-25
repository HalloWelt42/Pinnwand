<script lang="ts">
  // Konto: angemeldet mit dem Kellerwolke-Konto (feste Kennung, an ihr hängen Zeiten, Kommentare und Rechte); Name
  // kommt aus der Kellerwolke, das Kürzel ist nur Anzeige auf Karten. Abmelden. Das Zeitkonto steht unter Arbeitszeit.
  import { eigenesKuerzelSetzen } from "../../../daten/anwendung/boards.svelte";
  import { ICH } from "../../../daten/ich";
  import { konto } from "../../../daten/stand.svelte";
  import Person from "../../../board/Person.svelte";

  const ich = $derived(konto(ICH));

  function kuerzelSetzen(e: Event): void {
    const feld = e.currentTarget as HTMLInputElement;
    eigenesKuerzelSetzen(feld.value);
    feld.value = ich.kuerzel;
  }
</script>

<div class="rollfeld">
  <div class="pw-verwaltung-flaeche">
    <section class="bereich pw-verwaltung-konto">
      <Person id={ICH} gross />
      <div class="wer"><b>{ich.name}</b>
        <span class="klein leise">Angemeldet mit dem Kellerwolke-Konto <span class="pw-schluessel">{ich.kellerwolke}</span></span></div>
      <span class="zustand fertig"><i class="fa-solid fa-circle-check"></i>angemeldet</span>
      <button class="knopf"><i class="fa-solid fa-right-from-bracket"></i>Abmelden</button>
    </section>

    <section class="bereich">
      <h2 class="etikett">Wie du erscheinst</h2>
      <div class="einstellung">
        <div><div class="name">Name</div><div class="erklaerung">Kommt aus der Kellerwolke; dort änderst du ihn für alle eigenen Apps.</div></div>
        <div class="wert"><span>{ich.name}</span></div>
      </div>
      <div class="einstellung">
        <div><div class="name">Kürzel</div>
          <div class="erklaerung">Steht im Kreis auf Karten, in Listen und im Board. Nur Anzeige: Zeiten, Kommentare und Rechte hängen an deinem
            Konto, nicht am Kürzel.</div></div>
        <div class="wert"><input class="eingabe" value={ich.kuerzel} maxlength="3" aria-label="Dein Kürzel" onchange={kuerzelSetzen} /></div>
      </div>
      <div class="einstellung">
        <div><div class="name">Kennung</div><div class="erklaerung">Fest; an ihr erkennt dich jedes Board.</div></div>
        <div class="wert"><span class="pw-schluessel">{ich.kellerwolke}</span></div>
      </div>
    </section>

    <p class="pw-verwaltung-satz"><i class="fa-solid fa-calendar-check"></i>Wochenstunden, Urlaub und Bundesland gehören zu deinem Zeitkonto unter
      <a href="/arbeitszeit">Arbeitszeit</a>.</p>
  </div>
</div>
