<script lang="ts">
  // Hinweise am Telefon: kurz, neueste zuerst, neue mit Wort und Rahmen markiert; ein Tippen springt zur Karte (ohne
  // geladene Karte zu ihrem Board, ein Termin nach Heute, wo die Termine stehen) und gilt als gelesen, am Konto und damit
  // auf allen Geräten. Ein Hinweis aus einem Board, das du nicht mehr siehst, hat kein Ziel; "Alle gelesen" erfasst auch ihn.
  import { HINWEIS_ARTEN } from "../../anzeige";
  import { kartenNummer, ungelesen } from "../../daten/abfragen";
  import { alleGelesen, gelesen } from "../../daten/anwendung/hinweise.svelte";
  import { wann } from "../../daten/format";
  import { karte, stand } from "../../daten/stand.svelte";
  import type { Hinweis } from "../../modell";
  import { boardPfad } from "../../weg.svelte";
  import TelefonSchale from "./TelefonSchale.svelte";
  import { telPfad } from "./weg";

  const liste = $derived([...stand.hinweise].sort((a, b) => b.zeit.localeCompare(a.zeit)));
  const neu = $derived(ungelesen());
  const art = (h: Hinweis) => HINWEIS_ARTEN.find((a) => a.art === h.art);

  /** Ziel eines Hinweises; keines, wenn du sein Board nicht mehr siehst */
  function ziel(h: Hinweis): string | undefined {
    const b = stand.boards.find((x) => x.id === h.board);
    if (!b) return undefined;
    const k = h.karte ? karte(h.karte) : undefined;
    if (k) return telPfad(boardPfad(b.kuerzel, kartenNummer(k)), { von: "hinweise" });
    return h.art === "termin" ? telPfad("/heute") : telPfad(boardPfad(b.kuerzel));
  }
</script>

{#snippet inhalt(h: Hinweis)}
  <span class="zeichen"><i class="fa-solid {art(h)?.symbol ?? 'fa-bell'}"></i></span>
  <span class="text">
    <span class="kopfzeile"><b>{art(h)?.name ?? "Hinweis"}</b><span class="zeit">{wann(h.zeit)}</span>{#if !h.gelesen}<span class="zaehler pille info">neu</span>{/if}</span>
    <span class="was">{h.text}</span>
  </span>
{/snippet}

<TelefonSchale titel="Hinweise" unter={neu ? `${neu} neu` : "Alles gelesen"} zurueck={telPfad("/heute")} glocke={false}>
  {#if neu}
    <button class="knopf ohne pw-tel-alle" onclick={alleGelesen}><i class="fa-solid fa-check-double"></i>Alle gelesen</button>
  {/if}
  <div class="pw-tel-liste">
    {#each liste as h (h.id)}
      {@const z = ziel(h)}
      {#if z}
        <a class="pw-tel-hinweis" class:neu={!h.gelesen} href={z} onclick={() => gelesen(h.id)}>
          {@render inhalt(h)}
          <i class="fa-solid fa-chevron-right"></i>
        </a>
      {:else}
        <div class="pw-tel-hinweis" class:neu={!h.gelesen}>{@render inhalt(h)}</div>
      {/if}
    {/each}
  </div>
</TelefonSchale>
