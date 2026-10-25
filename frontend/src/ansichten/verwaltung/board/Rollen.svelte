<script lang="ts">
  // Rollen und Rechte: oben die Rollen (anlegen als Kopie einer anderen, umbenennen; die drei Start-Rollen bleiben),
  // darunter die Matrix Rollen mal Rechte, gruppiert nach dem Modul, das die Rechte mitbringt (nur Module, die diese
  // Fassung anbietet). Rechte abgeschalteter Module ruhen (ausgegraut, mit Hinweis). Ein Häkchen wirkt sofort für alle Mitglieder dieser Rolle. Besitzer behalten
  // "Board verwalten" und "Mitglieder verwalten", damit immer jemand das Board führen kann.
  import { untrack } from "svelte";
  import { MODUL_NAME } from "../../../anzeige";
  import {
    BESITZER_FEST, rechtSetzen, rolleAnlegen, rolleLoeschen, rolleUmbenennen, rolleVergeben,
  } from "../../../daten/anwendung/boards.svelte";
  import { RECHTE } from "../../../daten/konstanten";
  import Person from "../../../board/Person.svelte";
  import { stand } from "../../../daten/stand.svelte";
  import type { Board, ModulKennung, Recht, Rolle } from "../../../modell";
  import { modulAn as modulEingeschaltet } from "../../../regeln/board";
  import { boardPfad } from "../../../weg.svelte";

  let { board }: { board: Board } = $props();

  /** Rechte je Modul: der Kern und die Module, die diese Fassung anbietet */
  const gruppen = $derived.by(() => {
    const g: { modul: "kern" | ModulKennung; rechte: Recht[] }[] = [];
    for (const r of RECHTE.filter((x) => x.modul === "kern" || stand.moduleDa.includes(x.modul))) {
      const vorhanden = g.find((x) => x.modul === r.modul);
      if (vorhanden) vorhanden.rechte.push(r);
      else g.push({ modul: r.modul, rechte: [r] });
    }
    return g;
  });
  const modulAn = (m: "kern" | ModulKennung) => m === "kern" || modulEingeschaltet(board, m, stand.moduleDa);
  const fest = (rolle: Rolle, recht: string) => rolle.id === "besitzer" && BESITZER_FEST.includes(recht);
  const mitRolle = (id: string) => board.mitglieder.filter((m) => m.rolle === id);

  async function umbenennen(r: Rolle, e: Event): Promise<void> {
    const feld = e.currentTarget as HTMLInputElement;
    if (feld.value.trim() === r.name || !(await rolleUmbenennen(board.id, r.id, feld.value))) feld.value = r.name;
  }
  /** Häkchen setzen; abgelehnt steht wieder, was gilt */
  async function haken(r: Rolle, recht: string, e: Event): Promise<void> {
    const feld = e.currentTarget as HTMLInputElement;
    if (!(await rechtSetzen(board.id, r.id, recht, feld.checked))) feld.checked = r.rechte.includes(recht);
  }
  async function loeschenBestaetigen(r: Rolle): Promise<void> {
    if (await rolleLoeschen(board.id, r.id, ersatz)) loeschen = null;
  }

  let loeschen = $state<string | null>(null);
  let ersatz = $state("mitglied");
  $effect(() => { board.id; untrack(() => (loeschen = null)); });

  let neuName = $state("");
  let kopie = $state("mitglied");
  const neuDoppelt = $derived(neuName.trim() ? rolleVergeben(board, neuName) : undefined);
  async function anlegen(): Promise<void> {
    if (await rolleAnlegen(board.id, neuName, kopie)) neuName = "";
  }
</script>

<div class="rollfeld">
  <div class="pw-verwaltung-flaeche">
    <section class="bereich">
      <h2 class="etikett">Rollen</h2>
      <p class="pw-verwaltung-satz">Jede Person im Board hat genau eine Rolle. Besitzer, Mitglied und Leser hat jedes Board; sie lassen sich umbenennen,
        aber nicht löschen.</p>
      <div class="pw-verwaltung-liste">
        {#each board.rollen as r (r.id)}
          {@const leute = mitRolle(r.id)}
          <article class="pw-verwaltung-eintrag" class:gefahr={loeschen === r.id} aria-label="Rolle {r.name}">
            <div class="oben">
              <i class="fa-solid {r.id === 'besitzer' ? 'fa-crown' : r.vorgabe ? 'fa-user' : 'fa-user-gear'} pw-verwaltung-artsymbol"></i>
              <input class="eingabe pw-verwaltung-name" value={r.name} aria-label="Name der Rolle {r.name}" onchange={(e) => umbenennen(r, e)} />
              <span class="pw-personen" title="{leute.length} {leute.length === 1 ? 'Person hat' : 'Personen haben'} diese Rolle">
                {#each leute as m (m.kellerwolke)}{#if m.konto}<Person id={m.konto} />{:else}<span class="pw-personenwahl-neu" title="{m.kellerwolke}, wartet auf die erste Anmeldung"><i class="fa-solid fa-user"></i></span>{/if}{/each}
                <span class="mehr">{leute.length} {leute.length === 1 ? "Person" : "Personen"}</span></span>
              <span class="pw-angabe flaeche" title="Rechte dieser Rolle"><i class="fa-solid fa-key"></i>{r.rechte.length} {r.rechte.length === 1 ? "Recht" : "Rechte"}</span>
              {#if r.vorgabe}
                <span class="zustand" title="Start-Rolle jedes Boards: umbenennbar, nicht löschbar"><i class="fa-solid fa-lock"></i>Start-Rolle</span>
              {:else}
                <button class="knopf ohne symbol klein" title="Rolle {r.name} löschen" aria-label="Rolle {r.name} löschen" disabled={loeschen === r.id}
                        onclick={() => { loeschen = r.id; ersatz = "mitglied"; }}><i class="fa-solid fa-trash-can"></i></button>
              {/if}
            </div>
            {#if loeschen === r.id}
              <div class="hinweis gefahr pw-verwaltung-rueckfrage" role="alert"><i class="fa-solid fa-trash-can"></i>
                <div><b>Rolle {r.name} löschen?</b>
                  {#if leute.length}
                    {leute.length === 1 ? "Eine Person hat" : `${leute.length} Personen haben`} sie; sie bekommen dann die Rolle
                    <select class="eingabe" bind:value={ersatz} aria-label="Neue Rolle für die Personen">
                      {#each board.rollen.filter((x) => x.id !== r.id && x.id !== "besitzer") as x (x.id)}<option value={x.id}>{x.name}</option>{/each}
                    </select>
                  {:else}Niemand hat sie.{/if}</div>
                <span class="rechts"><button class="knopf klein" onclick={() => (loeschen = null)}>Abbrechen</button>
                  <button class="knopf gefahr-voll klein" onclick={() => loeschenBestaetigen(r)}><i class="fa-solid fa-trash-can"></i>Rolle löschen</button></span>
              </div>
            {/if}
          </article>
        {/each}
      </div>
      <div class="pw-verwaltung-formular">
        <input class="eingabe" bind:value={neuName} placeholder="Name der neuen Rolle" aria-label="Name der neuen Rolle"
               onkeydown={(e) => { if (e.key === "Enter") anlegen(); }} />
        <span class="pw-verwaltung-mit">mit den Rechten von</span>
        <select class="eingabe" bind:value={kopie} aria-label="Rechte übernehmen von">
          {#each board.rollen as r (r.id)}<option value={r.id}>{r.name}</option>{/each}
        </select>
        <button class="knopf" disabled={!neuName.trim() || !!neuDoppelt} onclick={anlegen}><i class="fa-solid fa-plus"></i>Rolle anlegen</button>
      </div>
      {#if neuDoppelt}<span class="pw-verwaltung-fehler" role="alert">Die Rolle {neuDoppelt} gibt es schon.</span>{/if}
    </section>

    <section class="bereich">
      <h2 class="etikett">Rechte</h2>
      <div class="hinweis"><i class="fa-solid fa-bolt"></i>
        <div>Ein Häkchen wirkt sofort für alle Mitglieder mit dieser Rolle, auch auf Seiten, die gerade offen sind. Der Server prüft jedes Recht
          auf jedem Weg, am Rechner wie am Telefon.</div></div>
      <div class="tabellen-raum pw-verwaltung-tabelle">
        <table class="tabelle karten pw-verwaltung-matrix">
          <thead><tr><th>Recht</th>{#each board.rollen as r (r.id)}<th class="haken">{r.name}</th>{/each}</tr></thead>
          <tbody>
            {#each gruppen as g (g.modul)}
              {@const an = modulAn(g.modul)}
              <tr class="gruppe"><td colspan={board.rollen.length + 1}>
                <span class="etikett">{MODUL_NAME[g.modul]}</span>
                {#if !an}
                  <span class="zustand aus"><i class="fa-solid fa-power-off"></i>Modul aus</span>
                  <span class="schwach">Diese Rechte ruhen und gelten wieder, sobald das Modul an ist.
                    <a href={boardPfad(board.kuerzel, "einstellungen/module")}>Module</a></span>
                {/if}
              </td></tr>
              {#each g.rechte as recht (recht.id)}
                <tr class:aus={!an}>
                  <td><b>{recht.name}</b><span class="pw-verwaltung-erklaerung">{recht.erklaerung}</span></td>
                  {#each board.rollen as r (r.id)}
                    <td class="haken" data-titel={r.name}>
                      <input type="checkbox" checked={r.rechte.includes(recht.id)} disabled={!an || fest(r, recht.id)}
                             aria-label="{r.name}: {recht.name}" onchange={(e) => haken(r, recht.id, e)}
                             title={fest(r, recht.id) ? "Besitzer behalten das immer, damit jemand das Board führen kann" : `${r.name}: ${recht.name}`} />
                      {#if fest(r, recht.id)}<i class="fa-solid fa-lock schwach" title="Fest für Besitzer"></i>{/if}
                    </td>
                  {/each}
                </tr>
              {/each}
            {/each}
          </tbody>
        </table>
      </div>
    </section>
  </div>
</div>
