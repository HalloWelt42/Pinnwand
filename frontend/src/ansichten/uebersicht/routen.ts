// Wege dieses Bereichs: Pfad der App auf Ansicht (siehe src/routen.ts). Die Liste eines Boards (/board/<kürzel>/liste)
// zeigt das Board selbst über seine Ansichten (board/ansichten.ts); Archiv und Papierkorb haben einen eigenen Kopf.
import { boardAusKuerzel, type Route } from "../../routen";
import Archiv from "./Archiv.svelte";
import Heute from "./Heute.svelte";
import Hinweise from "./Hinweise.svelte";
import Papierkorb from "./Papierkorb.svelte";

export const ROUTEN: Route[] = [
  { geraet: "rechner", muster: /^\/heute$/, ansicht: () => ({ navi: "heute", komponente: Heute, werte: {} }) },
  { geraet: "rechner", muster: /^\/hinweise$/, ansicht: () => ({ navi: "hinweise", komponente: Hinweise, werte: {} }) },
  {
    geraet: "rechner",
    muster: /^\/board\/([a-z0-9]+)\/(archiv|papierkorb)$/,
    ansicht: (m) => {
      const b = boardAusKuerzel(m[1]);
      if (!b) return null;
      return { navi: b.id, komponente: m[2] === "archiv" ? Archiv : Papierkorb, werte: { boardId: b.id } };
    },
  },
];
