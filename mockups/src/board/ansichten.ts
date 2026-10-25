// Ansichten eines Boards neben dem Spaltenstreifen (Pfad /board/<kürzel>/<ansicht>): jede bekommt das Board und den
// Entwurfszusatz und zeichnet unter dem gemeinsamen Kopf und der Werkzeugleiste des Boards.
import type { Component } from "svelte";
import Liste from "../ansichten/uebersicht/Liste.svelte";
import Kalender from "../ansichten/planung/Kalender.svelte";
import Zeitachse from "../ansichten/planung/Zeitachse.svelte";

export const BOARDANSICHTEN: Record<string, Component<any>> = { liste: Liste, kalender: Kalender, zeitachse: Zeitachse };
