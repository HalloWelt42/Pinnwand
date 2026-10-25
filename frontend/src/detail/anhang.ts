// Anzeige der Anhänge im Kartendetail: ein Symbol je Art der Datei (Liste der Karte und Wahl aus der Kellerwolke).
import type { Anhang } from "../modell";

export const SYMBOL: Record<Anhang["art"], string> = {
  pdf: "fa-file-pdf", bild: "fa-file-image", tabelle: "fa-file-excel", text: "fa-file-lines", ton: "fa-file-audio",
};
