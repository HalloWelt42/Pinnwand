<script lang="ts">
  // Spalten: Reihenfolge per Ziehen am Griff (wie im Board), je Spalte Name, Farbe, Grenze oder Zeitfenster; genau eine
  // Erledigt-Spalte. Löschen fragt in der Fläche und sagt, wohin die Karten gehen: verschieben (derselbe Weg wie Ziehen:
  // Alter neu, Gruppe zieht mit, Grenze warnt) oder mit der Spalte in den Papierkorb (Wiederherstellen an der alten
  // Stelle, mit Zeiten). Die Erledigt-Spalte und die letzte Spalte bleiben. Alles über die Anwendungsfälle.
  import { untrack } from "svelte";
  import { dragHandle, dragHandleZone, type DndEvent } from "svelte-dnd-action";
  import { laufendAuf, zeitDerKarte } from "../../../beispiel/abfragen";
  import {
    spalteAendern, spalteAnlegen, spalteLoeschen, spaltenOrdnen, zurErledigtSpalte,
  } from "../../../beispiel/anwendung/boards.svelte";
  import { dauer } from "../../../beispiel/format";
  import { kartenDerSpalte, stand } from "../../../beispiel/stand.svelte";
  import { ZEITFENSTER, ZEITFENSTER_VORGABE } from "../../../anzeige";
  import type { Board, Farbe, Spalte, Zeitfenster } from "../../../modell";
  import Farbwahl from "../../../teile/Farbwahl.svelte";
  import { EINSTELLUNG_GRENZEN as GRENZEN } from "../../../regeln/board";
  import Zahlfeld from "../../../teile/Zahlfeld.svelte";

  let { board, entwurf = "" }: { board: Board; entwurf?: string } = $props();

  // Ziehen ordnet erst die Anzeige, das Ablegen ruft den Anwendungsfall (wie im Board)
  let items = $state<Spalte[]>([]);
  $effect(() => { items = [...board.spalten]; });
  function erwaegen(e: CustomEvent<DndEvent<Spalte>>): void { items = e.detail.items; }
  function abgelegt(e: CustomEvent<DndEvent<Spalte>>): void {
    items = e.detail.items;
    spaltenOrdnen(board.id, items.map((s) => s.id));
    items = [...board.spalten];
  }

  const anzahl = (n: number, eins: string, viele: string) => `${n} ${n === 1 ? eins : viele}`;

  function umbenennen(s: Spalte, e: Event): void {
    const feld = e.currentTarget as HTMLInputElement;
    if (!spalteAendern(board.id, s.id, { name: feld.value })) feld.value = s.name;
  }

  // Rückfrage beim Löschen: eine Ansichtssache, die Änderung kommt erst mit dem Knopf
  let loeschen = $state<string | null>(null);
  let weg = $state<"verschieben" | "papierkorb">("verschieben");
  let ziel = $state("");

  function fragen(id: string): void {
    const i = board.spalten.findIndex((s) => s.id === id);
    if (i < 0) return;
    loeschen = id;
    weg = "verschieben";
    ziel = (board.spalten.slice(0, i).reverse().find((s) => !s.erledigt) ?? board.spalten.find((s, j) => j > i && !s.erledigt))?.id ?? "";
  }
  // vorgeführter Zustand: die Rückfrage zu Geplant steht offen (einmal je Entwurf)
  $effect(() => {
    const e = entwurf;
    untrack(() => { if (e === "rueckfrage") fragen("s-geplant"); else loeschen = null; });
  });
  function bestaetigen(): void {
    if (loeschen && spalteLoeschen(board.id, loeschen, weg === "verschieben" ? ziel : undefined)) loeschen = null;
  }

  const fort = $derived(board.spalten.find((s) => s.id === loeschen));
  const betroffen = $derived(loeschen ? kartenDerSpalte(loeschen) : []);
  const zielSpalte = $derived(board.spalten.find((s) => s.id === ziel));
  const erste = $derived(board.spalten.find((s) => s.id !== loeschen));
  const gruppen = $derived(new Set(betroffen.map((k) => k.gruppe).filter(Boolean)));
  const mitgezogen = $derived(stand.karten.filter((k) => k.board === board.id && k.gruppe && gruppen.has(k.gruppe)
    && k.spalte !== loeschen && k.spalte !== ziel));
  const laufend = $derived(betroffen.filter((k) => laufendAuf(k.id).length));
  const zeit = $derived(betroffen.reduce((s, k) => s + zeitDerKarte(k.id), 0));
  const serien = $derived(stand.serien.filter((s) => s.board === board.id && s.zielspalte === loeschen));
  const danach = $derived(zielSpalte ? kartenDerSpalte(zielSpalte.id).length + betroffen.length + mitgezogen.length : 0);
  const ueberGrenze = $derived(zielSpalte?.grenze !== undefined && danach > zielSpalte.grenze);

  // neue Spalte: ans Ende, ohne Grenze, nicht erledigt
  let neuName = $state("");
  let neuFarbe = $state<Farbe>("himmel");
  function anlegen(): void {
    if (spalteAnlegen(board.id, neuName, neuFarbe)) neuName = "";
  }
</script>

<div class="rollfeld">
  <div class="pw-verwaltung-flaeche">
    <p class="pw-verwaltung-satz"><i class="fa-solid fa-circle-info"></i>Am Griff ziehen ordnet die Spalten wie im Board. Die Grenze warnt,
      sobald mehr offene Karten in der Spalte liegen; sie hält nichts auf.</p>

    <div class="pw-verwaltung-liste" use:dragHandleZone={{ items, flipDurationMs: 160, type: "spalte", dropTargetStyle: {} }}
         onconsider={erwaegen} onfinalize={abgelegt}>
      {#each items as s (s.id)}
        {@const n = kartenDerSpalte(s.id).length}
        <article class="pw-verwaltung-eintrag" class:gefahr={loeschen === s.id} data-farbe={s.farbe} aria-label="Spalte {s.name}">
          <div class="oben">
            <span class="pw-verwaltung-griff" use:dragHandle aria-label="Spalte {s.name} ziehen zum Umsortieren" title="Ziehen zum Umsortieren">
              <i class="fa-solid fa-grip-vertical"></i></span>
            <span class="pw-farbpunkt"></span>
            <input class="eingabe pw-verwaltung-name" value={s.name} aria-label="Name der Spalte" onchange={(e) => umbenennen(s, e)} />
            <span class="pw-angabe flaeche" title="Karten in dieser Spalte"><i class="fa-regular fa-note-sticky"></i>{anzahl(n, "Karte", "Karten")}</span>
            <button class="knopf ohne symbol klein" disabled={s.erledigt || board.spalten.length === 1 || loeschen === s.id} onclick={() => fragen(s.id)}
                    title={s.erledigt ? "Die Erledigt-Spalte bleibt; mach erst eine andere Spalte zur Erledigt-Spalte"
                      : board.spalten.length === 1 ? "Die letzte Spalte bleibt: ein Board braucht mindestens eine" : `Spalte ${s.name} löschen`}
                    aria-label="Spalte {s.name} löschen"><i class="fa-solid fa-trash-can"></i></button>
          </div>
          <div class="angaben">
            <span class="angabe"><span class="etikett">Farbe</span>
              <Farbwahl kompakt wert={s.farbe} waehlen={(f) => f && spalteAendern(board.id, s.id, { farbe: f })} wofuer="Farbe der Spalte {s.name}" /></span>
            {#if s.erledigt}
              <span class="angabe" title="Welche erledigten Karten das Board zuerst zeigt; im Board stellt jede Person es für sich um">
                <span class="etikett">Zeitfenster</span>
                <select class="eingabe" value={s.zeitfenster ?? ZEITFENSTER_VORGABE} aria-label="Zeitfenster der Spalte {s.name}"
                        onchange={(e) => spalteAendern(board.id, s.id, { zeitfenster: (e.currentTarget as HTMLSelectElement).value as Zeitfenster })}>
                  {#each Object.entries(ZEITFENSTER) as [w, t] (w)}<option value={w}>{t}</option>{/each}
                </select></span>
              <span class="angabe" title="Genau eine Erledigt-Spalte je Board: ihre Karten gelten als erledigt und laden nach Abschlussdatum">
                <span class="zustand fertig"><i class="fa-solid fa-circle-check"></i>Erledigt-Spalte</span></span>
            {:else}
              <span class="angabe"><span class="etikett">Grenze</span>
                <Zahlfeld wert={s.grenze} setzen={(g) => spalteAendern(board.id, s.id, { grenze: g ?? null })} min={GRENZEN.grenze[0]} max={GRENZEN.grenze[1]}
                          leer="keine" name="Grenze der Spalte {s.name}" einheit="offene Karten" /></span>
              <span class="angabe">
                <button class="knopf ohne klein" onclick={() => zurErledigtSpalte(board.id, s.id)}
                        title="Wird die Erledigt-Spalte: ihre Karten gelten als erledigt (Abschluss heute, laufende Timer halten an und buchen); die bisherige Erledigt-Spalte wird offen">
                  <i class="fa-regular fa-circle-check"></i>Zur Erledigt-Spalte machen</button></span>
            {/if}
          </div>

          {#if loeschen === s.id && fort}
            <div class="hinweis gefahr pw-verwaltung-rueckfrage" role="alert"><i class="fa-solid fa-trash-can"></i>
              <div>
                <b>Spalte {fort.name} löschen?</b>
                {#if betroffen.length}Sie hat {anzahl(betroffen.length, "Karte", "Karten")}. Wohin damit?{:else}Sie ist leer.{/if}
                {#if betroffen.length}
                  <div class="wahl pw-verwaltung-wahl">
                    <label class:an={weg === "verschieben"}>
                      <input type="radio" name="wohin-{s.id}" value="verschieben" bind:group={weg} /><span class="kreis"></span>
                      <div><b>Karten verschieben nach
                        <select class="eingabe" bind:value={ziel} aria-label="Zielspalte der Karten">
                          {#each board.spalten.filter((x) => x.id !== s.id) as x (x.id)}<option value={x.id}>{x.name}</option>{/each}
                        </select></b>
                        <span>Wie beim Ziehen: das Alter im Status beginnt neu, verknüpfte Karten ziehen mit.
                          {#if zielSpalte?.erledigt}Sie gelten dann als erledigt, laufende Timer halten an und buchen.{/if}
                          {#each mitgezogen as m (m.id)}{m.schluessel} zieht aus {board.spalten.find((x) => x.id === m.spalte)?.name} mit. {/each}</span>
                        {#if ueberGrenze && zielSpalte}
                          <span class="pw-verwaltung-warnung"><i class="fa-solid fa-triangle-exclamation"></i>{zielSpalte.name} hat danach {danach} offene
                            Karten bei Grenze {zielSpalte.grenze}; das ist nur eine Warnung.</span>
                        {/if}
                      </div>
                    </label>
                    <label class:an={weg === "papierkorb"}>
                      <input type="radio" name="wohin-{s.id}" value="papierkorb" bind:group={weg} /><span class="kreis"></span>
                      <div><b>Mit der Spalte in den Papierkorb</b>
                        <span>Samt {dauer(zeit)} Stunden gebuchter Zeit, Kommentaren und Anhängen. Wiederherstellen bringt die Spalte an ihre alte
                          Stelle zurück, mit allem.{laufend.length ? ` Laufende Timer (${laufend.map((k) => k.schluessel).join(", ")}) halten an und buchen.` : ""}</span>
                      </div>
                    </label>
                  </div>
                {/if}
                {#each serien as se (se.id)}
                  <p class="pw-verwaltung-folge"><i class="fa-solid fa-repeat"></i>Die Serie {se.titel} legt ihre Karten bisher hier an, künftig
                    in {weg === "verschieben" && zielSpalte ? zielSpalte.name : erste?.name}.</p>
                {/each}
              </div>
              <span class="rechts">
                <button class="knopf klein" onclick={() => (loeschen = null)}>Abbrechen</button>
                <button class="knopf gefahr-voll klein" onclick={bestaetigen}><i class="fa-solid fa-trash-can"></i>Spalte löschen</button>
              </span>
            </div>
          {/if}
        </article>
      {/each}
    </div>

    <section class="bereich">
      <h2 class="etikett">Neue Spalte</h2>
      <div class="pw-verwaltung-formular">
        <input class="eingabe" bind:value={neuName} placeholder="Name der Spalte" aria-label="Name der neuen Spalte"
               onkeydown={(e) => { if (e.key === "Enter") anlegen(); }} />
        <button class="knopf haupt" disabled={!neuName.trim()} onclick={anlegen}><i class="fa-solid fa-plus"></i>Spalte anlegen</button>
      </div>
      <div class="pw-verwaltung-formular">
        <span class="etikett">Farbe</span><Farbwahl wert={neuFarbe} waehlen={(f) => f && (neuFarbe = f)} wofuer="Farbe der neuen Spalte" />
      </div>
      <p class="pw-verwaltung-satz">Kommt ans Ende, ohne Grenze und offen; alles andere stellst du danach in ihrer Zeile ein.</p>
    </section>
  </div>
</div>
