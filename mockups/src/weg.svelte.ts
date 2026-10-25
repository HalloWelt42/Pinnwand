// Weg der Entwürfe: echte Pfade in der Adresse wie später in der App (/board/prod/131), Zurück und Vor gehen.
// In der App übernimmt das die Navigation des Appkerns (navigation, gehe); hier reicht ein kleiner Weg, der zusätzlich
// den Zusatz ?entwurf=... für vorgeführte Zustände kennt.

export const weg = $state({ pfad: location.pathname, suche: location.search });

function lesen(): void {
  weg.pfad = location.pathname;
  weg.suche = location.search;
}

export function gehe(ziel: string): void {
  if (ziel !== location.pathname + location.search) history.pushState(null, "", ziel);
  lesen();
}

export function wert(name: string): string {
  return new URLSearchParams(weg.suche).get(name) ?? "";
}

/** Klicks auf Verweise der eigenen Seite über den Weg statt neu laden (wie die Schale von Fundus) */
export function wegStarten(): () => void {
  const klick = (e: MouseEvent): void => {
    if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    const a = (e.target as HTMLElement).closest<HTMLAnchorElement>("a[href]");
    if (!a || a.target || a.hasAttribute("download")) return;
    const url = new URL(a.href, location.href);
    if (url.origin !== location.origin) return;
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
