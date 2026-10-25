<script lang="ts">
  // Schnell erfassen am Telefon: Board wählen (das zuletzt genutzte ist vorbelegt), Titel, Arbeit oder Idee, Fällig;
  // Anlegen legt die Karte ans Ende der ersten offenen Spalte (oder der Spalte, aus der man kam), du bist zuständig, und
  // das Formular bleibt für die nächste Karte offen (M-32, M-33). Sprechen nimmt über die App Transkription auf.
  import { HEUTE, ORDNER } from "../../beispiel/daten";
  import { datum } from "../../beispiel/format";
  import { board, stand } from "../../beispiel/stand.svelte";
  import { boardPfad, wert } from "../../weg.svelte";
  import { anlegen, zielspalte } from "./aktionen.svelte";
  import { ZULETZT_BOARD } from "./daten";
  import { datumLesen, datumText, naechster, tagePlus } from "./eingabe";
  import Spracheingabe from "./Spracheingabe.svelte";
  import TelefonSchale from "./TelefonSchale.svelte";
  import { telPfad } from "./weg";

  let { entwurf = "" }: { entwurf?: string } = $props();

  const BOARDS = ORDNER.flatMap((o) => o.boards);
  const artVon = (id: string): "arbeit" | "idee" => (board(id).module.zeiterfassung ? "arbeit" : "idee");
  const vorgabe = stand.boards.find((x) => x.kuerzel.toLowerCase() === wert("board"))?.id ?? ZULETZT_BOARD;

  let boardId = $state(vorgabe);
  let spalteWunsch = $state(wert("spalte"));
  let titel = $state("");
  let beschreibung = $state("");
  let art = $state(artVon(vorgabe));
  let faellig = $state("");
  let fehler = $state("");
  let ausSprache = $state(false);
  let angelegt = $state<{ schluessel: string; pfad: string; spalte: string } | null>(null);
  let sprache = $state(false);
  $effect(() => { sprache = entwurf === "sprache"; });

  const b = $derived(board(boardId));
  const spalte = $derived(zielspalte(boardId, spalteWunsch));
  const FAELLIG: [string, string][] = [["Heute", HEUTE], ["Morgen", tagePlus(HEUTE, 1)], [datum(naechster(5), true), naechster(5)]];

  function boardWaehlen(id: string): void {
    boardId = id;
    spalteWunsch = "";
    art = artVon(id);
  }

  function anlegenKlick(): void {
    if (!titel.trim()) return;
    const iso = faellig.trim() ? datumLesen(faellig) : undefined;
    if (iso === null) { fehler = "Fällig bitte wie 30.10.2026 eingeben."; return; }
    const k = anlegen(boardId, spalte.id, { titel, art, faellig: iso, beschreibung: beschreibung.trim() || undefined });
    angelegt = { schluessel: k.schluessel, pfad: telPfad(boardPfad(b.kuerzel, k.schluessel.split("-")[1])), spalte: spalte.name };
    titel = "";
    beschreibung = "";
    faellig = "";
    fehler = "";
    ausSprache = false;
  }

  function uebernehmen(text: string): void {
    titel = (text.match(/^[^.!?]+/)?.[0] ?? text).trim();
    beschreibung = text;
    ausSprache = true;
    angelegt = null;
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
      <div class="hinweis erfolg"><i class="fa-solid fa-circle-check"></i>
        <div><b>{angelegt.schluessel}</b> angelegt in {angelegt.spalte}. Die nächste kann folgen.</div>
        <span class="rechts"><a class="knopf" href={angelegt.pfad}>Öffnen</a></span></div>
    {/if}
    {#if ausSprache}
      <div class="hinweis"><i class="fa-solid fa-wave-square"></i><div>Aus der Sprache übernommen; Titel und Beschreibung bitte prüfen.</div></div>
    {/if}

    <section class="pw-tel-abschnitt" aria-label="Board">
      <div class="etikett">Board</div>
      <div class="pw-tel-wahl">
        {#each BOARDS as id (id)}
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
      <input class="eingabe zahl" bind:value={faellig} inputmode="numeric" placeholder="TT.MM.JJJJ, leer: ohne" />
      <div class="pw-tel-chips">
        {#each FAELLIG as [name, iso] (iso)}
          <button class="chip" aria-pressed={datumLesen(faellig) === iso} onclick={() => (faellig = datumText(iso))}>{name}</button>
        {/each}
        <button class="chip" aria-pressed={!faellig} onclick={() => (faellig = "")}>Ohne</button>
      </div>
    </section>
    {#if fehler}<div class="hinweis warnung"><i class="fa-solid fa-triangle-exclamation"></i><div>{fehler}</div></div>{/if}
  {/if}
</TelefonSchale>
