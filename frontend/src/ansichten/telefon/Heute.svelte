<script lang="ts">
  // Heute am Telefon: deine offenen Karten aus allen Boards nach Dringlichkeit (wie Heute am Rechner, M-120), dazu deine
  // Termine der nächsten Tage mit Zusagen; jede Gruppe erscheint nur, wenn sie etwas enthält. Erledigen per Halten des
  // Rings, ein Tippen auf die Karte öffnet sie. Serienkarten stehen mit ihrer Uhrzeit dabei.
  import { meinTag, type TagEintrag } from "../../daten/abfragen";
  import { zusagen } from "../../daten/anwendung/termine.svelte";
  import { uhr } from "../../daten/uhr.svelte";
  import { ICH } from "../../daten/ich";
  import { datum } from "../../daten/format";
  import { board } from "../../daten/stand.svelte";
  import type { Karte } from "../../modell";
  import { tageZwischen } from "../../regeln/tage";
  import TelefonSchale from "./TelefonSchale.svelte";
  import TelKarte from "./TelKarte.svelte";

  let { entwurf = "" }: { entwurf?: string } = $props();

  /** Entwurf "halten": an dieser Karte füllt sich gerade der Ring */
  const VORGEFUEHRT = "c-h61";

  const tag = $derived(meinTag(ICH));
  const karten = (liste: TagEintrag[]): Karte[] => liste.map((e) => e.karte);
  const gruppen = $derived([
    { id: "ueber", name: "Überfällig", karten: karten(tag.ueberfaellig), zahl: "gefahr" },
    { id: "heute", name: "Heute fällig", karten: karten([...tag.heute, ...tag.serien]), zahl: "warnung" },
    { id: "woche", name: "Diese Woche", karten: karten(tag.woche), zahl: "" },
    { id: "liegt", name: "Liegengeblieben", karten: karten(tag.liegengeblieben), zahl: "" },
    { id: "blockiert", name: "Blockiert", karten: karten(tag.blockiert.filter((e) => !tag.liegengeblieben.includes(e))), zahl: "" },
    { id: "fertig", name: "Heute erledigt", karten: karten(tag.erledigt), zahl: "erfolg" },
  ].filter((g) => g.karten.length));
  const termine = $derived([...tag.termine.heute, ...tag.termine.woche]);
  const wochentag = (iso: string): string => {
    const t = tageZwischen(uhr.heute, iso);
    return t === 0 ? "Heute" : t === 1 ? "Morgen" : datum(iso, true);
  };
  /** Termine stehen hinter dem, was heute fällig ist */
  const vorne = $derived(gruppen.filter((g) => g.id === "ueber" || g.id === "heute"));
  const hinten = $derived(gruppen.filter((g) => !vorne.includes(g)));
</script>

<TelefonSchale titel="Heute" unter={datum(uhr.heute, true)} reiter="heute">
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
          {#if t.zugesagt.includes(ICH)}
            <span class="zustand fertig"><i class="fa-solid fa-check"></i>Zugesagt</span>
          {:else}
            <button class="knopf" onclick={() => zusagen(t.id, true)}><i class="fa-solid fa-check"></i>Zusagen</button>
          {/if}
        </span>
      </div>
    {/each}
  </section>
{/snippet}
