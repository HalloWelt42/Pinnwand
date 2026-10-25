<script lang="ts">
  // Vorschau beim Anlegen: so sieht das neue Board aus (Kopf, Spalten in ihren Farben, erste Kartennummer, Module, Felder,
  // Labels, Rollen, Mitglieder), noch ohne Karten. Sie folgt jeder Wahl links sofort.
  import { MODULE } from "../../anzeige";
  import { RECHTE } from "../../daten/konstanten";
  import Person from "../../board/Person.svelte";
  import type { Farbe, KellerwolkePerson, Vorlage } from "../../modell";

  let { name, kuerzel, farbe, ordner, vorlage, mitglieder }: {
    name: string; kuerzel: string; farbe: Farbe; ordner: string; vorlage: Vorlage; mitglieder: KellerwolkePerson[];
  } = $props();

  const mitRechten = $derived(RECHTE.filter((r) => r.modul === "kern" || vorlage.module.includes(r.modul)).length);
</script>

<section class="bereich pw-verwaltung-vorschau" aria-label="Vorschau des neuen Boards">
  <h2 class="etikett">Vorschau</h2>
  <div class="titel"><span class="pw-farbpunkt" data-farbe={farbe}></span><b>{name.trim() || "Neues Board"}</b></div>
  <div class="pfad"><i class="fa-solid fa-folder"></i>{ordner}<span class="pw-schluessel">Kürzel {kuerzel || "fehlt"}</span></div>
  <div class="pw-verwaltung-minispalten" style="--anzahl: {vorlage.spalten.length}">
    {#each vorlage.spalten as s, i (i)}
      <div class="spalte" data-farbe={s.farbe}>
        <span class="name">{s.name}{#if s.erledigt}<i class="fa-solid fa-circle-check erledigt" title="Erledigt-Spalte" aria-label="Erledigt-Spalte"></i>{/if}</span>
        {#if s.grenze}<span class="grenze" title="Grenze offener Karten">bis {s.grenze}</span>{/if}
      </div>
    {/each}
  </div>
  <div class="pfad"><i class="fa-regular fa-note-sticky"></i>Die erste Karte heißt <span class="pw-schluessel">{kuerzel || "?"}-1</span></div>
  <dl class="pw-verwaltung-bringt">
    <dt>Module</dt>
    <dd>{#each MODULE.filter((m) => vorlage.module.includes(m.id)) as m (m.id)}<span class="chip pw-verwaltung-fest"><i class="fa-solid {m.symbol}"></i>{m.name}</span>
      {:else}keine, zuschaltbar in den Einstellungen{/each}</dd>
    <dt>Felder</dt><dd>{vorlage.felder.length ? vorlage.felder.map((f) => f.name).join(", ") : "nur die Grundfelder"}</dd>
    <dt>Labels</dt>
    <dd>{#each vorlage.labels as l (l.name)}<span class="pw-label" data-farbe={l.farbe}>{l.name}</span>{:else}keine{/each}</dd>
    <dt>Rollen</dt><dd>Besitzer, Mitglied, Leser; {mitRechten} Rechte</dd>
    <dt>Mitglieder</dt>
    <dd><span class="pw-personen">{#each mitglieder as p (p.kennung)}{#if p.konto}<Person id={p.konto} />{:else}<span class="pw-personenwahl-neu" title={p.name}><i class="fa-solid fa-user"></i></span>{/if}{/each}</span>
      {mitglieder.length} {mitglieder.length === 1 ? "Person" : "Personen"}</dd>
  </dl>
</section>
