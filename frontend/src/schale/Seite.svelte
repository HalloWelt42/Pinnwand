<script lang="ts">
  // Seitenleiste: die Bereiche über alle Boards (Heute, Hinweise, Zeiten, Arbeitszeit, Serien, Berichte), darunter die
  // Boards in deinen Ordnern (Ordner ordnen nur, sie tragen keine Rechte), unten Einstellungen.
  import { ungelesen } from "../daten/abfragen";
  import { board, stand } from "../daten/stand.svelte";
  import { boardPfad } from "../weg.svelte";

  let { aktiv }: { aktiv: string } = $props();
  const NAVI = [
    ["heute", "Heute", "fa-sun", "Deine Karten, Termine und Serien aus allen Boards"],
    ["hinweise", "Hinweise", "fa-bell", "Zugewiesen, fällig, erwähnt, Termine"],
    ["zeiten", "Zeiten", "fa-clock", "Dein Stundenzettel der Woche"],
    ["arbeitszeit", "Arbeitszeit", "fa-calendar-check", "Zeitkonto, Urlaub und Jahreskalender"],
    ["serien", "Serien und Termine", "fa-repeat", "Wiederkehrende Karten und Termine aller Boards"],
    ["berichte", "Berichte", "fa-file-lines", "Auswertungen als PDF, Tabelle oder Text"],
  ] as const;
  const zahl = $derived(ungelesen());
</script>

{#each NAVI as [id, name, symbol, titel] (id)}
  <a class="navi" class:aktiv={aktiv === id} href="/{id}" title={titel}><i class="fa-solid {symbol}"></i>{name}
    {#if id === "hinweise" && zahl}<span class="zaehler pille gefahr">{zahl}</span>{/if}</a>
{/each}
<div class="etikett">Boards</div>
{#each stand.ordner as o (o.id)}
  <div class="pw-ordner"><i class="fa-solid fa-folder"></i>{o.name}</div>
  {#each o.boards as b (b)}
    <a class="navi pw-boardnavi" class:aktiv={aktiv === b} href={boardPfad(board(b).kuerzel)} title="Board {board(b).name}">
      <span class="pw-farbpunkt" data-farbe={board(b).farbe}></span><span class="pw-boardkuerzel" data-farbe={board(b).farbe}>{board(b).kuerzel}</span>{board(b).name}</a>
  {/each}
{/each}
<a class="navi" class:aktiv={aktiv === "board-neu"} href="/boards/neu"><i class="fa-solid fa-plus"></i>Board anlegen</a>
<div class="pw-seite-fuss">
  <a class="navi" class:aktiv={aktiv === "einstellungen"} href="/einstellungen"><i class="fa-solid fa-gear"></i>Einstellungen</a>
</div>
