<script lang="ts">
  // Einstellungen eines Boards (/board/<kürzel>/einstellungen/<reiter>): fester Kopf wie im Board, darunter die Reiter
  // mit eigener Adresse und je Reiter ein eigenes Rollfeld. Jede Änderung läuft über einen Anwendungsfall, gilt sofort
  // für alle Mitglieder und kommt mit Rückgängig; einen Speichern-Knopf gibt es nicht.
  import type { Component } from "svelte";
  import { ICH } from "../../beispiel/daten";
  import { board, ordnerVon } from "../../beispiel/stand.svelte";
  import { boardPfad } from "../../weg.svelte";
  import Allgemein from "./board/Allgemein.svelte";
  import Felder from "./board/Felder.svelte";
  import Labels from "./board/Labels.svelte";
  import Mitglieder from "./board/Mitglieder.svelte";
  import Module from "./board/Module.svelte";
  import Rollen from "./board/Rollen.svelte";
  import Spalten from "./board/Spalten.svelte";
  import { BOARD_REITER } from "./daten";

  let { boardId, reiter = "allgemein", entwurf = "" }: { boardId: string; reiter?: string; entwurf?: string } = $props();

  const SEITEN: Record<string, Component<any>> = {
    allgemein: Allgemein, spalten: Spalten, labels: Labels, felder: Felder, rollen: Rollen, mitglieder: Mitglieder, module: Module,
  };
  const b = $derived(board(boardId));
  const Seite = $derived(SEITEN[reiter] ?? Allgemein);
  const ordner = $derived(ordnerVon(b.id)?.name ?? "Ohne Ordner");
  const eigeneRolle = $derived(b.rollen.find((r) => r.id === b.mitglieder.find((m) => m.konto === ICH)?.rolle)?.name ?? "");
</script>

<div class="rahmen-kopf">
  <div class="seitenkopf pw-boardkopf">
    <h1><span class="pw-farbpunkt" data-farbe={b.farbe}></span>{b.name}</h1>
    <div class="rechts">
      <a class="knopf klein" href={boardPfad(b.kuerzel)}><i class="fa-solid fa-table-columns"></i>Zum Board</a>
    </div>
    <div class="pfad"><i class="fa-solid fa-sliders"></i>Einstellungen des Boards<span class="pw-schluessel">Kürzel {b.kuerzel}</span>
      <span>· <i class="fa-solid fa-folder"></i> {ordner} · gelten für {b.mitglieder.length === 1 ? "dich allein" : `alle ${b.mitglieder.length} Mitglieder`} · du bist {eigeneRolle}</span></div>
  </div>
  <nav class="reiter pw-verwaltung-reiter" aria-label="Einstellungen des Boards">
    {#each BOARD_REITER as r (r.id)}
      <a href={boardPfad(b.kuerzel, `einstellungen/${r.id}`)} class:aktiv={r.id === reiter} aria-current={r.id === reiter ? "page" : undefined}>
        <i class="fa-solid {r.symbol}"></i>{r.name}</a>
    {/each}
  </nav>
</div>
<Seite board={b} {entwurf} />
