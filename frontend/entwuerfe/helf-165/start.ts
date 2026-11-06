// Entwurf HELF-165: dieselbe Gestaltung wie die App (Appkern, Pinnwand), dazu der Baustein als Vorstufe.
import "@fortawesome/fontawesome-free/css/all.min.css";
import "appkern-oberflaeche/leitstand.css";
import "../../src/stil/pinnwand.css";
import "../../src/stil/board.css";
import "../../src/stil/detail.css";
import "../../src/stil/verwaltung.css";
import "../../src/stil/telefon.css";
import "./entwurf.css";
import { mount } from "svelte";
import Entwurf from "./Entwurf.svelte";

mount(Entwurf, { target: document.getElementById("app")! });
