// Was nur die Ansichten der Verwaltung brauchen: Grenzen der Zahlenfelder, die Grundfelder als Erklärung und die
// Reiter mit ihren Adressen. Daten, Namen und Regeln stehen in der gemeinsamen Schicht.


/** Grundfelder jeder Karte (fest, nicht abschaltbar), als Erklärung bei den eigenen Feldern */
export const GRUNDFELDER = ["Titel", "Beschreibung", "Notizen", "Arbeit oder Idee", "Zuständige", "Priorität", "Start", "Fällig",
  "Labels", "Checkliste", "Kommentare", "Cover", "Blockiert"];

/** Reiter der Board-Einstellungen, je mit eigener Adresse /board/<kürzel>/einstellungen/<reiter> */
export const BOARD_REITER = [
  { id: "allgemein", name: "Allgemein", symbol: "fa-sliders" },
  { id: "spalten", name: "Spalten", symbol: "fa-grip-vertical" },
  { id: "labels", name: "Labels", symbol: "fa-tags" },
  { id: "felder", name: "Felder", symbol: "fa-rectangle-list" },
  { id: "rollen", name: "Rollen und Rechte", symbol: "fa-user-shield" },
  { id: "mitglieder", name: "Mitglieder", symbol: "fa-users" },
  { id: "module", name: "Module", symbol: "fa-puzzle-piece" },
] as const;

/** Reiter der persönlichen Einstellungen, je mit eigener Adresse /einstellungen/<reiter> */
export const PERSON_REITER = [
  { id: "darstellung", name: "Darstellung", symbol: "fa-circle-half-stroke" },
  { id: "hinweise", name: "Hinweise", symbol: "fa-bell" },
  { id: "konto", name: "Konto", symbol: "fa-circle-user" },
  { id: "papierkorb", name: "Papierkorb", symbol: "fa-trash-can" },
  { id: "gestaltung", name: "Gestaltung", symbol: "fa-palette" },
] as const;
