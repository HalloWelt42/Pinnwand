<script lang="ts">
  // Heute am Telefon: deine offenen Karten aus allen Boards nach Dringlichkeit (wie Heute am Rechner, M-120), dazu deine
  // nächsten Termine; jede Gruppe erscheint nur, wenn sie etwas enthält. Erledigen per Halten des Rings, ein Tippen auf
  // die Karte öffnet sie. Serienkarten stehen mit ihrer Uhrzeit dabei.
  import { HEUTE, ICH, TERMINE } from "../../beispiel/daten";
  import { alterTage, datum, tageZwischen } from "../../beispiel/format";
  import { board, stand } from "../../beispiel/stand.svelte";
  import type { Karte } from "../../modell";
  import TelefonSchale from "./TelefonSchale.svelte";
  import TelKarte from "./TelKarte.svelte";

  let { entwurf = "" }: { entwurf?: string } = $props();

  /** Entwurf "halten": an dieser Karte füllt sich gerade der Ring */
  const VORGEFUEHRT = "c-h61";
  const LIEGT_AB = 8;
  const PRIO = { dringend: 0, hoch: 1, mittel: 2, niedrig: 3, keine: 4 };

  const offen = (k: Karte): boolean => !board(k.board).spalten.find((s) => s.id === k.spalte)?.erledigt;
  const meine = $derived(stand.karten.filter((k) => k.zustaendig.includes(ICH)));
  const bis = (k: Karte): number => (k.faellig ? tageZwischen(HEUTE, k.faellig) : Infinity);
  const ordnen = (a: Karte, b: Karte): number => bis(a) - bis(b) || PRIO[a.prioritaet] - PRIO[b.prioritaet];

  const gruppen = $derived.by(() => {
    const auf = meine.filter(offen);
    const ueber = auf.filter((k) => bis(k) < 0).sort(ordnen);
    const heute = auf.filter((k) => bis(k) === 0).sort(ordnen);
    const woche = auf.filter((k) => bis(k) > 0 && bis(k) <= 7).sort(ordnen);
    const gelistet = new Set([...ueber, ...heute, ...woche].map((k) => k.id));
    const liegt = auf.filter((k) => !gelistet.has(k.id) && !k.laeuft && alterTage(k.bewegtAm) >= LIEGT_AB);
    const blockiert = auf.filter((k) => !gelistet.has(k.id) && k.blockiert);
    const fertig = meine.filter((k) => !offen(k) && k.abgeschlossen === HEUTE);
    return [
      { id: "ueber", name: "Überfällig", karten: ueber, zahl: "gefahr" },
      { id: "heute", name: "Heute fällig", karten: heute, zahl: "warnung" },
      { id: "woche", name: "Diese Woche", karten: woche, zahl: "" },
      { id: "liegt", name: "Liegengeblieben", karten: liegt, zahl: "" },
      { id: "blockiert", name: "Blockiert", karten: blockiert, zahl: "" },
      { id: "fertig", name: "Heute erledigt", karten: fertig, zahl: "erfolg" },
    ].filter((g) => g.karten.length);
  });
  const termine = $derived(TERMINE.filter((t) => t.teilnehmer.includes(ICH) && t.datum >= HEUTE && tageZwischen(HEUTE, t.datum) <= 7)
    .sort((a, b) => (a.datum + a.von).localeCompare(b.datum + b.von)));
  const wochentag = (iso: string): string => {
    const t = tageZwischen(HEUTE, iso);
    return t === 0 ? "Heute" : t === 1 ? "Morgen" : datum(iso, true);
  };
  /** Termine stehen hinter dem, was heute fällig ist */
  const vorne = $derived(gruppen.filter((g) => g.id === "ueber" || g.id === "heute"));
  const hinten = $derived(gruppen.filter((g) => !vorne.includes(g)));
</script>

<TelefonSchale titel="Heute" unter={datum(HEUTE, true)} reiter="heute">
  {#each vorne as g (g.id)}{@render gruppe(g)}{/each}
  {#if termine.length}{@render terminListe()}{/if}
  {#each hinten as g (g.id)}{@render gruppe(g)}{/each}
  {#if !gruppen.length && !termine.length}
    <div class="leer"><i class="fa-regular fa-sun"></i><h2>Nichts fällig</h2><p>Heute steht keine deiner Karten an.</p></div>
  {/if}
</TelefonSchale>

{#snippet gruppe(g: (typeof gruppen)[number])}
  <section class="pw-tel-abschnitt" aria-label={g.name}>
    <div class="etikett">{g.name}<span class="zaehler {g.zahl}">{g.karten.length}</span></div>
    {#each g.karten as k (k.id)}
      <TelKarte karte={k} ort von="heute" halten={g.id !== "fertig"} vorfuehren={entwurf === "halten" && k.id === VORGEFUEHRT ? 0.5 : 0} />
    {/each}
  </section>
{/snippet}

{#snippet terminListe()}
  <section class="pw-tel-abschnitt" aria-label="Termine">
    <div class="etikett">Termine<span class="zaehler">{termine.length}</span></div>
    {#each termine as t (t.id)}
      {@const b = board(t.board)}
      <div class="pw-tel-termin">
        <span class="wann"><span class="tag">{wochentag(t.datum)}</span><span class="zahl">{t.von}</span></span>
        <span class="was">
          <span class="titel">{t.titel}</span>
          <span class="angaben" data-farbe={b.farbe} title={b.name}><span class="pw-farbpunkt"></span>{b.kuerzel} · bis <span class="zahl">{t.bis}</span>{t.ort ? ` · ${t.ort}` : ""}</span>
          {#if t.bestaetigt.includes(ICH)}
            <span class="zustand fertig"><i class="fa-solid fa-check"></i>Zugesagt</span>
          {:else}
            <span class="zustand wartet" title="Noch nicht zugesagt">Noch offen</span>
          {/if}
        </span>
      </div>
    {/each}
  </section>
{/snippet}
