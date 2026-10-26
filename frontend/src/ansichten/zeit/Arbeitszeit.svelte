<script lang="ts">
  // Arbeitszeit: dein Zeitkonto mit seinen Reitern als eigene Adressen (/arbeitszeit, /kalender, /urlaub, /team). Das
  // Zeitkonto hängt an deiner Person, nicht an einem Board; gebuchte Zeit aus allen Boards fließt hinein. Team zeigt die
  // Mitglieder eines Boards, nur mit dem Recht "Abwesenheiten sehen" in diesem Board. Kalender und Urlaub rechnen mit
  // Bundesland und Arbeitstagen des Zeitkontos; ohne Zeitkonto führen sie erst zu seiner Einstellung.
  import { Hilfepunkt } from "appkern-oberflaeche";
  import type { Component } from "svelte";
  import { ICH } from "../../daten/ich";
  import { stand } from "../../daten/stand.svelte";
  import Jahreskalender from "./Jahreskalender.svelte";
  import Team from "./Team.svelte";
  import Urlaub from "./Urlaub.svelte";
  import Zeitkonto from "./Zeitkonto.svelte";

  let { reiter = "" }: { reiter?: string } = $props();

  const REITER: [string, string, string, string, Component<any>][] = [
    ["", "Zeitkonto", "fa-scale-balanced", "Soll und Ist, Überstunden, Resturlaub, Einstellungen", Zeitkonto],
    ["kalender", "Kalender", "fa-calendar-days", "Jahreskalender mit Feiertagen und Abwesenheiten; Tage anklicken oder ziehen", Jahreskalender],
    ["urlaub", "Urlaub", "fa-umbrella-beach", "Urlaub und Abwesenheit eintragen, Wirkung auf das Soll, Brückentage", Urlaub],
    ["team", "Team", "fa-users", "Anwesenheit und Auslastung der Mitglieder eines Boards", Team],
  ];
  const aktiv = $derived(REITER.find((r) => r[0] === reiter) ?? REITER[0]);
  const Ansicht = $derived(aktiv[4]);
  /** Kalender und Urlaub brauchen ein Zeitkonto (Bundesland, Arbeitstage) */
  const ohneZeitkonto = $derived((reiter === "kalender" || reiter === "urlaub") && !stand.zeitkonten.some((z) => z.konto === ICH));
</script>

<div class="rahmen-kopf pw-arbeitszeit-rahmen">
  <div class="seitenkopf pw-arbeitszeit-kopf">
    <h1>Arbeitszeit<Hilfepunkt thema="arbeitszeit" abschnitt="aufruf" /></h1>
    <nav class="reiter" aria-label="Bereiche der Arbeitszeit">
      {#each REITER as [id, name, symbol, titel] (id)}
        <a class="knopf ohne" class:aktiv={aktiv[0] === id} href="/arbeitszeit{id ? '/' + id : ''}" title={titel}><i class="fa-solid {symbol}"></i>{name}</a>
      {/each}
    </nav>
  </div>
</div>
<div class="pw-zeiten-raum">
  {#if ohneZeitkonto}
    <div class="rollfeld">
      <div class="hinweis"><i class="fa-solid fa-scale-balanced"></i>
        <div><b>Noch kein Zeitkonto.</b> Wochenstunden, Arbeitstage und Bundesland bestimmen Soll, Feiertage und Urlaub; stelle sie
          zuerst im Zeitkonto ein.</div>
        <span class="rechts"><a class="knopf klein" href="/arbeitszeit">Zum Zeitkonto</a></span>
      </div>
    </div>
  {:else}
    <Ansicht />
  {/if}
</div>
