// Nachladen beim Rollen (HELF-50): ein Element am Ende einer langen Liste meldet, sobald es in Sicht kommt; die Liste
// zeigt dann die nächsten Einträge. Rollfelder dazwischen schneiden mit, das Element zählt erst, wenn es wirklich zu
// sehen ist. Ein Knopf "Mehr laden" an derselben Stelle bleibt der Weg ohne Rollen.

export interface Nachladen {
  /** zeigt die nächsten Einträge */
  mehr: () => void;
  /** wie viele gerade gezeigt sind: ändert sich die Zahl, prüft das Element neu (steht es noch in Sicht, lädt es weiter) */
  gezeigt: number;
}

/** Svelte-Aktion: ruft `mehr`, sobald das Element in Sicht kommt (mit etwas Vorlauf) */
export function nachladen(element: HTMLElement, angaben: Nachladen): { update: (neu: Nachladen) => void; destroy: () => void } {
  let jetzt = angaben;
  const beobachter = new IntersectionObserver((eintraege) => {
    if (eintraege.some((e) => e.isIntersecting)) jetzt.mehr();
  }, { rootMargin: "0px 0px 200px 0px" });
  beobachter.observe(element);
  return {
    update(neu) {
      const neuPruefen = neu.gezeigt !== jetzt.gezeigt;
      jetzt = neu;
      if (neuPruefen) {
        beobachter.unobserve(element);
        beobachter.observe(element);
      }
    },
    destroy() { beobachter.disconnect(); },
  };
}
