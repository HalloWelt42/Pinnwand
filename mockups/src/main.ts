import "@fortawesome/fontawesome-free/css/all.min.css";
import "appkern-oberflaeche/leitstand.css";
import "./stil/pinnwand.css";
import "./stil/uebersicht.css";
import "./stil/verwaltung.css";
import "./stil/zeit.css";
import "./stil/planung.css";
import "./stil/telefon.css";
import { mount } from "svelte";
import App from "./App.svelte";

mount(App, { target: document.getElementById("app")! });
