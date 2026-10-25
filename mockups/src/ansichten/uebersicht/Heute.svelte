<script lang="ts">
  // Heute: alles für dich aus allen Boards, in denen du Mitglied bist (Vorbild "Was steht an" der alten App). Links deine
  // Karten nach Fälligkeit, rechts Termine und heute fällige Serienkarten, oben dein laufender Timer. Abhaken, Timer und
  // Zusagen wirken sofort; jede Karte öffnet über ihren Pfad. Ohne Verbindung bleibt der letzte Stand sichtbar und
  // alles Schreibende ist gesperrt, damit nichts scheinbar gespeichert wird.
  import { SvelteSet } from "svelte/reactivity";
  import { HEUTE, ICH, SERIEN, TERMINE } from "../../beispiel/daten";
  import { datum } from "../../beispiel/format";
  import { stand } from "../../beispiel/stand.svelte";
  import { heuteGruppen, meineTermine } from "./heute";
  import HeuteZeile from "./HeuteZeile.svelte";
  import Laufend from "./Laufend.svelte";
  import Meldung from "./Meldung.svelte";
  import type { HeuteEintrag } from "./modell";
  import TerminZeile from "./TerminZeile.svelte";

  let { entwurf = "" }: { entwurf?: string } = $props();
  const leer = $derived(entwurf === "leer");
  const getrennt = $derived(entwurf === "getrennt");
  /** vorgeführt ohne Verbindung: dieser Haken kam nicht mehr beim Server an */
  const NICHT_GESPEICHERT = "c-h58";

  const g = $derived(heuteGruppen());
  const termine = $derived(meineTermine());
  const laufend = $derived(stand.karten.find((k) => k.laeuft?.konto === ICH));
  const laufendBoard = $derived(laufend ? stand.boards.find((b) => b.id === laufend.board) : undefined);
  const boardZahl = $derived(stand.boards.filter((b) => b.mitglieder.some((m) => m.konto === ICH)).length);
  const zugesagt = new SvelteSet(TERMINE.filter((t) => t.bestaetigt.includes(ICH)).map((t) => t.id));
  let vorlesen = $state(false);

  const gruppen = $derived([
    { name: "Überfällig", symbol: "fa-triangle-exclamation", gefahr: true, liste: g.ueberfaellig, ruhig: "Nichts überfällig.", titel: "" },
    { name: "Heute", symbol: "fa-calendar-day", gefahr: false, liste: g.heute, ruhig: "Heute ist keine Karte fällig.", titel: "" },
    { name: "Diese Woche", symbol: "fa-calendar-week", gefahr: false, liste: g.woche, ruhig: "In den nächsten sieben Tagen ist nichts fällig.",
      titel: "Fällig in den nächsten sieben Tagen" },
    { name: "Ohne Datum", symbol: "fa-inbox", gefahr: false, liste: g.ohneDatum, ruhig: "Keine Karte ohne Fälligkeit.",
      titel: "Dir zugewiesen, ohne Fälligkeit" },
  ]);

  function serienzeit(e: HeuteEintrag): string {
    return SERIEN.find((s) => s.id === e.karte.serie)?.uhrzeit ?? "";
  }
</script>

<div class="pw-uebersicht-seite">
  <div class="rahmen-kopf">
    <div class="seitenkopf">
      <h1>Heute</h1>
      <div class="aktionen">
        <button class="knopf" class:aktiv={vorlesen} title="Tagesplan vorlesen: Überfälliges, Heute, Termine und Serien"
                onclick={() => (vorlesen = !vorlesen)}><i class="fa-solid {vorlesen ? 'fa-stop' : 'fa-volume-high'}"></i>{vorlesen ? "Stopp" : "Vorlesen"}</button>
      </div>
      <div class="unterzeile">{datum(HEUTE, true)}2026 · deine Karten, Termine und Serien aus {boardZahl} Boards</div>
    </div>
    {#if getrennt || (laufend && laufendBoard && !leer)}
      <div class="pw-uebersicht-kopfteile">
        {#if getrennt}
          <div class="hinweis warnung"><i class="fa-solid fa-plug-circle-xmark"></i>
            <div><b>Keine Verbindung zum Server seit 10:41.</b> Du siehst den Stand von 10:41. Abhaken, Timer und Zusagen sind
              gesperrt, bis sie wieder steht. Nicht gespeichert: dein Haken an HAUS-58. Nächster Versuch in 8 Sekunden.</div>
            <span class="rechts"><button class="knopf klein"><i class="fa-solid fa-plug"></i>Jetzt verbinden</button></span>
          </div>
        {/if}
        {#if laufend && laufendBoard && !leer}<Laufend karte={laufend} board={laufendBoard} gesperrt={getrennt} />{/if}
      </div>
    {/if}
  </div>

  {#if leer}
    <div class="rollfeld">
      <div class="leer">
        <i class="fa-solid fa-mug-hot"></i>
        <h2>Heute ist nichts fällig</h2>
        <p>Keine überfällige Karte, nichts für heute oder diese Woche, kein Termin und keine Serie. Was dir jemand zuweist, erscheint
          hier sofort.</p>
      </div>
    </div>
  {:else}
    <div class="spalten pw-uebersicht-spalten">
      <div class="rollfeld">
        {#each gruppen as gr (gr.name)}
          <section class="pw-uebersicht-gruppe" aria-label={gr.name}>
            <h2 title={gr.titel || undefined} class:gefahr={gr.gefahr && gr.liste.length > 0}>
              <i class="fa-solid {gr.symbol}"></i>{gr.name}
              <span class="zaehler" class:gefahr={gr.gefahr && gr.liste.length > 0}>{gr.liste.length}</span></h2>
            {#each gr.liste as e (e.karte.id)}
              <HeuteZeile eintrag={e} gesperrt={getrennt} fehler={getrennt && e.karte.id === NICHT_GESPEICHERT ? "Haken nicht gespeichert" : ""} />
            {:else}
              <p class="pw-uebersicht-ruhig"><i class="fa-solid fa-circle-check"></i>{gr.ruhig}</p>
            {/each}
          </section>
        {/each}
      </div>
      <div class="rollfeld">
        <section class="pw-uebersicht-gruppe" aria-label="Termine">
          <h2><i class="fa-solid fa-calendar-check"></i>Termine heute<span class="zaehler">{termine.heute.length}</span></h2>
          {#each termine.heute as t (t.id)}
            <TerminZeile termin={t} zugesagt={zugesagt.has(t.id)} gesperrt={getrennt} zusagen={() => zugesagt.add(t.id)} />
          {:else}
            <p class="pw-uebersicht-ruhig"><i class="fa-solid fa-circle-check"></i>Heute keine Termine.</p>
          {/each}
          {#if termine.woche.length}
            <div class="etikett">Nächste sieben Tage</div>
            {#each termine.woche as t (t.id)}
              <TerminZeile termin={t} mitTag zugesagt={zugesagt.has(t.id)} gesperrt={getrennt} zusagen={() => zugesagt.add(t.id)} />
            {/each}
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
  {/if}
  <Meldung />
</div>
