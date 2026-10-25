<script lang="ts">
  // Heute: alles für dich aus allen Boards, in denen du Mitglied bist (Vorbild "Was steht an" der alten App). Links deine
  // Karten nach Fälligkeit, rechts Termine und heute fällige Serienkarten, oben dein Timer. Abhaken, Timer und Zusagen
  // laufen über die Anwendungsfälle; jede Karte öffnet über ihren Pfad. Ohne Verbindung bleibt der letzte Stand sichtbar
  // und alles Schreibende ist gesperrt, damit nichts scheinbar gespeichert wird.
  import { untrack } from "svelte";
  import { meinTag, timerVon, type MeinTag, type TagEintrag } from "../../beispiel/abfragen";
  import { erledigen } from "../../beispiel/anwendung/karten.svelte";
  import { meldungSchliessen } from "../../beispiel/anwendung/meldung.svelte";
  import { stoppen } from "../../beispiel/anwendung/timer.svelte";
  import { verbindungGemeldet } from "../../beispiel/anwendung/verbindung.svelte";
  import { HEUTE, ICH } from "../../beispiel/daten";
  import { datumJahr } from "../../beispiel/format";
  import { board, karte, stand } from "../../beispiel/stand.svelte";
  import HeuteZeile from "./HeuteZeile.svelte";
  import Laufend from "./Laufend.svelte";
  import TerminZeile from "./TerminZeile.svelte";

  let { entwurf = "" }: { entwurf?: string } = $props();

  /** Alles, was fällig ist (überfällig, heute, diese Woche, Serien heute) */
  function faellige(t: MeinTag): TagEintrag[] {
    return [...t.ueberfaellig, ...t.heute, ...t.woche, ...t.serien];
  }

  // vorgeführte Zustände richten sich nach dem Ausgangsstand über die Anwendungsfälle ein (einmal je Entwurf)
  const VORBEREITEN: Record<string, () => void> = {
    /** nichts fällig: deine fälligen Karten sind erledigt, dein Timer gestoppt */
    leer: () => {
      for (const e of faellige(meinTag())) erledigen(e.karte.id);
      stoppen();
      meldungSchliessen();
    },
    /** Verbindung getrennt; dein Haken an HAUS-58 kommt nicht mehr an und wird abgewiesen */
    getrennt: () => {
      verbindungGemeldet("getrennt");
      erledigen("c-h58");
    },
  };
  const vorbereiten = $derived(VORBEREITEN[entwurf]);
  $effect(() => { const v = vorbereiten; untrack(() => v?.()); });

  const getrennt = $derived(stand.verbindung === "getrennt");
  const g = $derived(meinTag());
  const nichtsFaellig = $derived(faellige(g).length === 0);
  const termine = $derived(g.termine);
  // Liegengeblieben und Blockiert als eigene Abschnitte (wie in der alten App), jede Karte nur einmal: was schon wegen
  // Fälligkeit steht, steht nicht noch einmal; was liegt, steht nicht noch unter Blockiert oder Ohne Datum
  const liegt = $derived(g.liegengeblieben);
  const blockiert = $derived(g.blockiert.filter((e) => !liegt.includes(e)));
  const ohneDatumRest = $derived(g.ohneDatum.filter((e) => !liegt.includes(e) && !blockiert.includes(e)));
  const timer = $derived(timerVon(ICH));
  const timerKarte = $derived(timer ? karte(timer.karte) : undefined);
  const boardZahl = $derived(stand.boards.filter((b) => b.mitglieder.some((m) => m.konto === ICH)).length);
  let vorlesen = $state(false);

  const gruppen = $derived([
    { name: "Überfällig", symbol: "fa-triangle-exclamation", gefahr: true, liste: g.ueberfaellig, ruhig: "Nichts überfällig.", titel: "" },
    { name: "Heute", symbol: "fa-calendar-day", gefahr: false, liste: g.heute, ruhig: "Heute ist keine Karte fällig.", titel: "" },
    { name: "Diese Woche", symbol: "fa-calendar-week", gefahr: false, liste: g.woche, ruhig: "In den nächsten sieben Tagen ist nichts fällig.",
      titel: "Fällig in den nächsten sieben Tagen" },
  ]);

  function serienzeit(e: TagEintrag): string {
    return stand.serien.find((s) => s.id === e.karte.serie)?.uhrzeit ?? "";
  }
</script>

{#snippet ohneDatum()}
  <section class="pw-uebersicht-gruppe" aria-label="Ohne Datum">
    <h2 title="Dir zugewiesen, ohne Fälligkeit"><i class="fa-solid fa-inbox"></i>Ohne Datum<span class="zaehler">{ohneDatumRest.length}</span></h2>
    {#each ohneDatumRest as e (e.karte.id)}
      <HeuteZeile eintrag={e} gesperrt={getrennt} />
    {:else}
      <p class="pw-uebersicht-ruhig"><i class="fa-solid fa-circle-check"></i>Keine Karte ohne Fälligkeit.</p>
    {/each}
  </section>
{/snippet}

<div class="pw-uebersicht-seite">
  <div class="rahmen-kopf">
    <div class="seitenkopf">
      <h1>Heute</h1>
      <div class="aktionen">
        <button class="knopf" class:aktiv={vorlesen} title="Tagesplan vorlesen: Überfälliges, Heute, Termine und Serien"
                onclick={() => (vorlesen = !vorlesen)}><i class="fa-solid {vorlesen ? 'fa-stop' : 'fa-volume-high'}"></i>{vorlesen ? "Stopp" : "Vorlesen"}</button>
      </div>
      <div class="unterzeile">{datumJahr(HEUTE, true)} · deine Karten, Termine und Serien aus {boardZahl} Boards</div>
    </div>
    {#if getrennt || (timer && timerKarte)}
      <div class="pw-uebersicht-kopfteile">
        {#if getrennt}
          <div class="hinweis warnung"><i class="fa-solid fa-plug-circle-xmark"></i>
            <div><b>Keine Verbindung zum Server.</b> Du siehst den letzten Stand. Abhaken, Timer und Zusagen sind gesperrt, bis sie
              wieder steht; was du jetzt tust, wird nicht gespeichert. Die Pinnwand verbindet sich von selbst neu, nächster Versuch in
              8 Sekunden.</div>
          </div>
        {/if}
        {#if timer && timerKarte}<Laufend {timer} karte={timerKarte} board={board(timerKarte.board)} gesperrt={getrennt} />{/if}
      </div>
    {/if}
  </div>

  <div class="spalten pw-uebersicht-spalten">
    <div class="rollfeld">
      {#if nichtsFaellig}
        <div class="leer pw-uebersicht-nichts">
          <i class="fa-solid fa-mug-hot"></i>
          <h2>Heute ist nichts fällig</h2>
          <p>Keine überfällige Karte, nichts für heute oder die nächsten sieben Tage und keine Serie. Was dir jemand zuweist, erscheint
            hier sofort.</p>
        </div>
      {:else}
        {#each gruppen as gr (gr.name)}
          <section class="pw-uebersicht-gruppe" aria-label={gr.name}>
            <h2 title={gr.titel || undefined} class:gefahr={gr.gefahr && gr.liste.length > 0}>
              <i class="fa-solid {gr.symbol}"></i>{gr.name}
              <span class="zaehler" class:gefahr={gr.gefahr && gr.liste.length > 0}>{gr.liste.length}</span></h2>
            {#each gr.liste as e (e.karte.id)}
              <HeuteZeile eintrag={e} gesperrt={getrennt} />
            {:else}
              <p class="pw-uebersicht-ruhig"><i class="fa-solid fa-circle-check"></i>{gr.ruhig}</p>
            {/each}
          </section>
        {/each}
      {/if}
      {#if liegt.length}
        <section class="pw-uebersicht-gruppe" aria-label="Liegengeblieben">
          <h2 title="Offen, ohne laufenden Timer und seit der Gefahrschwelle des Boards nicht bewegt"><i class="fa-solid fa-hourglass-end"></i>Liegengeblieben<span class="zaehler">{liegt.length}</span></h2>
          {#each liegt as e (e.karte.id)}<HeuteZeile eintrag={e} gesperrt={getrennt} />{/each}
        </section>
      {/if}
      {#if blockiert.length}
        <section class="pw-uebersicht-gruppe" aria-label="Blockiert">
          <h2 title="Offen und blockiert, mit Grund"><i class="fa-solid fa-ban"></i>Blockiert<span class="zaehler">{blockiert.length}</span></h2>
          {#each blockiert as e (e.karte.id)}<HeuteZeile eintrag={e} gesperrt={getrennt} />{/each}
        </section>
      {/if}
      {@render ohneDatum()}
    </div>
    <div class="rollfeld">
      <section class="pw-uebersicht-gruppe" aria-label="Termine heute">
        <h2><i class="fa-solid fa-calendar-check"></i>Termine heute<span class="zaehler">{termine.heute.length}</span></h2>
        {#each termine.heute as t (t.id)}
          <TerminZeile termin={t} gesperrt={getrennt} />
        {:else}
          <p class="pw-uebersicht-ruhig"><i class="fa-solid fa-circle-check"></i>Heute keine Termine.</p>
        {/each}
        {#if termine.woche.length}
          <div class="etikett">Nächste sieben Tage</div>
          {#each termine.woche as t (t.id)}<TerminZeile termin={t} mitTag gesperrt={getrennt} />{/each}
        {/if}
      </section>
      <section class="pw-uebersicht-gruppe" aria-label="Serien heute">
        <h2 title="Heute fällige Karten aus Serien"><i class="fa-solid fa-repeat"></i>Serien heute<span class="zaehler">{g.serien.length}</span></h2>
        {#each g.serien as e (e.karte.id)}
          <HeuteZeile eintrag={e} uhrzeit={serienzeit(e)} gesperrt={getrennt} />
        {:else}
          <p class="pw-uebersicht-ruhig"><i class="fa-solid fa-circle-check"></i>Heute ist keine Serie fällig.</p>
        {/each}
      </section>
    </div>
  </div>
</div>
