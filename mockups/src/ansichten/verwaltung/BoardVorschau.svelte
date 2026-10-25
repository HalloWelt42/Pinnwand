<script lang="ts">
  // Vorschau beim Anlegen: so sieht das neue Board aus (Kopf, Spalten, erste Kartennummer, Module, Felder, Rollen,
  // Mitglieder), noch ohne Karten. Sie folgt jeder Wahl links sofort.
  import { RECHTE } from "../../beispiel/daten";
  import Person from "../../board/Person.svelte";
  import type { Farbe, ModulKennung } from "../../modell";
  import { MODULE, type Vorschlag } from "./daten";

  let { name, kuerzel, farbe, ordner, spalten, module, felder, mitglieder }: {
    name: string; kuerzel: string; farbe: Farbe; ordner: string; spalten: string[]; module: ModulKennung[]; felder: string[];
    mitglieder: Vorschlag[];
  } = $props();

  /** Spaltenfarben der Vorschau: im Umlauf, die letzte (Erledigt) in Minze; jede Farbe ist danach einstellbar */
  const UMLAUF: Farbe[] = ["stahl", "himmel", "honig", "flieder"];
  const spaltenFarbe = (i: number) => (i === spalten.length - 1 ? "minze" : UMLAUF[i % UMLAUF.length]);
  const mitRechten = $derived(RECHTE.filter((r) => r.modul === "kern" || module.includes(r.modul)).length);
</script>

<section class="bereich pw-verwaltung-vorschau" aria-label="Vorschau des neuen Boards">
  <h2 class="etikett">Vorschau</h2>
  <div class="titel"><span class="pw-farbpunkt" data-farbe={farbe}></span><b>{name.trim() || "Neues Board"}</b></div>
  <div class="pfad"><i class="fa-solid fa-folder"></i>{ordner}<span class="pw-schluessel">Kürzel {kuerzel || "fehlt"}</span></div>
  <div class="pw-verwaltung-minispalten" style="--anzahl: {spalten.length}">
    {#each spalten as s, i (i)}
      <div class="spalte" data-farbe={spaltenFarbe(i)}>
        <span class="name">{s}{#if i === spalten.length - 1}<i class="fa-solid fa-circle-check erledigt" title="Erledigt-Spalte"
          aria-label="Erledigt-Spalte"></i>{/if}</span>
      </div>
    {/each}
  </div>
  <div class="pfad"><i class="fa-regular fa-note-sticky"></i>Die erste Karte heißt <span class="pw-schluessel">{kuerzel || "?"}-1</span></div>
  <dl class="pw-verwaltung-bringt">
    <dt>Module</dt>
    <dd>{#each MODULE.filter((m) => module.includes(m.id)) as m (m.id)}<span class="chip pw-verwaltung-fest"><i class="fa-solid {m.symbol}"></i>{m.name}</span>
      {:else}keine, zuschaltbar in den Einstellungen{/each}</dd>
    <dt>Felder</dt><dd>{felder.length ? felder.join(", ") : "nur die Grundfelder"}</dd>
    <dt>Rollen</dt><dd>Besitzer, Mitglied, Leser; {mitRechten} Rechte</dd>
    <dt>Mitglieder</dt>
    <dd><span class="pw-personen">{#each mitglieder as p (p.kennung)}{#if p.konto}<Person id={p.konto} />{:else}<span class="pw-verwaltung-neuperson" title={p.name}><i class="fa-solid fa-user"></i></span>{/if}{/each}</span>
      {mitglieder.length} {mitglieder.length === 1 ? "Person" : "Personen"}</dd>
  </dl>
</section>
