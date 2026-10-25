// Text in die Zwischenablage. Die Schnittstelle des Browsers gibt es nur in sicheren Kontexten (https, localhost); über
// http im Heimnetz fehlt sie. Dann gilt der Ersatzweg: ein unsichtbares Textfeld und execCommand("copy"), das nur im
// Klick selbst wirkt; deshalb läuft er ohne Warten noch im selben Aufruf. Ergebnis: ob kopiert wurde.

export function kopieren(text: string): Promise<boolean> {
  if (window.isSecureContext && navigator.clipboard?.writeText) {
    return navigator.clipboard.writeText(text).then(() => true, () => ersatzweg(text));
  }
  return Promise.resolve(ersatzweg(text));
}

function ersatzweg(text: string): boolean {
  const vorher = document.activeElement instanceof HTMLElement ? document.activeElement : null;
  const feld = document.createElement("textarea");
  feld.value = text;
  feld.readOnly = true;
  feld.setAttribute("aria-hidden", "true");
  Object.assign(feld.style, { position: "fixed", top: "0", left: "0", width: "1px", height: "1px", opacity: "0", pointerEvents: "none" });
  document.body.append(feld);
  feld.select();
  let kopiert = false;
  try {
    kopiert = document.execCommand("copy");
  } catch {
    kopiert = false;
  }
  feld.remove();
  vorher?.focus({ preventScroll: true });
  return kopiert;
}
