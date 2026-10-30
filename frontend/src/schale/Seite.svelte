<script lang="ts">
  // Seitenleiste: die Bereiche über alle Boards (Heute, Hinweise; Zeiten, Arbeitszeit, Serien und Berichte nur, wenn eines
  // deiner Boards das Modul eingeschaltet hat), darunter deine Boards nach deinen Ordnern (Ordner ordnen nur, sie tragen
  // keine Rechte), Boards ohne Ordner zuletzt unter "Ohne Ordner". Boards ziehen in einen Ordner, aus ihm heraus und
  // innerhalb um; Ordner werden hier umbenannt, gelöscht und angelegt. Unten Hilfe, Einstellungen und das Ein- und
  // Ausklappen (gemerkt auf diesem Gerät, Baustein seitenleiste des Appkerns).
  import { hilfe, Hilfepunkt, seitenleiste, seitenleisteUmschalten } from "appkern-oberflaeche";
  import { dndzone, TRIGGERS, type DndEvent } from "svelte-dnd-action";
  import { boardGruppen, modulIrgendwo, ungelesen } from "../daten/abfragen";
  import { ordnerAnlegen, ordnerLoeschen, ordnerSetzen, ordnerUmbenennen } from "../daten/anwendung/boards.svelte";
  import type { Board, ModulKennung, Ordner } from "../modell";
  import { boardPfad } from "../weg.svelte";
  import { enter } from "../teile/taste";

  let { aktiv }: { aktiv: string } = $props();
  const NAVI: [string, string, string, string, ModulKennung | null][] = [
    ["heute", "Heute", "fa-calendar-day", "Deine Karten aus allen Boards", null],
    ["hinweise", "Hinweise", "fa-bell", "Zugewiesen, fällig, erwähnt, kommentiert, verschoben", null],
    ["zeiten", "Zeiten", "fa-clock", "Dein Stundenzettel der Woche", "zeiterfassung"],
    ["arbeitszeit", "Arbeitszeit", "fa-calendar-check", "Zeitkonto, Urlaub und Jahreskalender", "arbeitszeit"],
    ["serien", "Serien und Termine", "fa-repeat", "Wiederkehrende Karten und Termine aller Boards", "serien"],
    ["berichte", "Berichte", "fa-file-lines", "Auswertungen als PDF, Tabelle oder Text", "berichte"],
  ];
  /** Hat eines deiner Boards das Modul an (und bietet diese Fassung es an)? */
  const bereiche = $derived(NAVI.filter(([, , , , modul]) => modul === null || modulIrgendwo(modul)));
  const gruppen = $derived(boardGruppen());
  const ordner = $derived(gruppen.flatMap((g) => (g.ordner ? [g.ordner] : [])));
  const zahl = $derived(ungelesen());

  // Ziehen: je Ordner eine Zone (Schlüssel die Kennung, "" für ohne Ordner). Während des Ziehens zeigt sie, was die Hand
  // gerade ordnet; das Ablegen ruft den Anwendungsfall, danach gilt wieder der Stand des Servers.
  let zonen = $state<Record<string, Board[]>>({});
  let ziehen = $state(false);
  $effect(() => {
    const neu = Object.fromEntries(gruppen.map((g) => [g.ordner?.id ?? "", g.boards]));
    if (!ziehen) zonen = { "": [], ...neu };
  });
  function erwaegen(schluessel: string, e: CustomEvent<DndEvent<Board>>): void {
    zonen[schluessel] = e.detail.items;
    if (e.detail.info.trigger === TRIGGERS.DRAG_STARTED) ziehen = true;
  }
  async function abgelegt(schluessel: string, e: CustomEvent<DndEvent<Board>>): Promise<void> {
    zonen[schluessel] = e.detail.items;
    const { id, trigger } = e.detail.info;
    if (trigger === TRIGGERS.DROPPED_INTO_ANOTHER) return;           // die Zone, in die es fiel, ruft den Anwendungsfall
    if (trigger === TRIGGERS.DROPPED_INTO_ZONE) await ordnerSetzen(id, schluessel, e.detail.items.findIndex((b) => b.id === id));
    ziehen = false;
  }
  const zone = (schluessel: string) => ({
    items: zonen[schluessel] ?? [], type: "board", flipDurationMs: 150, dropTargetStyle: {}, dragDisabled: bearbeiten !== null,
  });

  // Ordner bearbeiten: Name im Feld (Enter oder Verlassen übernimmt, Escape verwirft). Löschen am Papierkorb daneben:
  // ein leerer Ordner geht sofort (Rückgängig in der Meldung), einer mit Boards erst nach der Rückfrage
  let bearbeiten = $state<string | null>(null);
  let loeschen = $state<string | null>(null);
  async function umbenennen(o: Ordner, feld: HTMLInputElement): Promise<void> {
    if (bearbeiten !== o.id) return;
    bearbeiten = null;
    if (feld.value.trim() && feld.value.trim() !== o.name) await ordnerUmbenennen(o.id, feld.value);
  }
  function nameTaste(o: Ordner, e: KeyboardEvent): void {
    if (enter(e)) void umbenennen(o, e.currentTarget as HTMLInputElement);
    if (e.key === "Escape") bearbeiten = null;
  }
  async function loeschenBestaetigen(o: Ordner): Promise<void> {
    if (await ordnerLoeschen(o.id)) loeschen = null;
  }
  function loeschenKlick(o: Ordner): void {
    if (zonen[o.id]?.length) loeschen = loeschen === o.id ? null : o.id;
    else void ordnerLoeschen(o.id);
  }
  const fokus = (feld: HTMLInputElement) => { feld.focus(); feld.select(); };

  let neuOffen = $state(false);
  let neuName = $state("");
  async function anlegen(): Promise<void> {
    if (!neuName.trim() || (await ordnerAnlegen(neuName))) {
      neuName = "";
      neuOffen = false;
    }
  }
  function neuTaste(e: KeyboardEvent): void {
    if (enter(e)) void anlegen();
    if (e.key === "Escape") neuOffen = false;
  }
</script>

{#snippet boardsIn(schluessel: string)}
  <div class="pw-ordnerzone" class:leer={!zonen[schluessel]?.length} use:dndzone={zone(schluessel)}
       onconsider={(e) => erwaegen(schluessel, e)} onfinalize={(e) => abgelegt(schluessel, e)}>
    {#each zonen[schluessel] ?? [] as b (b.id)}
      <a class="navi pw-boardnavi" class:aktiv={aktiv === b.id} href={boardPfad(b.kuerzel)} title="Board {b.name}; ziehen ordnet es in einen Ordner">
        <span class="pw-farbpunkt" data-farbe={b.farbe}></span><span class="pw-boardkuerzel" data-farbe={b.farbe}>{b.kuerzel}</span>{b.name}</a>
    {/each}
  </div>
{/snippet}

{#each bereiche as [id, name, symbol, titel] (id)}
  <a class="navi" class:aktiv={aktiv === id} href="/{id}" title={titel}><i class="fa-solid {symbol}"></i>{name}
    {#if id === "hinweise" && zahl}<span class="zaehler pille gefahr">{zahl}</span>{/if}</a>
{/each}
<div class="etikett pw-boards-etikett">Boards<Hilfepunkt thema="uebersicht" abschnitt="ordner" titel="Hilfe zu Ordnern und Boards" /></div>
{#each ordner as o (o.id)}
  <div class="pw-ordner" class:bearbeiten={bearbeiten === o.id}>
    <i class="fa-solid fa-folder"></i>
    {#if bearbeiten === o.id}
      <input class="eingabe pw-ordner-feld" value={o.name} aria-label="Name des Ordners {o.name}" use:fokus
             onkeydown={(e) => nameTaste(o, e)} onblur={(e) => umbenennen(o, e.currentTarget)} />
    {:else}
      {@const leer = !zonen[o.id]?.length}
      <span class="pw-ordner-name">{o.name}</span>
      <button class="pw-ordner-knopf" title="Ordner {o.name} umbenennen" aria-label="Ordner {o.name} umbenennen"
              onclick={() => { loeschen = null; bearbeiten = o.id; }}><i class="fa-solid fa-pen"></i></button>
      <button class="pw-ordner-knopf" title={leer ? `Leeren Ordner ${o.name} löschen (Rückgängig möglich)` : `Ordner ${o.name} löschen; seine Boards bleiben`}
              aria-label="Ordner {o.name} löschen" onclick={() => loeschenKlick(o)}><i class="fa-solid fa-trash-can"></i></button>
    {/if}
  </div>
  {#if loeschen === o.id}
    <div class="pw-ordner-rueckfrage" role="alert">
      <span><b>Ordner {o.name} löschen?</b> Seine Boards stehen danach ohne Ordner; an ihnen ändert sich nichts.</span>
      <span class="knoepfe"><button class="knopf klein" onclick={() => (loeschen = null)}>Abbrechen</button>
        <button class="knopf klein gefahr-voll" onclick={() => loeschenBestaetigen(o)}><i class="fa-solid fa-trash-can"></i>Löschen</button></span>
    </div>
  {/if}
  {@render boardsIn(o.id)}
{/each}
{#if zonen[""]?.length || ziehen}
  <div class="pw-ordner"><i class="fa-regular fa-folder"></i><span class="pw-ordner-name">Ohne Ordner</span></div>
  {@render boardsIn("")}
{/if}
<a class="navi" class:aktiv={aktiv === "board-neu"} href="/boards/neu"><i class="fa-solid fa-plus"></i>Board anlegen</a>
{#if neuOffen}
  <div class="pw-ordner-neu">
    <input class="eingabe" bind:value={neuName} placeholder="Name des Ordners" aria-label="Name des neuen Ordners" use:fokus
           onkeydown={neuTaste} onblur={() => { if (!neuName.trim()) neuOffen = false; }} />
    <button class="knopf klein haupt" disabled={!neuName.trim()} onpointerdown={(e) => e.preventDefault()} onclick={anlegen}>Anlegen</button>
  </div>
{:else}
  <button class="navi" title="Neuer Ordner für die Seitenleiste; Boards zieht man danach hinein" onclick={() => (neuOffen = true)}>
    <i class="fa-solid fa-folder-plus"></i>Ordner anlegen</button>
{/if}
<div class="pw-seite-fuss">
  <button class="navi" class:aktiv={hilfe.offen} title="Hilfe zur Pinnwand: schwebendes Fenster, durchsuchbar" onclick={() => hilfe.umschalten()}>
    <i class="fa-solid fa-circle-question"></i>Hilfe</button>
  <a class="navi" class:aktiv={aktiv === "einstellungen"} href="/einstellungen"><i class="fa-solid fa-gear"></i>Einstellungen</a>
  <button class="navi" title={seitenleiste.schmal ? "Seitenleiste ausklappen (merkt sich dieses Gerät)" : "Seitenleiste einklappen (merkt sich dieses Gerät)"}
          onclick={seitenleisteUmschalten}>
    <i class="fa-solid {seitenleiste.schmal ? 'fa-angles-right' : 'fa-angles-left'}"></i>{seitenleiste.schmal ? "Ausklappen" : "Einklappen"}</button>
</div>
