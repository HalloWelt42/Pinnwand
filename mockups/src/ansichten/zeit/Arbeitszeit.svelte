<script lang="ts">
  // Arbeitszeit: dein Zeitkonto mit seinen Reitern als eigene Adressen (/arbeitszeit, /kalender, /urlaub, /team). Das
  // Zeitkonto hängt an deiner Person, nicht an einem Board; gebuchte Zeit aus allen Boards fließt hinein. Team zeigt die
  // Mitglieder eines Boards, nur mit dem Recht "Abwesenheiten sehen" in diesem Board.
  import type { Component } from "svelte";
  import Jahreskalender from "./Jahreskalender.svelte";
  import Team from "./Team.svelte";
  import Urlaub from "./Urlaub.svelte";
  import Zeitkonto from "./Zeitkonto.svelte";

  let { reiter = "", entwurf = "" }: { reiter?: string; entwurf?: string } = $props();

  const REITER: [string, string, string, string, Component<any>][] = [
    ["", "Zeitkonto", "fa-scale-balanced", "Soll und Ist, Überstunden, Resturlaub, Einstellungen", Zeitkonto],
    ["kalender", "Kalender", "fa-calendar-days", "Jahreskalender mit Feiertagen und Abwesenheiten; Tage anklicken oder ziehen", Jahreskalender],
    ["urlaub", "Urlaub", "fa-umbrella-beach", "Urlaub und Abwesenheit eintragen, Wirkung auf das Soll, Brückentage", Urlaub],
    ["team", "Team", "fa-users", "Anwesenheit und Auslastung der Mitglieder eines Boards", Team],
  ];
  const aktiv = $derived(REITER.find((r) => r[0] === reiter) ?? REITER[0]);
  const Ansicht = $derived(aktiv[4]);
</script>

<div class="rahmen-kopf pw-arbeitszeit-rahmen">
  <div class="seitenkopf pw-arbeitszeit-kopf">
    <h1>Arbeitszeit</h1>
    <nav class="reiter" aria-label="Bereiche der Arbeitszeit">
      {#each REITER as [id, name, symbol, titel] (id)}
        <a class="knopf ohne" class:aktiv={aktiv[0] === id} href="/arbeitszeit{id ? '/' + id : ''}" title={titel}><i class="fa-solid {symbol}"></i>{name}</a>
      {/each}
    </nav>
  </div>
</div>
<div class="pw-zeiten-raum">
  <Ansicht {entwurf} />
</div>
