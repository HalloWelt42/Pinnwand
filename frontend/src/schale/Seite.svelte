<script lang="ts">
  // Seitenleiste: die Bereiche über alle Boards (Heute, Hinweise; Zeiten, Arbeitszeit, Serien und Berichte nur, wenn eines
  // deiner Boards das Modul eingeschaltet hat), darunter deine Boards nach deinen Ordnern (Ordner ordnen nur, sie tragen
  // keine Rechte), Boards ohne Ordner zuletzt unter "Ohne Ordner", unten Einstellungen.
  import { boardGruppen, modulIrgendwo, ungelesen } from "../daten/abfragen";
  import type { ModulKennung } from "../modell";
  import { boardPfad } from "../weg.svelte";

  let { aktiv }: { aktiv: string } = $props();
  const NAVI: [string, string, string, string, ModulKennung | null][] = [
    ["heute", "Heute", "fa-sun", "Deine Karten aus allen Boards", null],
    ["hinweise", "Hinweise", "fa-bell", "Zugewiesen, fällig, erwähnt, kommentiert, verschoben", null],
    ["zeiten", "Zeiten", "fa-clock", "Dein Stundenzettel der Woche", "zeiterfassung"],
    ["arbeitszeit", "Arbeitszeit", "fa-calendar-check", "Zeitkonto, Urlaub und Jahreskalender", "arbeitszeit"],
    ["serien", "Serien und Termine", "fa-repeat", "Wiederkehrende Karten und Termine aller Boards", "serien"],
    ["berichte", "Berichte", "fa-file-lines", "Auswertungen als PDF, Tabelle oder Text", "berichte"],
  ];
  /** Hat eines deiner Boards das Modul an (und bietet diese Fassung es an)? */
  const bereiche = $derived(NAVI.filter(([, , , , modul]) => modul === null || modulIrgendwo(modul)));
  const gruppen = $derived(boardGruppen());
  const zahl = $derived(ungelesen());
</script>

{#each bereiche as [id, name, symbol, titel] (id)}
  <a class="navi" class:aktiv={aktiv === id} href="/{id}" title={titel}><i class="fa-solid {symbol}"></i>{name}
    {#if id === "hinweise" && zahl}<span class="zaehler pille gefahr">{zahl}</span>{/if}</a>
{/each}
<div class="etikett">Boards</div>
{#each gruppen as g (g.ordner?.id ?? "")}
  <div class="pw-ordner"><i class="fa-{g.ordner ? 'solid' : 'regular'} fa-folder"></i>{g.ordner?.name ?? "Ohne Ordner"}</div>
  {#each g.boards as b (b.id)}
    <a class="navi pw-boardnavi" class:aktiv={aktiv === b.id} href={boardPfad(b.kuerzel)} title="Board {b.name}">
      <span class="pw-farbpunkt" data-farbe={b.farbe}></span><span class="pw-boardkuerzel" data-farbe={b.farbe}>{b.kuerzel}</span>{b.name}</a>
  {/each}
{/each}
<a class="navi" class:aktiv={aktiv === "board-neu"} href="/boards/neu"><i class="fa-solid fa-plus"></i>Board anlegen</a>
<div class="pw-seite-fuss">
  <a class="navi" class:aktiv={aktiv === "einstellungen"} href="/einstellungen"><i class="fa-solid fa-gear"></i>Einstellungen</a>
</div>
