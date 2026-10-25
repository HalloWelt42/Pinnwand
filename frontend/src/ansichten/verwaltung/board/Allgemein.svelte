<script lang="ts">
  // Allgemein: Name, festes Kürzel, Ordner (persönlich), Farbe; Alterung und Erledigt-Grenzen (bisher global, jetzt je
  // Board); als Vorlage speichern; das Board in den Papierkorb (Rückfrage in der Fläche). Alles über die Anwendungsfälle.
  import { laufendAuf } from "../../../daten/abfragen";
  import { alsVorlageSpeichern, boardFarbeSetzen, boardUmbenennen, einstellungenSetzen, ordnerSetzen } from "../../../daten/anwendung/boards.svelte";
  import { boardInPapierkorb } from "../../../daten/anwendung/papierkorb.svelte";
  import { laufnummer, ordnerVon, stand } from "../../../daten/stand.svelte";
  import type { Board, BoardEinstellungen } from "../../../modell";
  import { alterung } from "../../../regeln/board";
  import Farbwahl from "../../../teile/Farbwahl.svelte";
  import { gehe } from "../../../weg.svelte";
  import { EINSTELLUNG_GRENZEN as GRENZEN } from "../../../regeln/board";
  import Zahlfeld from "../../../teile/Zahlfeld.svelte";

  let { board }: { board: Board; entwurf?: string } = $props();

  const e = $derived(board.einstellungen);
  const karten = $derived(stand.karten.filter((k) => k.board === board.id));
  const laufend = $derived(karten.filter((k) => laufendAuf(k.id).length));
  const serien = $derived(stand.serien.filter((s) => s.board === board.id));
  let vorlageOffen = $state(false);
  let vorlageName = $state("");
  let papierkorb = $state(false);

  function umbenennen(ev: Event): void {
    const feld = ev.currentTarget as HTMLInputElement;
    if (!boardUmbenennen(board.id, feld.value)) feld.value = board.name;
  }
  function setzen(teil: Partial<BoardEinstellungen>): void {
    einstellungenSetzen(board.id, teil);
  }
  async function wegwerfen(): Promise<void> {
    if (await boardInPapierkorb(board.id)) gehe("/heute");
  }

  /** Beispiele der Sanduhr mit den eingestellten Stufen (Regel des Boards) */
  const beispiele = $derived([...new Set([1, e.alterungWarnung, e.alterungGefahr].filter((t) => t > 0))].sort((a, b) => a - b));
  const anzahl = (n: number, eins: string, viele: string) => `${n} ${n === 1 ? eins : viele}`;
</script>

<div class="rollfeld">
  <div class="pw-verwaltung-flaeche">
    <section class="bereich">
      <h2 class="etikett">Board</h2>
      <div class="einstellung">
        <div><div class="name">Name</div><div class="erklaerung">Steht in der Seitenleiste und im Kopf. Umbenennen ändert das Kürzel nicht.</div></div>
        <div class="wert"><input class="eingabe pw-verwaltung-text" value={board.name} aria-label="Name des Boards" onchange={umbenennen} /></div>
      </div>
      <div class="einstellung">
        <div><div class="name">Kürzel <i class="fa-solid fa-lock schwach" title="Fest seit dem Anlegen"></i></div>
          <div class="erklaerung">Fest seit dem Anlegen und über alle Boards eindeutig, damit Kartenschlüssel und Adressen nie brechen.
            Nummern werden nie wiederverwendet, auch nicht nach dem Löschen.</div></div>
        <div class="wert pw-verwaltung-wert-spalte">
          <span class="pw-verwaltung-kuerzel">{board.kuerzel}</span>
          <span class="pw-schluessel">nächste Karte {board.kuerzel}-{laufnummer(board.id) + 1}</span>
        </div>
      </div>
      <div class="einstellung">
        <div><div class="name">Ordner</div><div class="erklaerung">Ordnet nur deine Seitenleiste; ein Ordner trägt keine Rechte.</div></div>
        <div class="wert">
          <select class="eingabe" value={ordnerVon(board.id)?.id ?? ""} aria-label="Ordner"
                  onchange={(ev) => ordnerSetzen(board.id, (ev.currentTarget as HTMLSelectElement).value)}>
            {#each stand.ordner as o (o.id)}<option value={o.id}>{o.name}</option>{/each}
            <option value="">Ohne Ordner</option>
          </select>
        </div>
      </div>
      <div class="einstellung">
        <div><div class="name">Farbe</div><div class="erklaerung">Punkt in der Seitenleiste und im Kopf; unterscheidet die Boards.</div></div>
        <div class="wert"><Farbwahl wert={board.farbe} waehlen={(f) => f && boardFarbeSetzen(board.id, f)} wofuer="Farbe des Boards" /></div>
      </div>
    </section>

    <section class="bereich">
      <h2 class="etikett">Alterung der Karten</h2>
      <div class="einstellung">
        <div><div class="name"><i class="fa-solid fa-hourglass-half"></i>Warnung ab</div>
          <div class="erklaerung">Tage seit dem letzten Spaltenwechsel, auf der Karte als Sanduhr; gilt auch für "Im Status" im Kartendetail
            und für "Liegengeblieben" in Heute. 0 schaltet die Stufe aus.</div></div>
        <div class="wert"><Zahlfeld wert={e.alterungWarnung} setzen={(n) => setzen({ alterungWarnung: n ?? 0 })} min={GRENZEN.alterung[0]}
                                    max={GRENZEN.alterung[1]} name="Warnung ab Tagen" einheit="Tagen" /></div>
      </div>
      <div class="einstellung">
        <div><div class="name"><i class="fa-solid fa-hourglass-end"></i>Gefahr ab</div>
          <div class="erklaerung">Unabhängig von der Warnung: 0 schaltet nur diese Stufe aus.</div></div>
        <div class="wert"><Zahlfeld wert={e.alterungGefahr} setzen={(n) => setzen({ alterungGefahr: n ?? 0 })} min={GRENZEN.alterung[0]}
                                    max={GRENZEN.alterung[1]} name="Gefahr ab Tagen" einheit="Tagen" /></div>
      </div>
      <div class="einstellung">
        <div><div class="name">So sieht es aus</div>
          {#if e.alterungWarnung > 0 && e.alterungGefahr > 0 && e.alterungGefahr <= e.alterungWarnung}
            <div class="erklaerung pw-verwaltung-warnung">Gefahr kommt hier vor der Warnung; die Karte zeigt dann gleich Gefahr.</div>
          {/if}</div>
        <div class="wert">
          {#each beispiele as t (t)}
            <span class="pw-angabe {alterung(t, e)}" title="Liegt {t} {t === 1 ? 'Tag' : 'Tage'} in dieser Spalte"><i class="fa-solid fa-hourglass-half"></i>{t}</span>
          {:else}
            <span class="schwach klein">Alterung aus</span>
          {/each}
        </div>
      </div>
    </section>

    <section class="bereich">
      <h2 class="etikett">Erledigte Karten</h2>
      <div class="einstellung">
        <div><div class="name">Karten je Ladeschritt</div>
          <div class="erklaerung">Die Erledigt-Spalte lädt so viele Karten auf einmal, beim Rollen die nächsten.</div></div>
        <div class="wert"><Zahlfeld wert={e.ladeschritt} setzen={(n) => n !== undefined && setzen({ ladeschritt: n })} min={GRENZEN.ladeschritt[0]}
                                    max={GRENZEN.ladeschritt[1]} name="Karten je Ladeschritt" einheit="Karten" /></div>
      </div>
      <div class="einstellung">
        <div><div class="name">Archiv ab</div>
          <div class="erklaerung">Erledigte Karten mit älterem Abschluss stehen nur im Archiv. Eine reine Ladegrenze: eine größere Zahl holt
            sie zurück, Berichte zählen alle.</div></div>
        <div class="wert"><Zahlfeld wert={e.archivTage} setzen={(n) => n !== undefined && setzen({ archivTage: n })} min={GRENZEN.archivTage[0]}
                                    max={GRENZEN.archivTage[1]} name="Archiv ab Tagen" einheit="Tagen" /></div>
      </div>
    </section>

    <section class="bereich">
      <h2 class="etikett">Vorlage</h2>
      <div class="einstellung">
        <div><div class="name">Als Vorlage speichern</div>
          <div class="erklaerung">Aufbau ohne Karten und Mitglieder: {anzahl(board.spalten.length, "Spalte", "Spalten")},
            {anzahl(board.felder.length, "Feld", "Felder")}, {anzahl(board.labels.length, "Label", "Labels")} und die Module.</div></div>
        <div class="wert">
          <button class="knopf" disabled={vorlageOffen} onclick={() => { vorlageOffen = true; vorlageName = board.name; }}>
            <i class="fa-solid fa-copy"></i>Als Vorlage speichern</button>
        </div>
      </div>
      {#if vorlageOffen}
        <div class="pw-verwaltung-formular">
          <input class="eingabe" bind:value={vorlageName} aria-label="Name der Vorlage" placeholder="Name der Vorlage"
                 onkeydown={(ev) => { if (ev.key === "Enter" && alsVorlageSpeichern(board.id, vorlageName)) vorlageOffen = false; }} />
          <button class="knopf ohne" onclick={() => (vorlageOffen = false)}>Abbrechen</button>
          <button class="knopf" disabled={!vorlageName.trim()} onclick={() => { if (alsVorlageSpeichern(board.id, vorlageName)) vorlageOffen = false; }}>
            <i class="fa-solid fa-check"></i>Vorlage speichern</button>
        </div>
      {/if}
    </section>

    <section class="bereich">
      <h2 class="etikett">Board entfernen</h2>
      <div class="einstellung">
        <div><div class="name">In den Papierkorb</div>
          <div class="erklaerung">Mit allen Karten, Zeiten, Kommentaren und Anhängen; wiederherstellen unter Einstellungen, Papierkorb.</div></div>
        <div class="wert"><button class="knopf gefahr" disabled={papierkorb} onclick={() => (papierkorb = true)}><i class="fa-solid fa-trash-can"></i>In den Papierkorb</button></div>
      </div>
      {#if papierkorb}
        <div class="hinweis gefahr" role="alert"><i class="fa-solid fa-trash-can"></i>
          <div><b>{board.name} in den Papierkorb legen?</b> {anzahl(karten.length, "Karte geht", "Karten gehen")} mit, samt Zeiten,
            Kommentaren und Anhängen; das Board liegt dann im Papierkorb der Einstellungen und lässt sich dort wiederherstellen.
            {#if board.mitglieder.length > 1}Die {anzahl(board.mitglieder.length - 1, "andere Person sieht", "anderen Mitglieder sehen")} es
              bis dahin nicht mehr.{/if}
            {#if laufend.length}Laufende Timer ({laufend.map((k) => k.schluessel).join(", ")}) halten an und buchen.{/if}
            {#if serien.length}{anzahl(serien.length, "Serie ruht", "Serien ruhen")} so lange.{/if}</div>
          <span class="rechts"><button class="knopf klein" onclick={() => (papierkorb = false)}>Abbrechen</button>
            <button class="knopf gefahr-voll klein" onclick={wegwerfen}><i class="fa-solid fa-trash-can"></i>In den Papierkorb</button></span>
        </div>
      {/if}
    </section>
  </div>
</div>
