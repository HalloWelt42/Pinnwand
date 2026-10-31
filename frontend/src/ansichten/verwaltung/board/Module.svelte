<script lang="ts">
  // Module des Boards: je Modul, das diese Fassung anbietet, ein Schalter mit dem, was es bringt (Ansichten, Felder,
  // Rechte); den Reiter gibt es nur, wenn sie welche anbietet. Abschalten blendet ein Modul in Board, Karten und Rollen
  // aus; seine Daten bleiben und sind beim Einschalten wieder da. Schalten über den Anwendungsfall.
  import { MODULE } from "../../../anzeige";
  import { modulSchalten } from "../../../daten/anwendung/boards.svelte";
  import { RECHTE } from "../../../daten/konstanten";
  import { stand } from "../../../daten/stand.svelte";
  import type { Board, ModulKennung } from "../../../modell";
  import { boardPfad } from "../../../weg.svelte";

  let { board }: { board: Board } = $props();

  const GRUPPEN = [["fach", "Fachmodule"], ["anbindung", "Anbindungen an andere Apps"]] as const;
  const angeboten = (art: string) => MODULE.filter((m) => m.art === art && stand.moduleDa.includes(m.id));
  const rechte = (id: string) => RECHTE.filter((r) => r.modul === id);

  /** Was einer Anbindung fehlt, damit sie wirkt (die Verbindung trägt man in den Einstellungen der App ein) */
  function fehlt(id: ModulKennung): string {
    if (id === "ki" && !stand.kiBereit) return "Die Leitstelle ist in den Einstellungen der App noch nicht eingerichtet; bis dahin erscheinen keine Vorschläge.";
    if (id === "transkripte" && !stand.transkriptionAdresse) return "Die Adresse der Transkription fehlt in den Einstellungen der App; bis dahin gibt es keine Transkripte.";
    if (id === "vorlesen" && !stand.vorlesenAdresse) return "Die Adresse der Vertonung fehlt in den Einstellungen der App; bis dahin wird nichts vorgelesen.";
    return "";
  }
</script>

<div class="rollfeld">
  <div class="pw-verwaltung-flaeche">
    <div class="hinweis"><i class="fa-solid fa-circle-info"></i>
      <div>Abschalten blendet ein Modul in Board, Karten und <a href={boardPfad(board.kuerzel, "einstellungen/rollen")}>Rollen</a> aus. Seine Daten
        bleiben (Zeiten, Serien, Marken) und sind beim Einschalten wieder da.</div></div>

    {#each GRUPPEN.filter(([art]) => angeboten(art).length) as [art, titel] (art)}
      <h2 class="etikett">{titel}</h2>
      <div class="pw-verwaltung-module">
        {#each angeboten(art) as m (m.id)}
          {@const an = board.module[m.id]}
          <div>
            <article class="karte pw-verwaltung-modul" class:aus={!an} aria-label="Modul {m.name}">
              <h3><i class="fa-solid {m.symbol}"></i>{m.name}
                <span class="rechts">
                  <span class="zustand {an ? 'fertig' : 'aus'}">{an ? "an" : "aus"}</span>
                  <button class="schalter" class:an aria-pressed={an} aria-label="Modul {m.name} {an ? 'abschalten' : 'einschalten'}"
                          onclick={() => modulSchalten(board.id, m.id, !an)}></button>
                </span></h3>
              <p>{m.text}</p>
              <dl class="pw-verwaltung-bringt">
                <dt>Ansichten</dt><dd>{m.ansichten.join(", ")}</dd>
                <dt>Felder</dt><dd>{m.felder.length ? m.felder.join(", ") : "keine"}</dd>
                <dt>Rechte</dt>
                <dd>{#each rechte(m.id) as r (r.id)}<span class="chip pw-verwaltung-fest" title={r.erklaerung}><i class="fa-solid fa-key"></i>{r.name}</span>
                  {:else}keine eigenen{/each}</dd>
              </dl>
              {#if !an}<p class="pw-verwaltung-satz"><i class="fa-solid fa-eye-slash"></i>Ausgeblendet; die Daten bleiben.</p>{/if}
              {#if fehlt(m.id)}
                <p class="pw-verwaltung-satz"><i class="fa-solid fa-plug-circle-xmark"></i>{fehlt(m.id)}</p>
              {/if}
            </article>
          </div>
        {/each}
      </div>
    {/each}
  </div>
</div>
