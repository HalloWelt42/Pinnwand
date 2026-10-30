// Tasten in Eingabefeldern: Enter gilt erst, wenn keine Zusammensetzung läuft (Akzent über eine Tottaste, Wortvorschlag,
// Diktat, Eingabehilfen). Sonst schließt dasselbe Enter die Zusammensetzung ab: das Feld hätte sich schon geleert und
// das zusammengesetzte Stück käme danach wieder hinein, die Karte entstünde ohne es. Chrome meldet das mit isComposing,
// Safari mit dem Tastencode 229 nach dem Ende der Zusammensetzung.

/** Enter, das wirklich abschickt (nicht das Ende einer Zusammensetzung) */
export function enter(e: KeyboardEvent): boolean {
  return e.key === "Enter" && !e.isComposing && e.keyCode !== 229;
}
