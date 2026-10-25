<script lang="ts">
  // Einstellungen eines Boards (/board/<kürzel>/einstellungen/<reiter>): fester Kopf wie im Board, darunter die Reiter
  // mit eigener Adresse und je Reiter ein eigenes Rollfeld. Jede Änderung läuft über einen Anwendungsfall, gilt sofort
  // für alle Mitglieder und kommt mit Rückgängig; einen Speichern-Knopf gibt es nicht. Wer das Recht des Reiters nicht
  // hat (Rollen und Mitglieder: "Mitglieder verwalten", sonst "Board verwalten"), sieht ihn nur; der Server prüft dasselbe.
  import type { Component } from "svelte";
  import { darf } from "../../daten/abfragen";
  import { RECHTE } from "../../daten/konstanten";
  import { ICH } from "../../daten/ich";
  import { board, ordnerVon, stand } from "../../daten/stand.svelte";
  import { boardPfad } from "../../weg.svelte";
  import Allgemein from "./board/Allgemein.svelte";
  import Felder from "./board/Felder.svelte";
  import Labels from "./board/Labels.svelte";
  import Mitglieder from "./board/Mitglieder.svelte";
  import Module from "./board/Module.svelte";
  import Rollen from "./board/Rollen.svelte";
  import Spalten from "./board/Spalten.svelte";
  import { boardReiter } from "./daten";

  let { boardId, reiter = "allgemein" }: { boardId: string; reiter?: string } = $props();

  const SEITEN: Record<string, Component<any>> = {
    allgemein: Allgemein, spalten: Spalten, labels: Labels, felder: Felder, rollen: Rollen, mitglieder: Mitglieder, module: Module,
  };
  const b = $derived(board(boardId));
  const Seite = $derived(SEITEN[reiter] ?? Allgemein);
  const reiterDa = $derived(boardReiter(stand.moduleDa));
  const ordner = $derived(ordnerVon(b.id)?.name ?? "Ohne Ordner");
  const eigeneRolle = $derived(b.rollen.find((r) => r.id === b.mitglieder.find((m) => m.konto === ICH)?.rolle)?.name ?? "");
  const recht = $derived(reiter === "rollen" || reiter === "mitglieder" ? "mitglieder.verwalten" : "board.verwalten");
  const gesperrt = $derived(!darf(b, recht));
</script>

<div class="rahmen-kopf">
  <div class="seitenkopf pw-boardkopf">
    <h1><span class="pw-farbpunkt" data-farbe={b.farbe}></span>{b.name}</h1>
    <div class="rechts">
      <a class="knopf klein" href={boardPfad(b.kuerzel)}><i class="fa-solid fa-table-columns"></i>Zum Board</a>
    </div>
    <div class="pfad"><i class="fa-solid fa-sliders"></i>Einstellungen des Boards<span class="pw-schluessel">Kürzel {b.kuerzel}</span>
      <span>· <i class="fa-solid fa-folder"></i> {ordner} · gelten für {b.mitglieder.length === 1 ? "dich allein" : `alle ${b.mitglieder.length} Mitglieder`} · du bist {eigeneRolle}</span>
      {#if gesperrt}<span class="zustand"><i class="fa-solid fa-eye"></i>nur ansehen: dir fehlt das Recht {RECHTE.find((r) => r.id === recht)?.name}</span>{/if}</div>
  </div>
  <nav class="reiter pw-verwaltung-reiter" aria-label="Einstellungen des Boards">
    {#each reiterDa as r (r.id)}
      <a href={boardPfad(b.kuerzel, `einstellungen/${r.id}`)} class:aktiv={r.id === reiter} aria-current={r.id === reiter ? "page" : undefined}>
        <i class="fa-solid {r.symbol}"></i>{r.name}</a>
    {/each}
  </nav>
</div>
<fieldset class="pw-verwaltung-gesperrt" disabled={gesperrt} aria-label="Einstellungen: {reiterDa.find((r) => r.id === reiter)?.name ?? ''}">
  <Seite board={b} />
</fieldset>
