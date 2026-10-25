<script lang="ts">
  // Mitglieder: einladen per Kontoname der Kellerwolke (Textfeld; bekannte Konten erscheinen als Vorschläge, jeder andere
  // Kontoname geht auch), je Person die Rolle aus den Rollen des Boards und seit wann; wer noch nie angemeldet war, steht
  // mit seinem Kontonamen da und wartet auf die erste Anmeldung. Entfernen mit Rückfrage, die sagt, was an Karten
  // geschieht (eine wartende Einladung wird zurückgenommen); Besitz übertragen. Ein Board hat immer mindestens einen
  // Besitzer. Alles über die Anwendungsfälle.
  import { untrack } from "svelte";
  import { kellerwolkePersonen, laufendAuf } from "../../../daten/abfragen";
  import {
    besitzUebertragen, einladen, kontonameOk, mitgliedEntfernen, personAusText, rolleSetzen,
  } from "../../../daten/anwendung/boards.svelte";
  import { ICH } from "../../../daten/ich";
  import { datum } from "../../../daten/format";
  import { konto, stand } from "../../../daten/stand.svelte";
  import Person from "../../../board/Person.svelte";
  import type { Board, KellerwolkePerson, Mitglied } from "../../../modell";
  import { modulAn } from "../../../regeln/board";
  import Personenwahl from "../../../teile/Personenwahl.svelte";

  let { board }: { board: Board } = $props();

  const mitJahr = (iso: string) => datum(iso) + iso.slice(0, 4);
  /** Name eines Mitglieds: aus seinem Konto, sonst (wartet noch) sein Kontoname der Kellerwolke */
  const name = (m: Mitglied) => (m.konto ? konto(m.konto).name : m.kellerwolke);
  const besitzer = $derived(board.mitglieder.filter((m) => m.rolle === "besitzer"));
  const einziger = (m: Mitglied) => m.rolle === "besitzer" && besitzer.length === 1;
  /** an wen der Besitz gehen kann: wer schon angemeldet war, außer dir */
  const nachfolger = $derived(board.mitglieder.filter((m) => m.konto && m.konto !== ICH));
  const zeiten = $derived(modulAn(board, "zeiterfassung", stand.moduleDa));
  const offeneKarten = (k: string) => stand.karten.filter((x) => x.board === board.id && x.zustaendig.includes(k)
    && !board.spalten.find((s) => s.id === x.spalte)?.erledigt);
  const timer = (k: string) => stand.karten.filter((x) => x.board === board.id && laufendAuf(x.id).some((t) => t.konto === k));

  // einladen: gewählt aus den Vorschlägen oder der Kontoname, wie er im Feld steht
  let suche = $state("");
  let gewaehlt = $state<KellerwolkePerson | null>(null);
  let rolle = $state("mitglied");
  $effect(() => { board.id; untrack(() => { suche = ""; gewaehlt = null; entfernen = null; uebertragen = false; }); });
  const getippt = $derived(suche.trim());
  const einzuladen = $derived(gewaehlt ?? (getippt ? personAusText(getippt, kellerwolkePersonen()) : null));
  const nameFalsch = $derived(!gewaehlt && !!getippt && !kontonameOk(getippt));

  async function einladenBestaetigen(): Promise<void> {
    if (!einzuladen || nameFalsch) return;
    if (await einladen(board.id, einzuladen, rolle)) { gewaehlt = null; suche = ""; }
  }

  // entfernen und Besitz übertragen: Rückfragen in der Fläche
  let entfernen = $state<string | null>(null);
  let uebertragen = $state(false);
  let an = $state("");
  let ichWerde = $state("mitglied");
  function uebertragenStarten(): void {
    uebertragen = true;
    an = nachfolger[0]?.kellerwolke ?? "";
    ichWerde = "mitglied";
  }
  async function rolleWaehlen(m: Mitglied, e: Event): Promise<void> {
    const feld = e.currentTarget as HTMLSelectElement;
    if (!(await rolleSetzen(board.id, m.kellerwolke, feld.value))) feld.value = m.rolle;
  }
  async function entfernenBestaetigen(m: Mitglied): Promise<void> {
    if (await mitgliedEntfernen(board.id, m.kellerwolke)) entfernen = null;
  }
  async function uebertragenBestaetigen(): Promise<void> {
    if (await besitzUebertragen(board.id, an, ichWerde)) uebertragen = false;
  }
  const anName = $derived(name(board.mitglieder.find((m) => m.kellerwolke === an) ?? { konto: "", kellerwolke: an, rolle: "", seit: "" }));
</script>

<div class="rollfeld">
  <div class="pw-verwaltung-flaeche">
    <section class="bereich">
      <h2 class="etikett">Einladen</h2>
      <div class="pw-verwaltung-formular">
        {#if gewaehlt}
          <span class="chip pw-verwaltung-gewaehlt">{#if gewaehlt.konto}<Person id={gewaehlt.konto} />{:else}<span class="pw-personenwahl-neu"><i class="fa-solid fa-user"></i></span>{/if}
            {gewaehlt.name}<button class="knopf ohne symbol klein" title="Andere Person wählen" aria-label="Andere Person wählen"
                                   onclick={() => (gewaehlt = null)}><i class="fa-solid fa-xmark"></i></button></span>
        {:else}
          <Personenwahl bind:text={suche} kandidaten={kellerwolkePersonen()} ausser={board.mitglieder.map((m) => m.konto).filter(Boolean)}
                        platzhalter="Kontoname in der Kellerwolke" waehlen={(p) => (gewaehlt = p)} />
        {/if}
        <span class="pw-verwaltung-mit">als</span>
        <select class="eingabe" bind:value={rolle} aria-label="Rolle der eingeladenen Person">
          {#each board.rollen as r (r.id)}<option value={r.id}>{r.name}</option>{/each}
        </select>
        <button class="knopf haupt" title={nameFalsch ? "Das ist kein Kontoname der Kellerwolke; wähle die Person aus den Vorschlägen" : undefined}
                disabled={!einzuladen || nameFalsch} onclick={einladenBestaetigen}><i class="fa-solid fa-paper-plane"></i>Einladen</button>
      </div>
      {#if nameFalsch && !/\s/.test(getippt)}
        <span class="pw-verwaltung-fehler" role="alert">"{getippt}" ist kein Kontoname der Kellerwolke: nur Buchstaben, Ziffern, Punkt, Bindestrich,
          Unterstrich und @, ohne Leerzeichen.</span>
      {:else if einzuladen && !einzuladen.konto && !nameFalsch}
        <p class="pw-verwaltung-satz"><i class="fa-solid fa-user-clock"></i>{einzuladen.kennung} war noch nie in der Pinnwand: die Person steht
          ab sofort im Board und sieht es, sobald sie sich mit diesem Kellerwolke-Konto das erste Mal anmeldet.</p>
      {/if}
      <p class="pw-verwaltung-satz">Eingeladen wird mit dem Kontonamen der Kellerwolke; bekannte Personen erscheinen beim Tippen als Vorschlag.
        Wer schon angemeldet war, sieht das Board sofort in der Seitenleiste.</p>
    </section>

    <section class="bereich">
      <h2 class="etikett">Mitglieder</h2>
      <div class="tabellen-raum pw-verwaltung-tabelle">
        <table class="tabelle karten">
          <thead><tr><th>Person</th><th>Rolle</th><th>Seit</th><th></th></tr></thead>
          <tbody>
            {#each board.mitglieder as m (m.kellerwolke)}
              <tr>
                <td><span class="pw-verwaltung-person">
                  {#if m.konto}<Person id={m.konto} gross />{:else}<span class="pw-personenwahl-neu"><i class="fa-solid fa-user"></i></span>{/if}
                  <span class="wer"><b>{name(m)}{m.konto === ICH ? " (du)" : ""}</b><span class="pw-schluessel">{m.kellerwolke}</span>
                    {#if !m.konto}<span class="zustand wartet" title="Eingeladen; das Konto entsteht bei der ersten Anmeldung">
                      <i class="fa-solid fa-user-clock"></i>wartet auf die erste Anmeldung</span>{/if}</span></span></td>
                <td data-titel="Rolle">
                  <select class="eingabe" value={m.rolle} disabled={einziger(m)} aria-label="Rolle von {name(m)}"
                          title={einziger(m) ? "Einziger Besitzer: erst den Besitz übertragen" : `Rolle von ${name(m)}`}
                          onchange={(e) => rolleWaehlen(m, e)}>
                    {#each board.rollen as r (r.id)}<option value={r.id}>{r.name}</option>{/each}
                  </select></td>
                <td data-titel="Seit" class="pw-verwaltung-datum">{mitJahr(m.seit)}</td>
                <td data-titel="Aktion" class="pw-verwaltung-aktion">
                  {#if einziger(m)}
                    <button class="knopf klein" disabled={uebertragen || !nachfolger.length || m.konto !== ICH} onclick={uebertragenStarten}
                            title={m.konto !== ICH ? "Den Besitz überträgt nur der Besitzer selbst"
                              : !nachfolger.length ? "Erst muss sich ein weiteres Mitglied einmal angemeldet haben" : "Den Besitz an ein anderes Mitglied geben"}>
                      <i class="fa-solid fa-crown"></i>Besitz übertragen</button>
                  {:else}
                    <button class="knopf ohne klein gefahr" disabled={entfernen === m.kellerwolke} onclick={() => (entfernen = m.kellerwolke)}>
                      <i class="fa-solid fa-user-xmark"></i>{m.konto ? "Entfernen" : "Einladung zurücknehmen"}</button>
                  {/if}
                </td>
              </tr>
              {#if entfernen === m.kellerwolke}
                {@const offen = m.konto ? offeneKarten(m.konto) : []}
                {@const laeuft = m.konto ? timer(m.konto) : []}
                <tr class="pw-verwaltung-zusatz"><td colspan="4">
                  <div class="hinweis gefahr" role="alert"><i class="fa-solid fa-user-xmark"></i>
                    {#if m.konto}
                      <div><b>{name(m)} aus dem Board entfernen?</b> Das Board verschwindet aus der Seitenleiste von {name(m).split(" ")[0]}.
                        {#if offen.length}An {offen.length === 1 ? "einer offenen Karte" : `${offen.length} offenen Karten`} ({offen.map((k) => k.schluessel).join(", ")})
                          fällt die Zuständigkeit weg.{/if}
                        {#if laeuft.length}Der laufende Timer an {laeuft.map((k) => k.schluessel).join(", ")} hält an und bucht.{/if}
                        {#if zeiten}Gebuchte Zeiten bleiben an den Karten und im Zeitkonto.{/if}</div>
                    {:else}
                      <div><b>Einladung an {m.kellerwolke} zurücknehmen?</b> Die Person hat sich noch nie angemeldet; das Board steht dann nicht
                        mehr für sie bereit.</div>
                    {/if}
                    <span class="rechts"><button class="knopf klein" onclick={() => (entfernen = null)}>Abbrechen</button>
                      <button class="knopf gefahr-voll klein" onclick={() => entfernenBestaetigen(m)}>
                        <i class="fa-solid fa-user-xmark"></i>{m.konto ? "Entfernen" : "Zurücknehmen"}</button></span>
                  </div>
                </td></tr>
              {/if}
              {#if uebertragen && einziger(m)}
                <tr class="pw-verwaltung-zusatz"><td colspan="4">
                  <div class="hinweis"><i class="fa-solid fa-crown"></i>
                    <div><b>Besitz übertragen</b> an
                      <select class="eingabe" bind:value={an} aria-label="Neuer Besitzer">
                        {#each nachfolger as x (x.kellerwolke)}<option value={x.kellerwolke}>{name(x)}</option>{/each}
                      </select>; du wirst
                      <select class="eingabe" bind:value={ichWerde} aria-label="Deine Rolle danach">
                        {#each board.rollen.filter((r) => r.id !== "besitzer") as r (r.id)}<option value={r.id}>{r.name}</option>{/each}
                      </select>.
                      Ab dann verwaltet {anName.split(" ")[0]} Board, Rollen und Mitglieder.</div>
                    <span class="rechts"><button class="knopf klein" onclick={() => (uebertragen = false)}>Abbrechen</button>
                      <button class="knopf klein" onclick={uebertragenBestaetigen}><i class="fa-solid fa-crown"></i>Übertragen</button></span>
                  </div>
                </td></tr>
              {/if}
            {/each}
          </tbody>
        </table>
      </div>
      {#if besitzer.length === 1}
        <p class="pw-verwaltung-satz"><i class="fa-solid fa-crown"></i>Ein Board hat immer mindestens einen Besitzer. Weitere Besitzer
          bekommst du über die Rolle; gehen kann der einzige erst, wenn er den Besitz übertragen hat, an jemanden, der schon angemeldet war.</p>
      {/if}
    </section>
  </div>
</div>
