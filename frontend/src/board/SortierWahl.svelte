<script lang="ts">
  // Sortierung einer Spalte als kleines Symbol (HELF-50, Nutzer: "mit Mini-Icons umschaltbar"): das Symbol zeigt, wie die
  // Spalte gerade geordnet ist, und erklärt es beim Überfahren; ein Klick öffnet die kleine Auswahl. Die Wahl gilt nur für
  // dich an diesem Gerät (wie das Zeitfenster); die Vorgabe für alle steht im Menü der Spalte. Escape oder ein Klick
  // daneben schließt die Auswahl.
  import { SPALTENSORTIERUNGEN } from "../anzeige";
  import { sortierungVorgabe } from "../daten/abfragen";
  import type { Spalte, Spaltensortierung } from "../modell";

  let { spalte, art, setzen, mitName = false }: {
    spalte: Spalte;
    /** die Sortierung, nach der du die Spalte gerade siehst */
    art: Spaltensortierung;
    setzen: (art: Spaltensortierung) => void;
    /** neben dem Symbol auch den Namen zeigen (Telefon) */
    mitName?: boolean;
  } = $props();

  let offen = $state(false);
  let anker = $state<HTMLElement>();
  const jetzt = $derived(SPALTENSORTIERUNGEN[art]);
  const vorgabe = $derived(sortierungVorgabe(spalte));
  const titel = $derived(`Sortiert nach ${jetzt.name}: ${jetzt.erklaerung}. Klick: andere Sortierung, nur für dich an diesem Gerät`);

  $effect(() => {
    if (!offen) return;
    const daneben = (e: PointerEvent): void => {
      if (!anker?.contains(e.target as Node)) offen = false;
    };
    window.addEventListener("pointerdown", daneben, true);
    return () => window.removeEventListener("pointerdown", daneben, true);
  });

  function taste(e: KeyboardEvent): void {
    if (e.key !== "Escape" || !offen) return;
    e.stopPropagation();
    offen = false;
    anker?.querySelector<HTMLElement>(".pw-sortierwahl-knopf")?.focus();
  }

  function waehlen(neu: Spaltensortierung): void {
    offen = false;
    if (neu !== art) setzen(neu);
  }
</script>

<!-- svelte-ignore a11y_no_static_element_interactions -->
<span class="pw-sortierwahl" bind:this={anker} onkeydown={taste}>
  <button class="knopf ohne klein pw-sortierwahl-knopf" class:symbol={!mitName} class:aktiv={offen} aria-haspopup="menu" aria-expanded={offen}
          aria-label="Sortierung der Spalte {spalte.name}: {jetzt.name}" title={titel} onclick={() => (offen = !offen)}>
    <i class="fa-solid {jetzt.symbol}"></i>{#if mitName}{jetzt.name}{/if}</button>
  {#if offen}
    <div class="pw-sortierwahl-liste" role="menu" aria-label="Sortierung der Spalte {spalte.name}">
      {#each Object.entries(SPALTENSORTIERUNGEN) as [w, s] (w)}
        <button role="menuitemradio" aria-checked={w === art} class:an={w === art} title={s.erklaerung}
                onclick={() => waehlen(w as Spaltensortierung)}>
          <i class="fa-solid {s.symbol}"></i><span>{s.name}</span>
          {#if w === vorgabe}<span class="pw-sortierwahl-vorgabe" title="Vorgabe der Spalte für alle">für alle</span>{/if}
        </button>
      {/each}
    </div>
  {/if}
</span>
