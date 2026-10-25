<script lang="ts">
  // Spalten: Reihenfolge per Ziehen am Griff (wie im Board), je Spalte Name, Farbe, Grenze, Erledigt-Spalte und die
  // Vorgabe des Zeitfensters. Löschen fragt in der Fläche und sagt, wohin die Karten gehen: verschieben (derselbe Weg
  // wie Ziehen: Alter neu, Gruppe zieht mit, Grenze warnt) oder mit der Spalte in den Papierkorb (Wiederherstellen an
  // der alten Stelle, mit Zeiten). Serien, die hier Karten anlegen, bekommen die neue Zielspalte. Die letzte Spalte bleibt.
  import { untrack } from "svelte";
  import { dragHandle, dragHandleZone, type DndEvent } from "svelte-dnd-action";
  import { SERIEN } from "../../../beispiel/daten";
  import { dauer } from "../../../beispiel/format";
  import { ablegen, stand } from "../../../beispiel/stand.svelte";
  import type { Board, Farbe, Spalte, Zeitfenster } from "../../../modell";
  import { ZEITFENSTER } from "../daten";
  import Farbwahl from "../Farbwahl.svelte";
  import Zahlfeld from "../Zahlfeld.svelte";

  let { board, entwurf = "" }: { board: Board; entwurf?: string } = $props();

  let items = $state<Spalte[]>([]);
  $effect(() => { items = [...board.spalten]; });
  function erwaegen(e: CustomEvent<DndEvent<Spalte>>): void { items = e.detail.items; }
  function abgelegt(e: CustomEvent<DndEvent<Spalte>>): void {
    items = e.detail.items;
    board.spalten = items;
  }

  const kartenIn = (id: string) => stand.karten.filter((k) => k.spalte === id);
  const anzahl = (n: number, eins: string, viele: string) => `${n} ${n === 1 ? eins : viele}`;

  function umbenennen(s: Spalte, e: Event): void {
    const feld = e.currentTarget as HTMLInputElement;
    if (feld.value.trim()) s.name = feld.value.trim();
    else feld.value = s.name;
  }

  // Rückfrage beim Löschen
  let loeschen = $state<string | null>(null);
  let weg = $state<"verschieben" | "papierkorb">("verschieben");
  let ziel = $state("");

  function fragen(id: string): void {
    const i = board.spalten.findIndex((s) => s.id === id);
    if (i < 0) return;
    loeschen = id;
    weg = "verschieben";
    ziel = (board.spalten[i - 1] ?? board.spalten[i + 1])?.id ?? "";
  }
  $effect(() => {
    const e = entwurf;
    untrack(() => { if (e === "rueckfrage") fragen("s-geplant"); else loeschen = null; });
  });

  const fort = $derived(board.spalten.find((s) => s.id === loeschen));
  const betroffen = $derived(loeschen ? kartenIn(loeschen) : []);
  const zielSpalte = $derived(board.spalten.find((s) => s.id === ziel));
  const erste = $derived(board.spalten.find((s) => s.id !== loeschen));
  const gruppen = $derived(new Set(betroffen.map((k) => k.gruppe).filter(Boolean)));
  const mitgezogen = $derived(stand.karten.filter((k) => k.board === board.id && k.gruppe && gruppen.has(k.gruppe)
    && k.spalte !== loeschen && k.spalte !== ziel));
  const laufend = $derived(betroffen.filter((k) => k.laeuft));
  const zeit = $derived(betroffen.reduce((s, k) => s + k.erfasstSek, 0));
  const serien = $derived(SERIEN.filter((s) => s.board === board.id && s.zielspalte === loeschen));
  const danach = $derived(zielSpalte && !zielSpalte.erledigt ? kartenIn(zielSpalte.id).length + betroffen.length + mitgezogen.length : 0);
  const ueberGrenze = $derived(zielSpalte?.grenze !== undefined && danach > zielSpalte.grenze);

  /** Verschieben geht denselben Weg wie das Ziehen im Board (Alter neu, Gruppe zieht mit, Erledigt bucht Timer);
   *  sonst gehen die Karten mit der Spalte in den Papierkorb */
  function spalteLoeschen(): void {
    if (!loeschen) return;
    if (betroffen.length && weg === "verschieben" && zielSpalte) {
      ablegen(zielSpalte.id, [...(stand.reihen[zielSpalte.id] ?? []), ...betroffen.map((k) => k.id)], zielSpalte.erledigt);
    } else {
      const id = loeschen;
      stand.karten = stand.karten.filter((k) => k.spalte !== id);
    }
    board.spalten = board.spalten.filter((s) => s.id !== loeschen);
    loeschen = null;
  }

  // neue Spalte: ans Ende, ohne Grenze, nicht erledigt
  let neuName = $state("");
  let neuFarbe = $state<Farbe>("himmel");
  function anlegen(): void {
    const name = neuName.trim();
    if (!name) return;
    board.spalten.push({ id: `s-${crypto.randomUUID()}`, name, farbe: neuFarbe, erledigt: false });
    neuName = "";
  }
</script>

<div class="rollfeld">
  <div class="pw-verwaltung-flaeche">
    <p class="pw-verwaltung-satz"><i class="fa-solid fa-circle-info"></i>Am Griff ziehen ordnet die Spalten wie im Board. Die Grenze warnt,
      sobald mehr offene Karten in der Spalte liegen; sie hält nichts auf.</p>

    <div class="pw-verwaltung-liste" use:dragHandleZone={{ items, flipDurationMs: 160, type: "spalte", dropTargetStyle: {} }}
         onconsider={erwaegen} onfinalize={abgelegt}>
      {#each items as s (s.id)}
        {@const n = kartenIn(s.id).length}
        <article class="pw-verwaltung-eintrag" class:gefahr={loeschen === s.id} data-farbe={s.farbe} aria-label="Spalte {s.name}">
          <div class="oben">
            <span class="pw-verwaltung-griff" use:dragHandle aria-label="Spalte {s.name} ziehen zum Umsortieren" title="Ziehen zum Umsortieren">
              <i class="fa-solid fa-grip-vertical"></i></span>
            <span class="pw-farbpunkt"></span>
            <input class="eingabe pw-verwaltung-name" value={s.name} aria-label="Name der Spalte" onchange={(e) => umbenennen(s, e)} />
            <span class="pw-angabe flaeche" title="Karten in dieser Spalte"><i class="fa-regular fa-note-sticky"></i>{anzahl(n, "Karte", "Karten")}</span>
            <button class="knopf ohne symbol klein" disabled={board.spalten.length === 1 || loeschen === s.id} onclick={() => fragen(s.id)}
                    title={board.spalten.length === 1 ? "Die letzte Spalte bleibt: ein Board braucht mindestens eine" : `Spalte ${s.name} löschen`}
                    aria-label="Spalte {s.name} löschen"><i class="fa-solid fa-trash-can"></i></button>
          </div>
          <div class="angaben">
            <span class="angabe"><span class="etikett">Farbe</span>
              <Farbwahl kompakt wert={s.farbe} waehlen={(f) => (s.farbe = f)} wofuer="Farbe der Spalte {s.name}" /></span>
            {#if s.erledigt}
              <span class="angabe" title="Welche erledigten Karten das Board zuerst zeigt; im Board stellt jede Person es für sich um">
                <span class="etikett">Zeitfenster</span>
                <select class="eingabe" value={s.zeitfenster ?? "heute"} aria-label="Zeitfenster der Spalte {s.name}"
                        onchange={(e) => (s.zeitfenster = (e.currentTarget as HTMLSelectElement).value as Zeitfenster)}>
                  {#each Object.entries(ZEITFENSTER) as [w, t] (w)}<option value={w}>{t}</option>{/each}
                </select></span>
            {:else}
              <span class="angabe"><span class="etikett">Grenze</span>
                <Zahlfeld wert={s.grenze} setzen={(g) => (s.grenze = g)} min={1} max={999} leer="keine" name="Grenze der Spalte {s.name}" einheit="offene Karten" /></span>
            {/if}
            <span class="angabe" title={s.erledigt ? "Ausschalten: die Karten sind wieder offen, ihr Alter beginnt neu"
                                                   : "Einschalten: die Karten gelten als erledigt (Abschluss heute), laufende Timer halten an und buchen; das Board lädt sie nach Abschlussdatum"}>
              <span class="etikett">Erledigt-Spalte</span>
              <button class="schalter" class:an={s.erledigt} aria-pressed={s.erledigt} aria-label="Erledigt-Spalte {s.name}"
                      onclick={() => (s.erledigt = !s.erledigt)}></button>{s.erledigt ? "ja" : "nein"}</span>
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
                        <span>Samt {dauer(zeit)} Stunden erfasster Zeit, Kommentaren und Anhängen. Wiederherstellen bringt die Spalte an ihre alte
                          Stelle zurück, mit allem.{#if laufend.length} Laufende Timer ({laufend.map((k) => k.schluessel).join(", ")}) halten an und buchen.{/if}</span>
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
                <button class="knopf gefahr-voll klein" onclick={spalteLoeschen}><i class="fa-solid fa-trash-can"></i>Spalte löschen</button>
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
        <span class="etikett">Farbe</span><Farbwahl wert={neuFarbe} waehlen={(f) => (neuFarbe = f)} wofuer="Farbe der neuen Spalte" />
      </div>
      <p class="pw-verwaltung-satz">Kommt ans Ende, ohne Grenze und nicht erledigt; alles andere stellst du danach in ihrer Zeile ein.</p>
    </section>
  </div>
</div>
