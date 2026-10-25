<script lang="ts">
  // Erfassen per Sprache: das Mikrofon nimmt auf, Zeit und Pegel zeigen, dass es hört; nach "Stopp und übernehmen"
  // setzt die Transkription die Aufnahme in Text um (Nutzer: "Nach dem Stopp"), der erste Satz wird Titel, der ganze
  // Text Beschreibung. Höchstens zwei Minuten, dann hält die Aufnahme von selbst an. Verwerfen beendet ohne Übernahme;
  // geht etwas nicht (kein Mikrofon, die Transkription lässt nicht zu), steht der Grund da, mit "Noch einmal".
  import { onDestroy, onMount } from "svelte";
  import { sprechen } from "../../daten/anwendung/transkripte.svelte";
  import type { Kennung } from "../../modell";

  let { boardId, uebernehmen, verwerfen }: {
    boardId: Kennung;
    uebernehmen: (text: string) => void;
    verwerfen: () => void;
  } = $props();

  /** so lange hört die Transkription am Stück (Sekunden); so viele Balken hat der Pegel */
  const HOECHSTENS_S = 120;
  const BALKEN = 28;
  /** Aufnahmeformate in der Reihenfolge der Wahl (das Telefon von Apple kann nur das zweite) */
  const FORMATE = ["audio/webm;codecs=opus", "audio/mp4", "audio/webm"];

  type Phase = "startet" | "hoert" | "setzt-um" | "fehler";
  let phase = $state<Phase>("startet");
  let grund = $state("");
  let sek = $state(0);
  let pegel = $state<number[]>(Array(BALKEN).fill(0.04));

  let strom: MediaStream | null = null;
  let rekorder: MediaRecorder | null = null;
  let kontext: AudioContext | null = null;
  let stuecke: Blob[] = [];
  let aufnahme: Blob | null = null;
  let takt: ReturnType<typeof setInterval> | undefined;
  let bild = 0;
  let steuerung: AbortController | null = null;

  onMount(() => void starten());
  onDestroy(aufraeumen);

  async function starten(): Promise<void> {
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") {
      fehler("Dieses Gerät oder diese Verbindung erlaubt keine Aufnahme (nötig ist HTTPS und ein Mikrofon)");
      return;
    }
    try {
      strom = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true } });
    } catch (f) {
      fehler(f instanceof DOMException && f.name === "NotAllowedError"
        ? "Kein Zugriff auf das Mikrofon; in den Einstellungen des Telefons für diese Web-App erlauben"
        : "Das Mikrofon lässt sich nicht öffnen");
      return;
    }
    const format = FORMATE.find((f) => MediaRecorder.isTypeSupported(f));
    rekorder = new MediaRecorder(strom, format ? { mimeType: format } : undefined);
    stuecke = [];
    rekorder.ondataavailable = (e) => { if (e.data.size) stuecke.push(e.data); };
    rekorder.onstop = () => {
      aufnahme = new Blob(stuecke, { type: rekorder?.mimeType || format || "audio/webm" });
      void umsetzen();
    };
    rekorder.start(1000);
    pegelMessen(strom);
    const beginn = Date.now();
    takt = setInterval(() => {
      sek = Math.floor((Date.now() - beginn) / 1000);
      if (sek >= HOECHSTENS_S) stopp();
    }, 250);
    phase = "hoert";
  }

  /** Lautstärke des Mikrofons als wandernde Balken (Mittel der Ausschläge, etwas verstärkt) */
  function pegelMessen(quelle: MediaStream): void {
    kontext = new AudioContext();
    const analyse = kontext.createAnalyser();
    analyse.fftSize = 1024;
    kontext.createMediaStreamSource(quelle).connect(analyse);
    const werte = new Uint8Array(analyse.fftSize);
    let zuletzt = 0;
    const malen = (zeit: number): void => {
      bild = requestAnimationFrame(malen);
      if (zeit - zuletzt < 90) return;
      zuletzt = zeit;
      analyse.getByteTimeDomainData(werte);
      let summe = 0;
      for (const w of werte) summe += ((w - 128) / 128) ** 2;
      const staerke = Math.min(1, Math.sqrt(summe / werte.length) * 4);
      pegel = [...pegel.slice(1), Math.max(0.04, staerke)];
    };
    bild = requestAnimationFrame(malen);
  }

  function stopp(): void {
    if (phase !== "hoert" || !rekorder) return;
    phase = "setzt-um";
    clearInterval(takt);
    rekorder.stop();
    mikrofonAus();
  }

  async function umsetzen(): Promise<void> {
    if (!aufnahme) return;
    phase = "setzt-um";
    const s = new AbortController();
    steuerung = s;
    try {
      const text = (await sprechen(boardId, aufnahme, s.signal)).trim();
      if (s.signal.aborted) return;
      if (text) uebernehmen(text);
      else fehler("In der Aufnahme war nichts zu verstehen");
    } catch (f) {
      if (!s.signal.aborted) fehler(f instanceof Error ? f.message : "Umsetzen ging nicht");
    }
  }

  function fehler(text: string): void {
    grund = text;
    phase = "fehler";
    mikrofonAus();
  }

  function mikrofonAus(): void {
    cancelAnimationFrame(bild);
    strom?.getTracks().forEach((t) => t.stop());
    strom = null;
    void kontext?.close().catch(() => undefined);
    kontext = null;
  }

  function aufraeumen(): void {
    clearInterval(takt);
    steuerung?.abort();
    if (rekorder && rekorder.state !== "inactive") {
      rekorder.onstop = null;
      rekorder.stop();
    }
    mikrofonAus();
  }

  function nochmal(): void {
    grund = "";
    if (aufnahme) void umsetzen();
    else {
      phase = "startet";
      void starten();
    }
  }

  function ende(): void {
    aufraeumen();
    verwerfen();
  }
</script>

<section class="pw-tel-sprache" aria-label="Aufnahme">
  <div class="kopfzeile">
    {#if phase === "hoert"}
      <span class="zustand laeuft"><i class="fa-solid fa-microphone"></i>Aufnahme läuft</span>
    {:else if phase === "setzt-um"}
      <span class="zustand"><i class="fa-solid fa-spinner fa-spin-pulse"></i>Wird umgesetzt</span>
    {:else if phase === "fehler"}
      <span class="zustand"><i class="fa-solid fa-microphone-slash"></i>Geht nicht</span>
    {:else}
      <span class="zustand"><i class="fa-solid fa-microphone"></i>Mikrofon wird geöffnet</span>
    {/if}
    <span class="zahl dauer">{Math.floor(sek / 60)}:{String(sek % 60).padStart(2, "0")}</span>
  </div>
  <div class="pegel" aria-hidden="true">
    {#each pegel as p, i (i)}<span style="--h: {phase === 'hoert' ? p : 0.04}"></span>{/each}
  </div>
  <div class="mitschrift" aria-live="polite">
    {#if phase === "fehler"}{grund}
    {:else if phase === "setzt-um"}<span class="vorlaeufig">Die Transkription setzt die Aufnahme in Text um ...</span>
    {:else}<span class="vorlaeufig">Sprich einfach los. Der Text erscheint nach dem Stopp, höchstens zwei Minuten.</span>{/if}
  </div>
  <span class="quelle"><i class="fa-solid fa-wave-square"></i>Die Transkription setzt um; der erste Satz wird Titel, alles Beschreibung.</span>
  <div class="knoepfe">
    <button class="knopf ohne" onclick={ende}><i class="fa-solid fa-xmark"></i>Verwerfen</button>
    {#if phase === "fehler"}
      <button class="knopf haupt" onclick={nochmal}><i class="fa-solid fa-rotate-right"></i>Noch einmal</button>
    {:else}
      <button class="knopf haupt" disabled={phase !== "hoert"} onclick={stopp}><i class="fa-solid fa-stop"></i>Stopp und übernehmen</button>
    {/if}
  </div>
</section>
