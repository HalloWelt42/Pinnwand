// Einstieg: Symbole als Paket, die Gestaltung aus dem Appkern (Leitstand, Anmeldung, Aufklappliste), die der Pinnwand,
// dann die App.
import "@fortawesome/fontawesome-free/css/all.min.css";
import "appkern-oberflaeche/leitstand.css";
import "appkern-oberflaeche/anmeldung.css";
import "appkern-oberflaeche/auswahl.css";
import "appkern-oberflaeche/hilfe.css";
import "./stil/pinnwand.css";
import "./stil/board.css";
import "./stil/detail.css";
import "./stil/uebersicht.css";
import "./stil/verwaltung.css";
import "./stil/zeit.css";
import "./stil/planung.css";
import "./stil/telefon.css";
import { mount } from "svelte";
import App from "./App.svelte";

mount(App, { target: document.getElementById("app")! });
