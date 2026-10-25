<script lang="ts">
  // Rollen und Rechte: oben die Rollen (anlegen als Kopie einer anderen, umbenennen; die drei Start-Rollen bleiben),
  // darunter die Matrix Rollen mal Rechte, gruppiert nach dem Modul, das die Rechte mitbringt. Rechte abgeschalteter
  // Module ruhen (ausgegraut, mit Hinweis). Ein Häkchen wirkt sofort für alle Mitglieder dieser Rolle. Besitzer behalten
  // "Board verwalten" und "Mitglieder verwalten", damit immer jemand das Board führen kann.
  import { untrack } from "svelte";
  import { RECHTE } from "../../../beispiel/daten";
  import Person from "../../../board/Person.svelte";
  import type { Board, ModulKennung, Recht, Rolle } from "../../../modell";
  import { boardPfad } from "../../../weg.svelte";
  import { MODUL_NAME } from "../daten";

  let { board }: { board: Board; entwurf?: string } = $props();

  const BESITZER_FEST = ["board.verwalten", "mitglieder.verwalten"];
  const gruppen = (() => {
    const g: { modul: "kern" | ModulKennung; rechte: Recht[] }[] = [];
    for (const r of RECHTE) {
      const vorhanden = g.find((x) => x.modul === r.modul);
      if (vorhanden) vorhanden.rechte.push(r);
      else g.push({ modul: r.modul, rechte: [r] });
    }
    return g;
  })();
  const modulAn = (m: "kern" | ModulKennung) => m === "kern" || board.module[m];
  const fest = (rolle: Rolle, recht: string) => rolle.id === "besitzer" && BESITZER_FEST.includes(recht);
  const mitRolle = (id: string) => board.mitglieder.filter((m) => m.rolle === id);

  function umschalten(rolle: Rolle, recht: string): void {
    rolle.rechte = rolle.rechte.includes(recht) ? rolle.rechte.filter((x) => x !== recht) : [...rolle.rechte, recht];
  }

  const vergeben = (name: string, ausser = "") =>
    board.rollen.find((r) => r.id !== ausser && r.name.toLowerCase() === name.trim().toLowerCase());
  let fehler = $state<Record<string, string>>({});
  function umbenennen(r: Rolle, e: Event): void {
    const feld = e.currentTarget as HTMLInputElement;
    const neu = feld.value.trim();
    const doppelt = vergeben(neu, r.id);
    if (!neu || doppelt) {
      fehler[r.id] = neu ? `Die Rolle ${doppelt!.name} gibt es schon.` : "Eine Rolle braucht einen Namen.";
      feld.value = r.name;
      return;
    }
    fehler[r.id] = "";
    r.name = neu;
  }

  let loeschen = $state<string | null>(null);
  let ersatz = $state("mitglied");
  $effect(() => { board.id; untrack(() => (loeschen = null)); });
  function rolleLoeschen(r: Rolle): void {
    for (const m of board.mitglieder) if (m.rolle === r.id) m.rolle = ersatz;
    board.rollen = board.rollen.filter((x) => x.id !== r.id);
    loeschen = null;
  }

  let neuName = $state("");
  let kopie = $state("mitglied");
  const neuDoppelt = $derived(neuName.trim() ? vergeben(neuName) : undefined);
  function anlegen(): void {
    const name = neuName.trim();
    if (!name || neuDoppelt) return;
    const vorlage = board.rollen.find((r) => r.id === kopie);
    board.rollen.push({ id: `r-${crypto.randomUUID()}`, name, rechte: [...(vorlage?.rechte ?? [])] });
    neuName = "";
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
                {#each leute as m (m.konto)}<Person id={m.konto} />{/each}
                <span class="mehr">{leute.length} {leute.length === 1 ? "Person" : "Personen"}</span></span>
              <span class="pw-angabe flaeche" title="Rechte dieser Rolle"><i class="fa-solid fa-key"></i>{r.rechte.length} {r.rechte.length === 1 ? "Recht" : "Rechte"}</span>
              {#if r.vorgabe}
                <span class="zustand" title="Start-Rolle jedes Boards: umbenennbar, nicht löschbar"><i class="fa-solid fa-lock"></i>Start-Rolle</span>
              {:else}
                <button class="knopf ohne symbol klein" title="Rolle {r.name} löschen" aria-label="Rolle {r.name} löschen" disabled={loeschen === r.id}
                        onclick={() => { loeschen = r.id; ersatz = "mitglied"; }}><i class="fa-solid fa-trash-can"></i></button>
              {/if}
            </div>
            {#if fehler[r.id]}<span class="pw-verwaltung-fehler" role="alert">{fehler[r.id]}</span>{/if}
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
                  <button class="knopf gefahr-voll klein" onclick={() => rolleLoeschen(r)}><i class="fa-solid fa-trash-can"></i>Rolle löschen</button></span>
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
      {#if neuDoppelt}<span class="pw-verwaltung-fehler" role="alert">Die Rolle {neuDoppelt.name} gibt es schon.</span>{/if}
    </section>

    <section class="bereich">
      <h2 class="etikett">Rechte</h2>
      <div class="hinweis"><i class="fa-solid fa-bolt"></i>
        <div>Ein Häkchen wirkt sofort für alle Mitglieder mit dieser Rolle, auch auf Seiten, die gerade offen sind. Der Server prüft jedes Recht
          auf jedem Weg: Oberfläche, Telefon, Assistent und Serien.</div></div>
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
                             aria-label="{r.name}: {recht.name}" onchange={() => umschalten(r, recht.id)}
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
