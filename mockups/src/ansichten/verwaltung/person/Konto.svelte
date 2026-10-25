<script lang="ts">
  // Konto: angemeldet mit dem Kellerwolke-Konto (feste Kennung, an ihr hängen Zeiten, Kommentare und Rechte); Name
  // kommt aus der Kellerwolke, das Kürzel ist nur Anzeige auf Karten. Abmelden. Das Zeitkonto steht unter Arbeitszeit.
  import { ICH } from "../../../beispiel/daten";
  import { konto } from "../../../beispiel/stand.svelte";
  import Person from "../../../board/Person.svelte";
  import { KENNUNGEN } from "../daten";

  const ich = konto(ICH);
  let kuerzel = $state(ich.kuerzel);
  let fehler = $state("");

  function kuerzelSetzen(e: Event): void {
    const feld = e.currentTarget as HTMLInputElement;
    const k = feld.value.trim().toUpperCase();
    if (!/^[A-ZÄÖÜ]{1,3}$/.test(k)) {
      fehler = "Ein bis drei Buchstaben.";
      feld.value = kuerzel;
      return;
    }
    fehler = "";
    kuerzel = k;
    feld.value = k;
  }
</script>

<div class="rollfeld">
  <div class="pw-verwaltung-flaeche">
    <section class="bereich pw-verwaltung-konto">
      <Person id={ICH} gross />
      <div class="wer"><b>{ich.name}</b>
        <span class="klein leise">Angemeldet mit dem Kellerwolke-Konto <span class="pw-schluessel">{KENNUNGEN[ICH]}</span></span></div>
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
        <div class="wert pw-verwaltung-wert-spalte">
          <input class="eingabe" value={kuerzel} maxlength="3" aria-label="Dein Kürzel" onchange={kuerzelSetzen} />
          {#if fehler}<span class="pw-verwaltung-fehler" role="alert">{fehler}</span>{/if}
        </div>
      </div>
      <div class="einstellung">
        <div><div class="name">Kennung</div><div class="erklaerung">Fest; an ihr erkennt dich jedes Board.</div></div>
        <div class="wert"><span class="pw-schluessel">{KENNUNGEN[ICH]}</span></div>
      </div>
    </section>

    <p class="pw-verwaltung-satz"><i class="fa-solid fa-calendar-check"></i>Wochenstunden, Urlaub und Bundesland gehören zu deinem Zeitkonto unter
      <a href="/arbeitszeit">Arbeitszeit</a>.</p>
  </div>
</div>
