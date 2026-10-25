<script lang="ts">
  // Hinweise am Telefon: kurz, neueste zuerst, neue mit Wort und Rahmen markiert; ein Tippen springt zur Karte (Termine
  // ohne Karte nach Heute) und gilt als gelesen, am Konto und damit auf allen Geräten. Dieselben Hinweise kommen als
  // Push aufs Telefon.
  import { HINWEIS_ARTEN } from "../../anzeige";
  import { kartenNummer, ungelesen } from "../../daten/abfragen";
  import { alleGelesen, gelesen } from "../../daten/anwendung/hinweise.svelte";
  import { wann } from "../../daten/format";
  import { board, karte, stand } from "../../daten/stand.svelte";
  import type { Hinweis } from "../../modell";
  import { boardPfad } from "../../weg.svelte";
  import TelefonSchale from "./TelefonSchale.svelte";
  import { telPfad } from "./weg";

  const liste = $derived([...stand.hinweise].sort((a, b) => b.zeit.localeCompare(a.zeit)));
  const neu = $derived(ungelesen());
  const art = (h: Hinweis) => HINWEIS_ARTEN.find((a) => a.art === h.art);
  function ziel(h: Hinweis): string {
    const k = h.karte ? karte(h.karte) : undefined;
    return k ? telPfad(boardPfad(board(k.board).kuerzel, kartenNummer(k)), { von: "hinweise" }) : telPfad("/heute");
  }
</script>

<TelefonSchale titel="Hinweise" unter={neu ? `${neu} neu` : "Alles gelesen"} zurueck={telPfad("/heute")} glocke={false}>
  {#if neu}
    <button class="knopf ohne pw-tel-alle" onclick={alleGelesen}><i class="fa-solid fa-check-double"></i>Alle gelesen</button>
  {/if}
  <div class="pw-tel-liste">
    {#each liste as h (h.id)}
      <a class="pw-tel-hinweis" class:neu={!h.gelesen} href={ziel(h)} onclick={() => gelesen(h.id)}>
        <span class="zeichen"><i class="fa-solid {art(h)?.symbol ?? 'fa-bell'}"></i></span>
        <span class="text">
          <span class="kopfzeile"><b>{art(h)?.name ?? "Hinweis"}</b><span class="zeit">{wann(h.zeit)}</span>{#if !h.gelesen}<span class="zaehler pille info">neu</span>{/if}</span>
          <span class="was">{h.text}</span>
        </span>
        <i class="fa-solid fa-chevron-right"></i>
      </a>
    {/each}
  </div>
</TelefonSchale>
