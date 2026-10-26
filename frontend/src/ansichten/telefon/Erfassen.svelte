<script lang="ts">
  // Schnell erfassen am Telefon: Board wählen (das zuletzt genutzte ist vorbelegt, gemerkt auf diesem Gerät), Titel,
  // Arbeit oder Idee (nur mit Zeiterfassung, sonst die Kartenart des Boards), Fällig; Anlegen legt die Karte ans Ende der
  // ersten offenen Spalte (oder der Spalte, aus der man kam), du bist zuständig, und das Formular bleibt für die nächste
  // Karte offen (M-32, M-33). Mit dem Modul Transkripte nimmt "Sprechen" auf; der Text wächst beim Sprechen und kommt
  // nach dem Stopp in Titel und Beschreibung, geprüft vor dem Anlegen.
  import { boardGruppen, darf, kartenNummer } from "../../daten/abfragen";
  import { anlegen } from "../../daten/anwendung/karten.svelte";
  import { transkripteDa } from "../../daten/anwendung/transkripte.svelte";
  import { uhr } from "../../daten/uhr.svelte";
  import { datum } from "../../daten/format";
  import { board, karte, stand } from "../../daten/stand.svelte";
  import { plusTage, wochentag } from "../../regeln/tage";
  import DatumFeld from "../../teile/DatumFeld.svelte";
  import { boardPfad, wert } from "../../weg.svelte";
  import { geraet, geraetMerken } from "./geraet.svelte";
  import Spracheingabe, { sprechenStarten } from "./Spracheingabe.svelte";
  import TelefonSchale from "./TelefonSchale.svelte";
  import { telPfad } from "./weg";

  /** Boards, in denen du Karten anlegen darfst, nach deinen Ordnern */
  const moegliche = () => boardGruppen().flatMap((g) => g.boards).filter((x) => darf(x, "karten.anlegen")).map((x) => x.id);
  const boards = $derived(moegliche());
  const vorgabe = stand.boards.find((x) => x.kuerzel.toLowerCase() === wert("board"))?.id
    ?? (moegliche().includes(geraet.board) ? geraet.board : moegliche()[0] ?? "");

  let boardId = $state(vorgabe);
  let spalteWunsch = $state(wert("spalte"));
  let titel = $state("");
  let beschreibung = $state("");
  let datumGueltig = $state(true);
  let gewaehlt = $state<"arbeit" | "idee" | null>(null);
  /** die Aufnahme läuft; Titel und Beschreibung kamen aus der Sprache (Hinweis zum Prüfen) */
  let sprache = $state(false);
  let ausSprache = $state(false);
  /** Fälligkeit als ISO-Tag, leer: ohne */
  let faellig = $state("");
  /** die zuletzt hier angelegte Karte (verschwindet, wenn Rückgängig sie wieder entfernt) */
  let angelegtId = $state("");
  const angelegt = $derived(angelegtId ? karte(angelegtId) : undefined);
  const b = $derived(board(boardId));
  const mitZeit = $derived(!!boardId && b.module.zeiterfassung);
  const art = $derived(mitZeit ? gewaehlt ?? b.kartenart : b.kartenart);
  /** wohin die Karte kommt: die Spalte, aus der man kam, sonst die erste offene (wie anlegen) */
  const spalte = $derived(b.spalten.find((s) => s.id === spalteWunsch) ?? b.spalten.find((s) => !s.erledigt) ?? b.spalten[0]);
  const freitag = plusTage(uhr.heute, ((5 - wochentag(uhr.heute) + 6) % 7) + 1);
  const FAELLIG: [string, string][] = [["Heute", uhr.heute], ["Morgen", plusTage(uhr.heute, 1)], [datum(freitag, true), freitag]];

  function boardWaehlen(id: string): void {
    boardId = id;
    spalteWunsch = "";
    gewaehlt = null;
  }

  async function anlegenKlick(): Promise<void> {
    const k = await anlegen(boardId, spalte.id, { titel, art, faellig: faellig || undefined, beschreibung });
    if (!k) return;
    angelegtId = k.id;
    titel = "";
    beschreibung = "";
    faellig = "";
    ausSprache = false;
    geraet.board = boardId;
    geraetMerken();
  }

  function uebernehmen(text: string): void {
    titel = (text.match(/^[^.!?]+/)?.[0] ?? text).trim().slice(0, 300);
    beschreibung = text;
    ausSprache = true;
    sprache = false;
  }
</script>

{#snippet knoepfe()}
  <div class="pw-tel-aktionen">
    {#if transkripteDa(b)}
      <button class="knopf" onclick={() => { sprechenStarten(boardId); sprache = true; }} title="Per Sprache erfassen (Transkription)"><i class="fa-solid fa-microphone"></i>Sprechen</button>
    {/if}
    <button class="knopf haupt" disabled={!titel.trim() || !datumGueltig} title={datumGueltig ? "" : "Das Datum ist nicht lesbar"} onclick={anlegenKlick}><i class="fa-solid fa-plus"></i>Anlegen</button>
  </div>
{/snippet}

<TelefonSchale titel="Erfassen" unter={sprache ? "Per Sprache" : "Neue Karte"} reiter="erfassen" unten={boards.length && !sprache ? knoepfe : undefined}>
  {#if sprache}
    <Spracheingabe {boardId} {uebernehmen} verwerfen={() => (sprache = false)} />
  {:else if !boards.length}
    <div class="leer"><i class="fa-solid fa-circle-plus"></i><h2>Kein Board zum Erfassen</h2>
      <p>Du brauchst ein Board, in dem du Karten anlegen darfst. Boards legst du am Rechner an.</p></div>
  {:else}
    {#if angelegt}
      <a class="pw-tel-zuletzt" href={telPfad(boardPfad(board(angelegt.board).kuerzel, kartenNummer(angelegt)))}>
        <i class="fa-solid fa-circle-check"></i><span>Zuletzt angelegt: <span class="pw-schluessel">{angelegt.schluessel}</span> {angelegt.titel}</span>
        <i class="fa-solid fa-chevron-right"></i></a>
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
      <span class="pw-tel-notiz">Landet in {spalte.name} · zuständig du{boardId === geraet.board ? " · zuletzt genutzt" : ""}</span>
    </section>

    {#if ausSprache}
      <div class="hinweis"><i class="fa-solid fa-wave-square"></i><div>Aus der Sprache übernommen; Titel und Beschreibung bitte prüfen.</div></div>
    {/if}
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

    {#if mitZeit}
      <section class="pw-tel-abschnitt" aria-label="Art">
        <div class="etikett">Art</div>
        <div class="pw-tel-umschalter" title="Arbeit hat Zeiterfassung, eine Idee nicht">
          <button class:an={art === "arbeit"} aria-pressed={art === "arbeit"} onclick={() => (gewaehlt = "arbeit")}><i class="fa-solid fa-briefcase"></i>Arbeit</button>
          <button class="idee" class:an={art === "idee"} aria-pressed={art === "idee"} onclick={() => (gewaehlt = "idee")}><i class="fa-solid fa-lightbulb"></i>Idee</button>
        </div>
      </section>
    {/if}

    <section class="pw-tel-abschnitt" aria-label="Fällig">
      <div class="etikett">Fällig</div>
      <DatumFeld tag={faellig} ontag={(t) => (faellig = t)} bind:gueltig={datumGueltig} leerErlaubt titel="Fällig wie 30.10.2026 oder 30.10.; leer: ohne" />
      <div class="pw-tel-chips">
        {#each FAELLIG as [name, iso] (iso)}
          <button class="chip" aria-pressed={faellig === iso} onclick={() => (faellig = iso)}>{name}</button>
        {/each}
        <button class="chip" aria-pressed={!faellig} onclick={() => (faellig = "")}>Ohne</button>
      </div>
    </section>
  {/if}
</TelefonSchale>
