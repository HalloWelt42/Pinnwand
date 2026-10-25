<script lang="ts">
  // Menü einer Spalte im Board (Mechanik M-21), nur mit dem Recht "Board verwalten": Name, Farbe, Grenze oder bei der
  // Erledigt-Spalte die Vorgabe des Zeitfensters; einklappen, nach links oder rechts, zur Erledigt-Spalte machen und
  // löschen mit Rückfrage in der Fläche (Karten verschieben oder mit der Spalte in den Papierkorb). Felder speichern beim
  // Verlassen oder mit Enter, Befehle schließen das Menü; Escape oder ein Klick daneben schließt es auch (in der alten App
  // blieb es offen). Alles über die Anwendungsfälle mit Rückgängig.
  import { untrack } from "svelte";
  import { ZEITFENSTER, ZEITFENSTER_VORGABE } from "../anzeige";
  import { EINSTELLUNG_GRENZEN as GRENZEN } from "../regeln/board";
  import Zahlfeld from "../teile/Zahlfeld.svelte";
  import { spalteAendern, spalteLoeschen, spaltenOrdnen, zurErledigtSpalte } from "../daten/anwendung/boards.svelte";
  import { kartenDerSpalte } from "../daten/stand.svelte";
  import type { Board, Spalte, Zeitfenster } from "../modell";
  import Farbwahl from "../teile/Farbwahl.svelte";

  let { board, spalte, einklappen, schliessen, anker }: {
    board: Board; spalte: Spalte;
    einklappen: () => void;
    schliessen: () => void;
    /** der Knopf, der das Menü öffnet: ein Klick darauf ist kein Klick daneben */
    anker?: HTMLElement;
  } = $props();

  let menue: HTMLElement;
  let nameFeld = $state<HTMLInputElement>();
  // beim Öffnen ganz in Sicht (die Spalte kann halb aus dem Streifen ragen), der Fokus im Namen
  $effect(() => {
    menue.scrollIntoView({ block: "nearest", inline: "nearest" });
    untrack(() => nameFeld?.focus({ preventScroll: true }));
  });
  const platz = $derived(board.spalten.findIndex((s) => s.id === spalte.id));
  const loeschbar = $derived(!spalte.erledigt && board.spalten.length > 1);
  const anzahl = (n: number) => `${n} ${n === 1 ? "Karte" : "Karten"}`;

  // Klick daneben schließt (in der Fangphase, damit kein anderer Teil ihn verschluckt)
  $effect(() => {
    const daneben = (e: PointerEvent): void => {
      const ziel = e.target as Node;
      if (!menue.contains(ziel) && !anker?.contains(ziel)) schliessen();
    };
    window.addEventListener("pointerdown", daneben, true);
    return () => window.removeEventListener("pointerdown", daneben, true);
  });

  function taste(e: KeyboardEvent): void {
    if (e.key !== "Escape") return;
    e.stopPropagation();
    schliessen();
    anker?.focus();
  }

  function umbenennen(e: Event): void {
    const feld = e.currentTarget as HTMLInputElement;
    if (!spalteAendern(board.id, spalte.id, { name: feld.value })) feld.value = spalte.name;
  }
  function nameTaste(e: KeyboardEvent): void {
    const feld = e.currentTarget as HTMLInputElement;
    if (e.key === "Enter") feld.blur();
    if (e.key === "Escape") feld.value = spalte.name;
  }

  /** Befehl ausführen und schließen */
  function tun(befehl: () => unknown): void {
    befehl();
    schliessen();
  }
  function verschieben(um: -1 | 1): void {
    const ids = board.spalten.map((s) => s.id);
    [ids[platz], ids[platz + um]] = [ids[platz + um], ids[platz]];
    tun(() => spaltenOrdnen(board.id, ids));
  }

  // Rückfrage beim Löschen: eine Sache der Ansicht, geändert wird erst mit dem Knopf
  let fragen = $state(false);
  let weg = $state<"verschieben" | "papierkorb">("verschieben");
  let ziel = $state("");
  function loeschenFragen(): void {
    fragen = true;
    weg = "verschieben";
    ziel = (board.spalten.slice(0, platz).reverse().find((s) => !s.erledigt) ?? board.spalten.find((s, i) => i > platz && !s.erledigt))?.id ?? "";
  }
  const betroffen = $derived(kartenDerSpalte(spalte.id).length);
  const zielSpalte = $derived(board.spalten.find((s) => s.id === ziel));
  const danach = $derived(zielSpalte ? kartenDerSpalte(zielSpalte.id).length + betroffen : 0);
  function loeschen(): void {
    if (spalteLoeschen(board.id, spalte.id, weg === "verschieben" && betroffen ? ziel : undefined)) schliessen();
  }
</script>

<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
<div class="pw-spaltenmenue" role="dialog" aria-label="Spalte {spalte.name} bearbeiten" tabindex="-1" bind:this={menue} onkeydown={taste}>
  {#if fragen}
    <div class="hinweis gefahr" role="alert"><i class="fa-solid fa-trash-can"></i>
      <div>
        <b>Spalte {spalte.name} löschen?</b>
        {#if betroffen}Sie hat {anzahl(betroffen)}. Wohin damit?{:else}Sie ist leer.{/if}
        {#if betroffen}
          <div class="wahl">
            <label class:an={weg === "verschieben"}>
              <input type="radio" name="wohin-{spalte.id}" value="verschieben" bind:group={weg} /><span class="kreis"></span>
              <div><b>Verschieben nach</b>
                <select class="eingabe" bind:value={ziel} aria-label="Zielspalte der Karten">
                  {#each board.spalten.filter((x) => x.id !== spalte.id) as x (x.id)}<option value={x.id}>{x.name}</option>{/each}
                </select>
                <span>Wie beim Ziehen: das Alter beginnt neu, verknüpfte Karten ziehen mit.{zielSpalte?.erledigt ? " Sie gelten dann als erledigt, laufende Timer buchen." : ""}</span>
                {#if zielSpalte?.grenze !== undefined && danach > zielSpalte.grenze}
                  <span class="pw-spaltenmenue-warnung"><i class="fa-solid fa-triangle-exclamation"></i>{zielSpalte.name} hat danach {danach} bei Grenze {zielSpalte.grenze}</span>
                {/if}
              </div>
            </label>
            <label class:an={weg === "papierkorb"}>
              <input type="radio" name="wohin-{spalte.id}" value="papierkorb" bind:group={weg} /><span class="kreis"></span>
              <div><b>Mit in den Papierkorb</b><span>Wiederherstellen bringt die Spalte mit allem an ihre Stelle zurück.</span></div>
            </label>
          </div>
        {/if}
      </div>
      <span class="rechts">
        <button class="knopf klein" onclick={() => (fragen = false)}>Abbrechen</button>
        <button class="knopf gefahr-voll klein" onclick={loeschen}><i class="fa-solid fa-trash-can"></i>Spalte löschen</button>
      </span>
    </div>
  {:else}
    <label class="pw-spaltenmenue-feld"><span class="etikett">Name</span>
      <input class="eingabe" value={spalte.name} bind:this={nameFeld} aria-label="Name der Spalte" onchange={umbenennen} onkeydown={nameTaste} /></label>
    <div class="pw-spaltenmenue-feld"><span class="etikett">Farbe</span>
      <Farbwahl wert={spalte.farbe} waehlen={(f) => f && spalteAendern(board.id, spalte.id, { farbe: f })} wofuer="Farbe der Spalte {spalte.name}" /></div>
    {#if spalte.erledigt}
      <label class="pw-spaltenmenue-feld" title="Welche erledigten Karten die Spalte zeigt, solange jemand es nicht für sich umstellt">
        <span class="etikett">Zeitfenster für alle</span>
        <select class="eingabe" value={spalte.zeitfenster ?? ZEITFENSTER_VORGABE} aria-label="Vorgabe des Zeitfensters der Spalte {spalte.name}"
                onchange={(e) => spalteAendern(board.id, spalte.id, { zeitfenster: e.currentTarget.value as Zeitfenster })}>
          {#each Object.entries(ZEITFENSTER) as [w, t] (w)}<option value={w}>{t}</option>{/each}
        </select></label>
    {:else}
      <div class="pw-spaltenmenue-feld" title="Ab so vielen offenen Karten warnt die Spalte; sie hält nichts auf. Leer heißt keine Grenze">
        <span class="etikett">Grenze</span>
        <Zahlfeld wert={spalte.grenze} setzen={(g) => spalteAendern(board.id, spalte.id, { grenze: g ?? null })} min={GRENZEN.grenze[0]}
                  max={GRENZEN.grenze[1]} leer="keine" name="Grenze der Spalte {spalte.name}" einheit="offene Karten" /></div>
    {/if}
    <div class="pw-spaltenmenue-befehle">
      <button class="knopf ohne klein" onclick={() => tun(einklappen)} title="Nur für dich an diesem Gerät; Karten lassen sich weiter hineinziehen">
        <i class="fa-solid fa-angles-left"></i>Einklappen</button>
      {#if platz > 0}
        <button class="knopf ohne klein" onclick={() => verschieben(-1)}><i class="fa-solid fa-arrow-left"></i>Nach links</button>
      {/if}
      {#if platz < board.spalten.length - 1}
        <button class="knopf ohne klein" onclick={() => verschieben(1)}><i class="fa-solid fa-arrow-right"></i>Nach rechts</button>
      {/if}
      {#if !spalte.erledigt}
        <button class="knopf ohne klein" onclick={() => tun(() => zurErledigtSpalte(board.id, spalte.id))}
                title="Ihre Karten gelten dann als erledigt (Abschluss heute, laufende Timer halten an und buchen); die bisherige Erledigt-Spalte wird offen">
          <i class="fa-regular fa-circle-check"></i>Zur Erledigt-Spalte machen</button>
      {/if}
      {#if loeschbar}
        <button class="knopf ohne klein gefahr" onclick={loeschenFragen}><i class="fa-solid fa-trash-can"></i>Löschen</button>
      {/if}
    </div>
  {/if}
</div>
