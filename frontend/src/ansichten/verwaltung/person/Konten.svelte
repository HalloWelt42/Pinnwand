<script lang="ts">
  // Konten (nur für den Besitzer der App): jedes Konto der Pinnwand mit Kürzel und Kellerwolke-Namen; zurücksetzen (wie
  // bei der ersten Anmeldung) oder löschen (es verschwindet, meldet es sich wieder an, ist es neu), beides ohne Rückweg
  // und bestätigt mit dem Namen. Der Server prüft, dass du Besitzer der App bist.
  import { Hilfepunkt } from "appkern-oberflaeche";
  import Person from "../../../board/Person.svelte";
  import { kontoLoeschen, kontoZuruecksetzen } from "../../../daten/anwendung/konten.svelte";
  import { ICH } from "../../../daten/ich";
  import { stand } from "../../../daten/stand.svelte";
  import type { Konto } from "../../../modell";
  import Endgueltig from "../../../teile/Endgueltig.svelte";

  const konten = $derived([...stand.konten].sort((a, b) => a.name.localeCompare(b.name, "de")));
  let offen = $state<{ id: string; art: "zuruecksetzen" | "loeschen" } | null>(null);
  /** Boards, die du mit dem Konto teilst (andere siehst du nicht) */
  const gemeinsam = (k: Konto) => stand.boards.filter((b) => b.mitglieder.some((m) => m.konto === k.id)).length;

  async function ausfuehren(k: Konto, bestaetigung: string): Promise<boolean> {
    const ok = offen?.art === "loeschen" ? await kontoLoeschen(k.id, bestaetigung) : await kontoZuruecksetzen(k.id, bestaetigung);
    if (ok) offen = null;
    return ok;
  }
</script>

<div class="rollfeld">
  <div class="pw-verwaltung-flaeche">
    <p class="pw-verwaltung-satz"><i class="fa-solid fa-circle-info"></i>Du besitzt die App: hier setzt du jedes Konto zurück oder löschst es. Was dem
      Konto allein gehört, geht dabei ganz, auch seine gebuchten Zeiten; geteilte Boards bleiben.<Hilfepunkt thema="einstellungen" abschnitt="konten" /></p>
    <section class="bereich">
      <h2 class="etikett">Konten der Pinnwand <span class="zaehler">{konten.length}</span></h2>
      {#each konten as k (k.id)}
        <article class="pw-verwaltung-eintrag" class:gefahr={offen?.id === k.id} aria-label="Konto {k.name}">
          <div class="oben">
            <Person id={k.id} />
            <div class="wer pw-konten-wer"><b>{k.name}{#if k.id === ICH}<span class="zaehler akzent">du</span>{/if}</b>
              <span class="klein leise">Kellerwolke <span class="pw-schluessel">{k.kellerwolke}</span> · {gemeinsam(k) === 1 ? "1 gemeinsames Board" : `${gemeinsam(k)} gemeinsame Boards`}</span></div>
            <button class="knopf klein" disabled={offen?.id === k.id} onclick={() => (offen = { id: k.id, art: "zuruecksetzen" })}>
              <i class="fa-solid fa-rotate-left"></i>Zurücksetzen</button>
            <button class="knopf klein gefahr" disabled={offen?.id === k.id} onclick={() => (offen = { id: k.id, art: "loeschen" })}>
              <i class="fa-solid fa-user-xmark"></i>Löschen</button>
          </div>
          {#if offen?.id === k.id}
            <Endgueltig frage={offen.art === "loeschen" ? `Konto ${k.name} löschen?` : `Konto ${k.name} zurücksetzen?`} wort={k.name}
                        knopf={offen.art === "loeschen" ? "Konto löschen" : "Konto zurücksetzen"} bestaetigen={(e) => ausfuehren(k, e)}
                        abbrechen={() => (offen = null)}>
              Boards, in denen {k.id === ICH ? "du" : k.name} allein {k.id === ICH ? "bist" : "ist"}, gehen mit allen Karten, Serien und Terminen.
              Aus geteilten Boards wird das Konto ausgetragen; war es dort einziger Besitzer, übernimmt das nächste Mitglied.
              Zeiten, Timer, Zeitkonto, Urlaub, Hinweise, Ordner, Vorlagen und Berichte gehen ganz.
              {offen.art === "loeschen" ? "Danach ist das Konto aus der Pinnwand verschwunden und abgemeldet; meldet es sich wieder an, ist es neu."
                : "Danach ist es wie bei der ersten Anmeldung."} Das lässt sich nicht rückgängig machen.
            </Endgueltig>
          {/if}
        </article>
      {/each}
    </section>
  </div>
</div>
