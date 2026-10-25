<script lang="ts">
  // Einstellungen eines Boards (/board/<kürzel>/einstellungen/<reiter>): fester Kopf wie im Board, darunter die Reiter
  // mit eigener Adresse und je Reiter ein eigenes Rollfeld. Jede Änderung gilt sofort für alle Mitglieder (Ereignisstrom);
  // es gibt keinen Speichern-Knopf, jedes Feld meldet sich erst nach der Antwort des Servers als gespeichert.
  import type { Component } from "svelte";
  import { ICH, ORDNER } from "../../beispiel/daten";
  import { board } from "../../beispiel/stand.svelte";
  import { boardPfad } from "../../weg.svelte";
  import Allgemein from "./board/Allgemein.svelte";
  import Felder from "./board/Felder.svelte";
  import Labels from "./board/Labels.svelte";
  import Mitglieder from "./board/Mitglieder.svelte";
  import Module from "./board/Module.svelte";
  import Rollen from "./board/Rollen.svelte";
  import Spalten from "./board/Spalten.svelte";
  import { BOARD_REITER } from "./daten";
  import Reiter from "./Reiter.svelte";

  let { boardId, reiter = "allgemein", entwurf = "" }: { boardId: string; reiter?: string; entwurf?: string } = $props();

  const SEITEN: Record<string, Component<any>> = {
    allgemein: Allgemein, spalten: Spalten, labels: Labels, felder: Felder, rollen: Rollen, mitglieder: Mitglieder, module: Module,
  };
  const b = $derived(board(boardId));
  const Seite = $derived(SEITEN[reiter] ?? Allgemein);
  const ordner = $derived(ORDNER.find((o) => o.id === b.ordner)?.name ?? "Ohne Ordner");
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
  <Reiter reiter={BOARD_REITER} aktiv={reiter} name="Einstellungen des Boards" pfad={(id) => boardPfad(b.kuerzel, `einstellungen/${id}`)} />
</div>
<Seite board={b} {entwurf} />
