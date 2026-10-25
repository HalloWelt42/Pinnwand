<script lang="ts">
  // Schnell erfassen am Telefon: Board wählen (das zuletzt genutzte ist vorbelegt), Titel, Arbeit oder Idee, Fällig;
  // Anlegen legt die Karte ans Ende der ersten offenen Spalte (oder der Spalte, aus der man kam), du bist zuständig, und
  // das Formular bleibt für die nächste Karte offen (M-32, M-33). Sprechen nimmt über die App Transkription auf.
  import { kartenNummer } from "../../beispiel/abfragen";
  import { anlegen } from "../../beispiel/anwendung/karten.svelte";
  import { HEUTE } from "../../beispiel/daten";
  import { datum } from "../../beispiel/format";
  import { board, karte, stand } from "../../beispiel/stand.svelte";
  import { plusTage, wochentag } from "../../regeln/tage";
  import DatumFeld from "../../teile/DatumFeld.svelte";
  import { boardPfad, wert } from "../../weg.svelte";
  import { ZULETZT_BOARD } from "./daten";
  import Spracheingabe from "./Spracheingabe.svelte";
  import TelefonSchale from "./TelefonSchale.svelte";
  import { telPfad } from "./weg";

  let { entwurf = "" }: { entwurf?: string } = $props();

  const boards = $derived(stand.ordner.flatMap((o) => o.boards));
  const artVon = (id: string): "arbeit" | "idee" => (board(id).module.zeiterfassung ? "arbeit" : "idee");
  const vorgabe = stand.boards.find((x) => x.kuerzel.toLowerCase() === wert("board"))?.id ?? ZULETZT_BOARD;

  let boardId = $state(vorgabe);
  let spalteWunsch = $state(wert("spalte"));
  let titel = $state("");
  let beschreibung = $state("");
  let art = $state(artVon(vorgabe));
  /** Fälligkeit als ISO-Tag, leer: ohne */
  let faellig = $state("");
  let ausSprache = $state(false);
  /** die zuletzt hier angelegte Karte (verschwindet, wenn Rückgängig sie wieder entfernt) */
  let angelegtId = $state("");
  const angelegt = $derived(angelegtId ? karte(angelegtId) : undefined);
  let sprache = $state(false);
  $effect(() => { sprache = entwurf === "sprache"; });

  const b = $derived(board(boardId));
  /** wohin die Karte kommt: die Spalte, aus der man kam, sonst die erste offene (wie anlegen) */
  const spalte = $derived(b.spalten.find((s) => s.id === spalteWunsch) ?? b.spalten.find((s) => !s.erledigt) ?? b.spalten[0]);
  const freitag = plusTage(HEUTE, ((5 - wochentag(HEUTE) + 6) % 7) + 1);
  const FAELLIG: [string, string][] = [["Heute", HEUTE], ["Morgen", plusTage(HEUTE, 1)], [datum(freitag, true), freitag]];

  function boardWaehlen(id: string): void {
    boardId = id;
    spalteWunsch = "";
    art = artVon(id);
  }

  function anlegenKlick(): void {
    const k = anlegen(boardId, spalte.id, { titel, art, faellig: faellig || undefined, beschreibung });
    if (!k) return;
    angelegtId = k.id;
    titel = "";
    beschreibung = "";
    faellig = "";
    ausSprache = false;
  }

  function uebernehmen(text: string): void {
    titel = (text.match(/^[^.!?]+/)?.[0] ?? text).trim();
    beschreibung = text;
    ausSprache = true;
    sprache = false;
  }
</script>

{#snippet knoepfe()}
  <div class="pw-tel-aktionen">
    <button class="knopf" onclick={() => (sprache = true)} title="Per Sprache erfassen (Transkription)"><i class="fa-solid fa-microphone"></i>Sprechen</button>
    <button class="knopf haupt" disabled={!titel.trim()} onclick={anlegenKlick}><i class="fa-solid fa-plus"></i>Anlegen</button>
  </div>
{/snippet}

<TelefonSchale titel="Erfassen" unter={sprache ? "Per Sprache" : "Neue Karte"} reiter="erfassen" unten={sprache ? undefined : knoepfe}>
  {#if sprache}
    <Spracheingabe vorfuehren={entwurf === "sprache"} {uebernehmen} verwerfen={() => (sprache = false)} />
  {:else}
    {#if angelegt}
      <a class="pw-tel-zuletzt" href={telPfad(boardPfad(board(angelegt.board).kuerzel, kartenNummer(angelegt)))}>
        <i class="fa-solid fa-circle-check"></i><span>Zuletzt angelegt: <span class="pw-schluessel">{angelegt.schluessel}</span> {angelegt.titel}</span>
        <i class="fa-solid fa-chevron-right"></i></a>
    {/if}
    {#if ausSprache}
      <div class="hinweis"><i class="fa-solid fa-wave-square"></i><div>Aus der Sprache übernommen; Titel und Beschreibung bitte prüfen.</div></div>
    {/if}

    <section class="pw-tel-abschnitt" aria-label="Board">
      <div class="etikett">Board</div>
      <div class="pw-tel-wahl">
        {#each boards as id (id)}
          {@const x = board(id)}
          <button class:an={id === boardId} aria-pressed={id === boardId} data-farbe={x.farbe} onclick={() => boardWaehlen(id)}>
            <span class="pw-farbpunkt"></span>{x.name}{#if id === boardId}<i class="fa-solid fa-check"></i>{/if}</button>
        {/each}
      </div>
      <span class="pw-tel-notiz">Landet in {spalte.name} · zuständig du{boardId === ZULETZT_BOARD ? " · zuletzt genutzt" : ""}</span>
    </section>

    <label class="pw-tel-abschnitt">
      <span class="etikett">Titel</span>
      <textarea class="eingabe" rows="2" bind:value={titel} placeholder="Was ist zu tun?"></textarea>
    </label>
    {#if beschreibung || ausSprache}
      <label class="pw-tel-abschnitt">
        <span class="etikett">Beschreibung</span>
        <textarea class="eingabe" rows="4" bind:value={beschreibung}></textarea>
      </label>
    {/if}

    <section class="pw-tel-abschnitt" aria-label="Art">
      <div class="etikett">Art</div>
      <div class="pw-tel-umschalter" title="Arbeit hat Zeiterfassung, eine Idee nicht">
        <button class:an={art === "arbeit"} aria-pressed={art === "arbeit"} onclick={() => (art = "arbeit")}><i class="fa-solid fa-briefcase"></i>Arbeit</button>
        <button class="idee" class:an={art === "idee"} aria-pressed={art === "idee"} onclick={() => (art = "idee")}><i class="fa-solid fa-lightbulb"></i>Idee</button>
      </div>
    </section>

    <section class="pw-tel-abschnitt" aria-label="Fällig">
      <div class="etikett">Fällig</div>
      <DatumFeld tag={faellig} ontag={(t) => (faellig = t)} leerErlaubt titel="Fällig wie 30.10.2026 oder 30.10.; leer: ohne" />
      <div class="pw-tel-chips">
        {#each FAELLIG as [name, iso] (iso)}
          <button class="chip" aria-pressed={faellig === iso} onclick={() => (faellig = iso)}>{name}</button>
        {/each}
        <button class="chip" aria-pressed={!faellig} onclick={() => (faellig = "")}>Ohne</button>
      </div>
    </section>
  {/if}
</TelefonSchale>
