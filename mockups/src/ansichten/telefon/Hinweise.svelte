<script lang="ts">
  // Hinweise am Telefon: kurz, neueste zuerst, neue mit Wort und Punkt markiert; ein Tippen springt zur Karte (Termine
  // ohne Karte nach Heute) und gilt als gelesen. Dieselben Hinweise kommen als Push aufs Telefon.
  import { HINWEISE } from "../../beispiel/daten";
  import { wann } from "../../beispiel/format";
  import { board, karte } from "../../beispiel/stand.svelte";
  import type { Hinweis, HinweisArt } from "../../modell";
  import { boardPfad } from "../../weg.svelte";
  import { gelesen, telefon } from "./aktionen.svelte";
  import TelefonSchale from "./TelefonSchale.svelte";
  import { telPfad } from "./weg";

  const ART: Record<HinweisArt, [string, string]> = {
    zugewiesen: ["Zugewiesen", "fa-user-plus"],
    faellig: ["Fällig", "fa-calendar-day"],
    erwaehnt: ["Erwähnt", "fa-at"],
    termin: ["Termin", "fa-calendar-check"],
    kommentar: ["Kommentar", "fa-comment"],
    verschoben: ["Verschoben", "fa-arrow-right-arrow-left"],
  };
  const liste = $derived([...HINWEISE].sort((a, b) => b.zeit.localeCompare(a.zeit)));
  const neu = (h: Hinweis): boolean => !h.gelesen && !telefon.gelesen.includes(h.id);
  const ungelesen = $derived(liste.filter(neu));
  function ziel(h: Hinweis): string {
    const k = h.karte ? karte(h.karte) : undefined;
    return k ? telPfad(boardPfad(board(k.board).kuerzel, k.schluessel.split("-")[1]), { von: "hinweise" }) : telPfad("/heute");
  }
</script>

<TelefonSchale titel="Hinweise" unter={ungelesen.length ? `${ungelesen.length} neu` : "Alles gelesen"} zurueck={telPfad("/heute")} glocke={false}>
  {#if ungelesen.length}
    <button class="knopf ohne pw-tel-alle" onclick={() => gelesen(...ungelesen.map((h) => h.id))}><i class="fa-solid fa-check-double"></i>Alle gelesen</button>
  {/if}
  <div class="pw-tel-liste">
    {#each liste as h (h.id)}
      <a class="pw-tel-hinweis" class:neu={neu(h)} href={ziel(h)} onclick={() => gelesen(h.id)}>
        <span class="zeichen"><i class="fa-solid {ART[h.art][1]}"></i></span>
        <span class="text">
          <span class="kopfzeile"><b>{ART[h.art][0]}</b><span class="zeit">{wann(h.zeit)}</span>{#if neu(h)}<span class="zaehler pille info">neu</span>{/if}</span>
          <span class="was">{h.text}</span>
        </span>
        <i class="fa-solid fa-chevron-right"></i>
      </a>
    {/each}
  </div>
</TelefonSchale>
