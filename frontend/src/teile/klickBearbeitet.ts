// Ein Klick in den Text eines eigenen Kommentars öffnet das Bearbeiten (HELF-98), aber nur ein einfacher Klick ohne
// Auswahl: Links, Knöpfe und aufklappbare Teile behalten ihren Klick, wer Text markiert (ziehen, Doppel- oder
// Dreifachklick), landet nicht im Feld. Der einfache Klick wartet dafür kurz, ob ein zweiter folgt.

const WARTEN = 250;
const EIGENER_KLICK = "a, button, input, label, summary, details, img, video, audio";

export function klickBearbeitet(knoten: HTMLElement, oeffnen: () => void): { update(neu: () => void): void; destroy(): void } {
  let tun = oeffnen;
  let uhr: ReturnType<typeof setTimeout> | undefined;

  function klick(e: MouseEvent): void {
    clearTimeout(uhr);
    if (e.button !== 0 || e.detail > 1 || e.ctrlKey || e.metaKey || e.shiftKey || e.altKey) return;
    if (e.target instanceof Element && e.target.closest(EIGENER_KLICK)) return;
    uhr = setTimeout(() => {
      const auswahl = getSelection();
      if (auswahl && !auswahl.isCollapsed && auswahl.toString().trim()) return;
      tun();
    }, WARTEN);
  }

  knoten.addEventListener("click", klick);
  return {
    update(neu) {
      tun = neu;
    },
    destroy() {
      clearTimeout(uhr);
      knoten.removeEventListener("click", klick);
    },
  };
}
