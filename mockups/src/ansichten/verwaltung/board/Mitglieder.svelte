<script lang="ts">
  // Mitglieder: einladen per Name eines Kellerwolke-Kontos (Textfeld mit Vorschlägen), je Person die Rolle aus den
  // Rollen des Boards und seit wann; entfernen mit Rückfrage, die sagt, was an Karten und Timern geschieht; Besitz
  // übertragen. Ein Board hat immer mindestens einen Besitzer: der einzige kann weder gehen noch seine Rolle abgeben,
  // bevor er den Besitz überträgt.
  import { untrack } from "svelte";
  import { HEUTE, ICH } from "../../../beispiel/daten";
  import { datum } from "../../../beispiel/format";
  import { konto, stand } from "../../../beispiel/stand.svelte";
  import Person from "../../../board/Person.svelte";
  import type { Board, Mitglied } from "../../../modell";
  import { KENNUNGEN, MITGLIED_SEIT, type Vorschlag } from "../daten";
  import Personenwahl from "../Personenwahl.svelte";

  let { board }: { board: Board; entwurf?: string } = $props();

  const mitJahr = (iso: string) => datum(iso) + iso.slice(0, 4);
  const seit = (k: string) => MITGLIED_SEIT[board.id]?.[k] ?? HEUTE;
  const rolleName = (id: string) => board.rollen.find((r) => r.id === id)?.name ?? "";
  const besitzer = $derived(board.mitglieder.filter((m) => m.rolle === "besitzer"));
  const einziger = (m: Mitglied) => m.rolle === "besitzer" && besitzer.length === 1;
  const offeneKarten = (k: string) => stand.karten.filter((x) => x.board === board.id && x.zustaendig.includes(k)
    && !board.spalten.find((s) => s.id === x.spalte)?.erledigt);
  const timer = (k: string) => stand.karten.filter((x) => x.board === board.id && x.laeuft?.konto === k);

  // einladen
  let suche = $state("ka");
  let gewaehlt = $state<Vorschlag | null>(null);
  let rolle = $state("mitglied");
  let neu = $state<(Vorschlag & { rolle: string })[]>([]);
  let gemeldet = $state("");
  $effect(() => { board.id; untrack(() => { suche = "ka"; gewaehlt = null; neu = []; gemeldet = ""; entfernen = null; uebertragen = false; }); });

  function einladen(): void {
    if (!gewaehlt) return;
    if (gewaehlt.konto) board.mitglieder.push({ konto: gewaehlt.konto, rolle });
    else neu = [...neu, { ...gewaehlt, rolle }];
    gemeldet = `${gewaehlt.name} ist eingeladen und sieht das Board ab sofort in der Seitenleiste.`;
    gewaehlt = null;
  }

  // entfernen und Besitz übertragen
  let entfernen = $state<string | null>(null);
  let uebertragen = $state(false);
  let an = $state("");
  let ichWerde = $state("mitglied");
  function uebertragenStarten(): void {
    uebertragen = true;
    an = board.mitglieder.find((m) => m.konto !== ICH)?.konto ?? "";
    ichWerde = "mitglied";
  }
  function uebertragenAusfuehren(): void {
    const ziel = board.mitglieder.find((m) => m.konto === an);
    const ich = board.mitglieder.find((m) => m.konto === ICH);
    if (ziel) ziel.rolle = "besitzer";
    if (ich) ich.rolle = ichWerde;
    uebertragen = false;
  }
</script>

<div class="rollfeld">
  <div class="pw-verwaltung-flaeche">
    <section class="bereich">
      <h2 class="etikett">Einladen</h2>
      <div class="pw-verwaltung-formular">
        {#if gewaehlt}
          <span class="chip pw-verwaltung-gewaehlt">{#if gewaehlt.konto}<Person id={gewaehlt.konto} />{:else}<i class="fa-solid fa-user"></i>{/if}
            {gewaehlt.name}<button class="knopf ohne symbol klein" title="Andere Person wählen" aria-label="Andere Person wählen"
                                   onclick={() => (gewaehlt = null)}><i class="fa-solid fa-xmark"></i></button></span>
        {:else}
          <Personenwahl bind:text={suche} ausser={board.mitglieder.map((m) => m.konto)} waehlen={(p) => { gewaehlt = p; gemeldet = ""; }} />
        {/if}
        <span class="pw-verwaltung-mit">als</span>
        <select class="eingabe" bind:value={rolle} aria-label="Rolle der eingeladenen Person">
          {#each board.rollen as r (r.id)}<option value={r.id}>{r.name}</option>{/each}
        </select>
        <button class="knopf haupt" disabled={!gewaehlt} onclick={einladen}><i class="fa-solid fa-paper-plane"></i>Einladen</button>
      </div>
      <p class="pw-verwaltung-satz">Wer ein Kellerwolke-Konto hat, lässt sich per Name finden; die Person bekommt einen Hinweis und sieht das Board
        sofort. Wer noch kein Board hat, bekommt dabei Kürzel und Farbe.</p>
      {#if gemeldet}<div class="hinweis erfolg"><i class="fa-solid fa-circle-check"></i><div>{gemeldet}</div></div>{/if}
    </section>

    <section class="bereich">
      <h2 class="etikett">Mitglieder</h2>
      <div class="tabellen-raum pw-verwaltung-tabelle">
        <table class="tabelle karten">
          <thead><tr><th>Person</th><th>Rolle</th><th>Seit</th><th></th></tr></thead>
          <tbody>
            {#each board.mitglieder as m (m.konto)}
              {@const p = konto(m.konto)}
              <tr>
                <td><span class="pw-verwaltung-person"><Person id={m.konto} gross />
                  <span class="wer"><b>{p.name}{m.konto === ICH ? " (du)" : ""}</b><span class="pw-schluessel">{KENNUNGEN[m.konto]}</span></span></span></td>
                <td data-titel="Rolle">
                  <select class="eingabe" bind:value={m.rolle} disabled={einziger(m)} aria-label="Rolle von {p.name}"
                          title={einziger(m) ? "Einziger Besitzer: erst den Besitz übertragen" : `Rolle von ${p.name}`}>
                    {#each board.rollen as r (r.id)}<option value={r.id}>{r.name}</option>{/each}
                  </select></td>
                <td data-titel="Seit" class="pw-verwaltung-datum">{mitJahr(seit(m.konto))}</td>
                <td data-titel="Aktion" class="pw-verwaltung-aktion">
                  {#if einziger(m)}
                    <button class="knopf klein" disabled={uebertragen || board.mitglieder.length === 1} onclick={uebertragenStarten}
                            title={board.mitglieder.length === 1 ? "Erst eine weitere Person einladen" : "Den Besitz an ein anderes Mitglied geben"}>
                      <i class="fa-solid fa-crown"></i>Besitz übertragen</button>
                  {:else}
                    <button class="knopf ohne klein gefahr" disabled={entfernen === m.konto} onclick={() => (entfernen = m.konto)}>
                      <i class="fa-solid fa-user-xmark"></i>Entfernen</button>
                  {/if}
                </td>
              </tr>
              {#if entfernen === m.konto}
                {@const offen = offeneKarten(m.konto)}
                {@const laeuft = timer(m.konto)}
                <tr class="pw-verwaltung-zusatz"><td colspan="4">
                  <div class="hinweis gefahr" role="alert"><i class="fa-solid fa-user-xmark"></i>
                    <div><b>{p.name} aus dem Board entfernen?</b> Das Board verschwindet aus der Seitenleiste von {p.name.split(" ")[0]}.
                      {#if offen.length}An {offen.length === 1 ? "einer offenen Karte" : `${offen.length} offenen Karten`} ({offen.map((k) => k.schluessel).join(", ")})
                        fällt die Zuständigkeit weg.{/if}
                      {#if laeuft.length}Der laufende Timer an {laeuft.map((k) => k.schluessel).join(", ")} hält an und bucht.{/if}
                      Gebuchte Zeiten bleiben an den Karten und im Zeitkonto.</div>
                    <span class="rechts"><button class="knopf klein" onclick={() => (entfernen = null)}>Abbrechen</button>
                      <button class="knopf gefahr-voll klein" onclick={() => { board.mitglieder = board.mitglieder.filter((x) => x.konto !== m.konto); entfernen = null; }}>
                        <i class="fa-solid fa-user-xmark"></i>Entfernen</button></span>
                  </div>
                </td></tr>
              {/if}
              {#if uebertragen && einziger(m)}
                <tr class="pw-verwaltung-zusatz"><td colspan="4">
                  <div class="hinweis"><i class="fa-solid fa-crown"></i>
                    <div><b>Besitz übertragen</b> an
                      <select class="eingabe" bind:value={an} aria-label="Neuer Besitzer">
                        {#each board.mitglieder.filter((x) => x.konto !== m.konto) as x (x.konto)}<option value={x.konto}>{konto(x.konto).name}</option>{/each}
                      </select>; du wirst
                      <select class="eingabe" bind:value={ichWerde} aria-label="Deine Rolle danach">
                        {#each board.rollen.filter((r) => r.id !== "besitzer") as r (r.id)}<option value={r.id}>{r.name}</option>{/each}
                      </select>.
                      Ab dann verwaltet {konto(an).name.split(" ")[0]} Board, Rollen und Mitglieder.</div>
                    <span class="rechts"><button class="knopf klein" onclick={() => (uebertragen = false)}>Abbrechen</button>
                      <button class="knopf klein" onclick={uebertragenAusfuehren}><i class="fa-solid fa-crown"></i>Übertragen</button></span>
                  </div>
                </td></tr>
              {/if}
            {/each}
            {#each neu as p (p.kennung)}
              <tr>
                <td><span class="pw-verwaltung-person"><span class="pw-verwaltung-neuperson gross"><i class="fa-solid fa-user"></i></span>
                  <span class="wer"><b>{p.name}</b><span class="pw-schluessel">{p.kennung}</span></span></span></td>
                <td data-titel="Rolle">{rolleName(p.rolle)}</td>
                <td data-titel="Seit" class="pw-verwaltung-datum">{mitJahr(HEUTE)}</td>
                <td data-titel="Aktion" class="pw-verwaltung-aktion"><span class="zustand fertig"><i class="fa-solid fa-check"></i>neu dabei</span></td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
      {#if besitzer.length === 1}
        <p class="pw-verwaltung-satz"><i class="fa-solid fa-crown"></i>Ein Board hat immer mindestens einen Besitzer. Weitere Besitzer
          bekommst du über die Rolle; gehen kann der einzige erst, wenn er den Besitz übertragen hat.</p>
      {/if}
    </section>
  </div>
</div>
