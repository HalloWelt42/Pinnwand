<script lang="ts">
  // Persönliche Einstellungen (/einstellungen/<reiter>): Darstellung auf diesem Gerät, Hinweise je Art und Weg, das
  // Konto aus der Kellerwolke, deine Ordner, der Papierkorb der App, die Einstellungen der ganzen Pinnwand (App und
  // Verbindungen) und die Gestaltung aus dem Appkern. Einstellungen eines Boards stehen im Board; je Board ein Weg dorthin.
  import { Hilfepunkt } from "appkern-oberflaeche";
  import { boardGruppen, modulIrgendwo } from "../../daten/abfragen";
  import { stand } from "../../daten/stand.svelte";
  import { boardPfad } from "../../weg.svelte";
  import type { Component } from "svelte";
  import Gestaltung from "appkern-oberflaeche/gestaltung";
  import { PERSON_REITER } from "./daten";
  import App from "./person/App.svelte";
  import Darstellung from "./person/Darstellung.svelte";
  import Hinweise from "./person/Hinweise.svelte";
  import Konto from "./person/Konto.svelte";
  import Konten from "./person/Konten.svelte";
  import Ordner from "./person/Ordner.svelte";
  import Papierkorb from "./person/Papierkorb.svelte";

  let { reiter = "darstellung" }: { reiter?: string } = $props();

  const SEITEN: Record<string, Component<any>> = { darstellung: Darstellung, hinweise: Hinweise, konto: Konto, ordner: Ordner, papierkorb: Papierkorb, app: App, konten: Konten };
  const Seite = $derived(SEITEN[reiter]);
  /** Das Zeitkonto gibt es, sobald eines deiner Boards Arbeitszeit eingeschaltet hat */
  const arbeitszeit = $derived(modulIrgendwo("arbeitszeit"));
  const boards = $derived(boardGruppen().flatMap((g) => g.boards));
</script>

<div class="rahmen-kopf">
  <div class="seitenkopf">
    <h1>Einstellungen<Hilfepunkt thema="einstellungen" abschnitt={reiter} titel="Hilfe zu diesem Reiter" /></h1>
    <div class="unterzeile">Was nur dich betrifft; unter <a href="/einstellungen/app">App und Verbindungen</a> das, was für die ganze Pinnwand gilt{#if arbeitszeit};
      dein Zeitkonto steht unter <a href="/arbeitszeit">Arbeitszeit</a>{/if}.</div>
    {#if boards.length}
      <div class="pw-boardwege"><span>Einstellungen eines Boards (Module, Spalten, Mitglieder):</span>
        {#each boards as b (b.id)}
          <a class="knopf klein" href={boardPfad(b.kuerzel, "einstellungen")}><span class="pw-farbpunkt" data-farbe={b.farbe}></span>{b.name}</a>
        {/each}
      </div>
    {/if}
  </div>
  <nav class="reiter pw-verwaltung-reiter" aria-label="Persönliche Einstellungen">
    {#each PERSON_REITER.filter((r) => r.id !== "konten" || stand.appBesitzer) as r (r.id)}
      <a href="/einstellungen/{r.id}" class:aktiv={r.id === reiter} aria-current={r.id === reiter ? "page" : undefined}>
        <i class="fa-solid {r.symbol}"></i>{r.name}</a>
    {/each}
  </nav>
</div>
{#if Seite}
  <Seite />
{:else}
  <div class="rollfeld"><Gestaltung familie="leitstand" /></div>
{/if}
