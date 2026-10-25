// Weg der Pinnwand: echte Pfade in der Adresse (/board/haus/12), Zurück und Vor gehen. Geschoben wird über die
// Navigation des Appkerns (sie lädt beim Seitenwechsel eine neue Fassung von selbst); hier dazu Pfad und Zusatz
// (?karte=...) als ein Zustand und das Abfangen von Klicks auf eigene Verweise.
import { gehe as navigationGehe } from "appkern-oberflaeche";

export const weg = $state({ pfad: location.pathname, suche: location.search });

function lesen(): void {
  weg.pfad = location.pathname;
  weg.suche = location.search;
}

/** Zu einem Pfad der App gehen ("/board/haus/12", auch mit Zusatz); `ersetzen` legt keinen neuen Eintrag in den Verlauf */
export function gehe(ziel: string, ersetzen = false): void {
  navigationGehe(ziel, ersetzen);
  lesen();
}

export function wert(name: string): string {
  return new URLSearchParams(weg.suche).get(name) ?? "";
}

/** Klicks auf Verweise der eigenen Seite über den Weg statt neu laden */
export function wegStarten(): () => void {
  const klick = (e: MouseEvent): void => {
    if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    const a = (e.target as HTMLElement).closest<HTMLAnchorElement>("a[href]");
    if (!a || a.target || a.hasAttribute("download")) return;
    const url = new URL(a.href, location.href);
    if (url.origin !== location.origin || url.pathname.startsWith("/api/")) return;
    e.preventDefault();
    gehe(url.pathname + url.search);
  };
  document.addEventListener("click", klick);
  addEventListener("popstate", lesen);
  return () => {
    document.removeEventListener("click", klick);
    removeEventListener("popstate", lesen);
  };
}

/** Pfad eines Boards aus seinem Kürzel (fest, auch beim Umbenennen) */
export function boardPfad(kuerzel: string, rest = ""): string {
  return `/board/${kuerzel.toLowerCase()}${rest ? "/" + rest : ""}`;
}
