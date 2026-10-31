<script lang="ts">
  // Schreibhilfe für Markdown in einem Textfeld (HELF-92, Kommentare am Rechner und am Telefon): kleine Knöpfe setzen die
  // Zeichen um die Auswahl (fett, kursiv, Code, Verweis) oder vor jede gewählte Zeile (Überschrift, Liste, Häkchenliste,
  // Zitat); "Vorschau" zeigt den Text unter dem Feld so, wie er nach dem Senden erscheint, mit demselben Darsteller wie überall
  // (teile/markdown.ts). Das Feld selbst gehört der Seite; die Leiste ändert nur seinen Text und setzt die Auswahl neu.
  import { tick, type Snippet } from "svelte";
  import { markdownHtml, type MarkdownOptionen } from "./markdown";

  let { feld, text = $bindable(""), optionen = {}, gross = false, children }: {
    /** das Textfeld, auf das die Knöpfe wirken; es steht als `children` zwischen Leiste und Vorschau */
    feld: HTMLTextAreaElement | undefined;
    children: Snippet;
    text?: string;
    optionen?: MarkdownOptionen;
    /** größere Knöpfe (Telefon) */
    gross?: boolean;
  } = $props();

  let vorschau = $state(false);
  const html = $derived(vorschau ? markdownHtml(text, optionen) : "");

  /** setzt neuen Text und markiert danach von `von` bis `bis` */
  async function setzen(neu: string, von: number, bis: number): Promise<void> {
    text = neu;
    await tick();
    feld?.focus();
    feld?.setSelectionRange(von, bis);
  }

  /** Zeichen um die Auswahl; ohne Auswahl mit einem Platzhalter, der danach markiert ist */
  function umschliessen(vor: string, nach: string, platzhalter: string): void {
    const a = feld?.selectionStart ?? text.length, e = feld?.selectionEnd ?? text.length;
    const innen = text.slice(a, e) || platzhalter;
    void setzen(text.slice(0, a) + vor + innen + nach + text.slice(e), a + vor.length, a + vor.length + innen.length);
  }

  /** ein Zeichen vor jede gewählte Zeile (ohne Auswahl: vor die Zeile mit der Einfügemarke) */
  function zeilen(praefix: string): void {
    const a = feld?.selectionStart ?? text.length, e = feld?.selectionEnd ?? text.length;
    const anfang = text.lastIndexOf("\n", a - 1) + 1;
    const ende = text.indexOf("\n", e) === -1 ? text.length : text.indexOf("\n", e);
    const block = text.slice(anfang, ende).split("\n").map((z) => (z.startsWith(praefix) ? z : praefix + z)).join("\n");
    void setzen(text.slice(0, anfang) + block + text.slice(ende), anfang, anfang + block.length);
  }

  const KNOEPFE: { symbol: string; titel: string; tun: () => void }[] = [
    { symbol: "fa-bold", titel: "Fett: **Text**", tun: () => umschliessen("**", "**", "fett") },
    { symbol: "fa-italic", titel: "Kursiv: *Text*", tun: () => umschliessen("*", "*", "kursiv") },
    { symbol: "fa-heading", titel: "Überschrift: ## am Zeilenanfang", tun: () => zeilen("## ") },
    { symbol: "fa-list-ul", titel: "Liste: - am Zeilenanfang", tun: () => zeilen("- ") },
    { symbol: "fa-list-check", titel: "Häkchenliste: - [ ] am Zeilenanfang", tun: () => zeilen("- [ ] ") },
    { symbol: "fa-quote-left", titel: "Zitat: > am Zeilenanfang", tun: () => zeilen("> ") },
    { symbol: "fa-code", titel: "Code: `Text`; für mehrere Zeilen ``` davor und danach", tun: () => umschliessen("`", "`", "Code") },
    { symbol: "fa-link", titel: "Verweis: [Text](Adresse)", tun: () => umschliessen("[", "](https://)", "Text") },
  ];
</script>

<div class="pw-mdleiste" class:gross role="toolbar" aria-label="Markdown-Hilfe">
  {#each KNOEPFE as k (k.symbol)}
    <button type="button" class="knopf ohne symbol klein" title={k.titel} aria-label={k.titel}
            onpointerdown={(e) => e.preventDefault()} onclick={k.tun}><i class="fa-solid {k.symbol}"></i></button>
  {/each}
  <button type="button" class="knopf ohne klein pw-mdleiste-vorschau" aria-pressed={vorschau} disabled={!text.trim() && !vorschau}
          title={vorschau ? "Vorschau ausblenden" : "Unter dem Feld zeigen, wie der Text nach dem Senden erscheint"} onclick={() => (vorschau = !vorschau)}>
    <i class="fa-solid {vorschau ? 'fa-eye-slash' : 'fa-eye'}"></i>Vorschau</button>
</div>
{@render children()}
{#if vorschau}
  <div class="pw-mdleiste-ansicht pw-md" aria-label="Vorschau">{@html html}</div>
{/if}
