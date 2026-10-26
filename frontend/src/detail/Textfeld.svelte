<script lang="ts">
  // Markdown-Feld der Karte (Beschreibung, Notizen; M-56, M-57): gerendert lesen, ein Klick bearbeitet. Die Beschreibung
  // an Ort und Stelle, die Notizen im Vollbild mit Vorschau daneben; Vollbild geht für beide. "Fertig" (oder Strg und
  // Enter) speichert über den Anwendungsfall, "Verwerfen" und Escape stellen den Stand vom Öffnen wieder her. Schließt
  // jemand das Detail oder wechselt die Karte, während der Editor offen ist, wird gespeichert: nichts geht still verloren
  // (die alte App verlor so die letzten 600 ms). Gespeichert wird immer an der Karte, an der das Bearbeiten begann.
  import { Hilfepunkt } from "appkern-oberflaeche";
  import { onDestroy, tick } from "svelte";
  import { markdownHtml, type MarkdownOptionen } from "../teile/markdown";
  import { verlassen } from "../teile/verwerfen";

  let { name, text = "", leer, schreiben, nurVollbild = false, vorlesen, liest = false, speichern, optionen = {} }: {
    name: string;
    /** der gespeicherte Text der Karte (Markdown) */
    text?: string;
    /** Leerzustand, etwa "Keine Beschreibung." */
    leer: string;
    /** Recht, die Karte zu bearbeiten */
    schreiben: boolean;
    /** bearbeitet wird nur im Vollbild (Notizen) */
    nurVollbild?: boolean;
    /** liest den Text vor (Modul Vorlesen); ohne: kein Knopf */
    vorlesen?: () => void;
    /** liest gerade (der Knopf hält dann an) */
    liest?: boolean;
    /** speichert den Text; Ergebnis: ob es wirkte (sonst bleibt der Editor offen) */
    speichern: (text: string) => Promise<boolean>;
    optionen?: MarkdownOptionen;
  } = $props();

  let modus = $state<"lesen" | "ort" | "vollbild">("lesen");
  let entwurf = $state("");
  let ausgang = "";
  let ziel: ((text: string) => Promise<boolean>) | null = null;
  let feld = $state<HTMLTextAreaElement>();
  let abschnitt = $state<HTMLElement>();
  const geaendert = $derived(modus !== "lesen" && entwurf.trim() !== ausgang.trim());
  const ansicht = $derived(markdownHtml(text, optionen));
  const vorschau = $derived(modus === "vollbild" ? markdownHtml(entwurf, optionen) : "");

  async function oeffnen(m: "ort" | "vollbild"): Promise<void> {
    if (!schreiben) return;
    if (modus === "lesen") {
      ausgang = text;
      entwurf = text;
      ziel = speichern;
    }
    modus = m;
    await tick();
    feld?.focus({ preventScroll: m === "vollbild" });
  }

  /** Editor zu; der Fokus bleibt in der Fläche um das Feld (das Kartendetail) */
  function schliessen(): void {
    if (abschnitt) verlassen(abschnitt);
    modus = "lesen";
    ziel = null;
  }

  async function fertig(): Promise<void> {
    if (geaendert && ziel && !(await ziel(entwurf.trim()))) return;
    schliessen();
  }

  function verwerfen(): void {
    entwurf = ausgang;
    schliessen();
  }

  function taste(e: KeyboardEvent): void {
    if (e.defaultPrevented) return;
    if (e.key === "Escape" && !e.isComposing) { e.preventDefault(); verwerfen(); }
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) { e.preventDefault(); void fertig(); }
  }

  /** ein Klick auf den Text bearbeitet; ein Verweis darin führt dagegen zu seinem Ziel */
  function klick(e: MouseEvent): void {
    if ((e.target as HTMLElement).closest("a")) return;
    oeffnen(nurVollbild ? "vollbild" : "ort");
  }

  onDestroy(() => { if (geaendert && ziel) void ziel(entwurf.trim()); });
</script>

{#snippet knoepfe()}
  <button class="knopf haupt klein" onclick={fertig} title="Speichern und schließen (Strg und Enter)"><i class="fa-solid fa-check"></i>Fertig</button>
  <button class="knopf ohne klein" onclick={verwerfen} title="Stand vom Öffnen wiederherstellen (Escape)">Verwerfen</button>
  <span class="pw-textfeld-stand" class:offen={geaendert}>{geaendert ? "Nicht gespeichert" : "Unverändert"}</span>
{/snippet}

<section class="pw-abschnitt" bind:this={abschnitt}>
  <div class="etikett">{name}<Hilfepunkt thema="kartendetail" abschnitt="texte" />
    <span class="rechts">
      {#if vorlesen && text.trim()}
        <button class="knopf ohne symbol klein" title={liest ? "Vorlesen anhalten" : "Vorlesen"} aria-pressed={liest} onclick={vorlesen}>
          <i class="fa-solid {liest ? 'fa-stop' : 'fa-volume-high'}"></i></button>
      {/if}
      {#if schreiben && !nurVollbild && modus === "lesen"}
        <button class="knopf ohne symbol klein" title="Bearbeiten" onclick={() => oeffnen("ort")}><i class="fa-solid fa-pen"></i></button>
      {/if}
      {#if schreiben && (text.trim() || !nurVollbild)}
        <button class="knopf ohne symbol klein" title="Im Vollbild bearbeiten, mit Vorschau" onclick={() => oeffnen("vollbild")}><i class="fa-solid fa-expand"></i></button>
      {/if}
    </span>
  </div>
  {#if modus === "ort"}
    <div class="pw-text bearbeiten">
      <textarea bind:this={feld} bind:value={entwurf} onkeydown={taste} aria-label="{name} bearbeiten"
                placeholder="Text in Markdown: **fett**, *kursiv*, - Liste, # Überschrift"></textarea>
    </div>
    <div class="pw-textfeld-knoepfe">{@render knoepfe()}</div>
  {:else if text.trim()}
    <!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_static_element_interactions -->
    <div class="pw-text pw-md" class:nur-lesen={!schreiben} onclick={klick}
         title={schreiben ? (nurVollbild ? "Klick öffnet das Vollbild zum Bearbeiten" : "Klick zum Bearbeiten") : ""}>{@html ansicht}</div>
  {:else if schreiben}
    <button class="pw-text noch-leer" onclick={() => oeffnen(nurVollbild ? "vollbild" : "ort")}>{leer} Klicken zum Bearbeiten.</button>
  {:else}
    <div class="pw-text noch-leer nur-lesen">{leer}</div>
  {/if}
</section>

{#if modus === "vollbild"}
  <div class="pw-textfeld-voll" role="dialog" aria-label="{name} bearbeiten" tabindex="-1" onkeydown={taste}>
    <div class="pw-textfeld-voll-kopf">
      <b>{name}</b>
      <span class="rechts">{@render knoepfe()}
        {#if !nurVollbild}<button class="knopf ohne symbol klein" title="Zurück an Ort und Stelle" onclick={() => oeffnen("ort")}><i class="fa-solid fa-compress"></i></button>{/if}
      </span>
    </div>
    <div class="pw-textfeld-voll-raum">
      <textarea class="pw-textfeld-eingabe" bind:this={feld} bind:value={entwurf} aria-label="{name} in Markdown"
                placeholder="Text in Markdown: **fett**, *kursiv*, - Liste, # Überschrift, | Tabelle |"></textarea>
      <div class="pw-textfeld-vorschau pw-md" aria-label="Vorschau">
        {#if entwurf.trim()}{@html vorschau}{:else}<span class="schwach">Die Vorschau erscheint beim Schreiben.</span>{/if}
      </div>
    </div>
  </div>
{/if}
