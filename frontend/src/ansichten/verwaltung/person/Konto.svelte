<script lang="ts">
  // Konto: angemeldet mit dem Kellerwolke-Konto (feste Kennung, an ihr hängen Zeiten, Kommentare und Rechte); der Name
  // kommt aus der Kellerwolke, das Kürzel ist nur Anzeige auf Karten. Abmelden über den Appkern; das eigene Konto
  // zurücksetzen oder löschen, bestätigt mit dem Namen (ohne Rückweg).
  import { modulIrgendwo } from "../../../daten/abfragen";
  import { abmelden } from "appkern-oberflaeche";
  import { eigenesKuerzelSetzen } from "../../../daten/anwendung/boards.svelte";
  import { ICH } from "../../../daten/ich";
  import { konto } from "../../../daten/stand.svelte";
  import Person from "../../../board/Person.svelte";
  import { kontoLoeschen, kontoZuruecksetzen } from "../../../daten/anwendung/konten.svelte";
  import Endgueltig from "../../../teile/Endgueltig.svelte";
  import { Hilfepunkt } from "appkern-oberflaeche";

  const ich = $derived(konto(ICH));
  /** Das Zeitkonto gibt es, sobald eines deiner Boards Arbeitszeit eingeschaltet hat */
  const arbeitszeit = $derived(modulIrgendwo("arbeitszeit"));

  let offen = $state<"zuruecksetzen" | "loeschen" | null>(null);
  async function ausfuehren(bestaetigung: string): Promise<boolean> {
    const ok = offen === "loeschen" ? await kontoLoeschen(ICH, bestaetigung) : await kontoZuruecksetzen(ICH, bestaetigung);
    if (ok) offen = null;
    return ok;
  }

  async function kuerzelSetzen(e: Event): Promise<void> {
    const feld = e.currentTarget as HTMLInputElement;
    await eigenesKuerzelSetzen(feld.value);
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
      <button class="knopf" onclick={abmelden}><i class="fa-solid fa-right-from-bracket"></i>Abmelden</button>
    </section>

    <section class="bereich">
      <h2 class="etikett">Wie du erscheinst</h2>
      <div class="einstellung">
        <div><div class="name">Name</div><div class="erklaerung">Kommt aus der Kellerwolke; dort änderst du ihn für alle eigenen Apps.</div></div>
        <div class="wert"><span>{ich.name}</span></div>
      </div>
      <div class="einstellung">
        <div><div class="name">Kürzel</div>
          <div class="erklaerung">Ein bis drei Buchstaben im Kreis auf Karten, in Listen und im Board; gilt sofort für alle. Nur Anzeige:
            Zeiten, Kommentare und Rechte hängen an deinem Konto, nicht am Kürzel.</div></div>
        <div class="wert"><input class="eingabe" value={ich.kuerzel} maxlength="3" aria-label="Dein Kürzel" onchange={kuerzelSetzen} /></div>
      </div>
      <div class="einstellung">
        <div><div class="name">Kennung</div><div class="erklaerung">Fest; an ihr erkennt dich jedes Board.</div></div>
        <div class="wert"><span class="pw-schluessel">{ich.kellerwolke}</span></div>
      </div>
    </section>

    <section class="bereich">
      <h2 class="etikett">Neu anfangen<Hilfepunkt thema="einstellungen" abschnitt="konto" /></h2>
      <div class="einstellung">
        <div><div class="name">Konto zurücksetzen</div>
          <div class="erklaerung">Alles, was dir in der Pinnwand gehört, geht; danach ist es wie bei der ersten Anmeldung.</div></div>
        <div class="wert"><button class="knopf" disabled={offen !== null} onclick={() => (offen = "zuruecksetzen")}><i class="fa-solid fa-rotate-left"></i>Zurücksetzen</button></div>
      </div>
      <div class="einstellung">
        <div><div class="name">Konto löschen</div>
          <div class="erklaerung">Wie Zurücksetzen, und dein Konto verschwindet aus der Pinnwand; du wirst abgemeldet. Meldest du dich wieder an,
            bist du neu.</div></div>
        <div class="wert"><button class="knopf gefahr" disabled={offen !== null} onclick={() => (offen = "loeschen")}><i class="fa-solid fa-user-xmark"></i>Löschen</button></div>
      </div>
      {#if offen}
        <Endgueltig frage={offen === "loeschen" ? "Dein Konto löschen?" : "Dein Konto zurücksetzen?"} wort={ich.name}
                    knopf={offen === "loeschen" ? "Konto löschen" : "Konto zurücksetzen"} bestaetigen={ausfuehren} abbrechen={() => (offen = null)}>
          Boards, in denen du allein bist, gehen mit allen Karten, Serien und Terminen. Aus geteilten Boards wirst du ausgetragen; bist du dort
          einziger Besitzer, übernimmt das nächste Mitglied. Deine Zeiten, Timer, dein Zeitkonto, Urlaub, Hinweise, Ordner, Vorlagen und
          Berichte gehen ganz. Das lässt sich nicht rückgängig machen.
        </Endgueltig>
      {/if}
    </section>

    {#if arbeitszeit}
      <p class="pw-verwaltung-satz"><i class="fa-solid fa-calendar-check"></i>Wochenstunden, Urlaub und Bundesland gehören zu deinem Zeitkonto unter
        <a href="/arbeitszeit">Arbeitszeit</a>.</p>
    {/if}
  </div>
</div>
