<script lang="ts">
  // Transkripte an der Karte (Modul Transkripte, M-112 und M-113): je Stelle Name, Zeit, Sprecher und Text aus dem
  // Transkript; Abspielen ab der Stelle (ein Spieler je Karte, ein zweiter Klick hält an), "In der Transkription
  // öffnen", eine Notiz (speichert beim Verlassen, Escape verwirft) und mit KI an der Karte ein Vorschlag dafür; lösen
  // mit Rückgängig. Das Suchfeld sucht wie die Transkription (kurz nach der letzten Taste) und verknüpft eine
  // Fundstelle oder das ganze Transkript. Hören und suchen kann nur, wer die Transkription selbst nutzen darf.
  import { Hilfepunkt, Suchfeld } from "appkern-oberflaeche";
  import { notizHolen, Vorschlagslauf } from "../daten/anwendung/ki.svelte";
  import { melden } from "../daten/anwendung/meldung.svelte";
  import {
    inTranskription, loesen, notizSetzen, stelleText, suchen, tonAdresse, verknuepfen, type Trefferseite,
  } from "../daten/anwendung/transkripte.svelte";
  import type { Karte, TranskriptMarke } from "../modell";
  import { verlassen, verwerfbar, verwerfen } from "../teile/verwerfen";
  import Vorschlag from "./Vorschlag.svelte";
  import { enter } from "../teile/taste";

  let { karte, schreiben, ki = false }: {
    karte: Karte;
    schreiben: boolean;
    /** Vorschläge der KI gehen in diesem Board */
    ki?: boolean;
  } = $props();

  /** so lange nach der letzten Taste wird gesucht (wie in der alten App) */
  const WARTEN_MS = 220;

  // ═══ Suchen und verknüpfen ═══════════════════════════════════════════════════════════════════════════════════════

  let text = $state("");
  let seite = $state<Trefferseite | null>(null);
  let sucht = $state(false);
  let suchFehler = $state("");
  let uhr: ReturnType<typeof setTimeout> | undefined;
  let steuerung: AbortController | null = null;

  function eingabe(): void {
    clearTimeout(uhr);
    steuerung?.abort();
    const t = text.trim();
    if (!t) {
      seite = null;
      suchFehler = "";
      sucht = false;
      return;
    }
    uhr = setTimeout(() => void holen(t), WARTEN_MS);
  }

  async function holen(t: string): Promise<void> {
    const s = new AbortController();
    steuerung = s;
    sucht = true;
    try {
      const ergebnis = await suchen(karte.id, t, s.signal);
      if (!s.signal.aborted) {
        seite = ergebnis;
        suchFehler = "";
      }
    } catch (f) {
      if (!s.signal.aborted) {
        seite = null;
        suchFehler = f instanceof Error ? f.message : "Die Suche ging nicht";
      }
    } finally {
      if (steuerung === s) sucht = false;
    }
  }

  async function anhaengen(transkript: string, sekunde: number | null): Promise<void> {
    if (await verknuepfen(karte.id, transkript, sekunde)) {
      text = "";
      seite = null;
    }
  }

  // ═══ Abspielen ab der Stelle ═════════════════════════════════════════════════════════════════════════════════════

  let spieler: HTMLAudioElement;
  /** welche Stelle gerade spielt */
  let spielt = $state<string | null>(null);

  function abspielen(m: TranskriptMarke): void {
    if (spielt === m.id) {
      spieler.pause();
      spielt = null;
      return;
    }
    spielt = m.id;
    // die Stelle als Zeitangabe der Adresse: so springt der Spieler selbst, auch auf dem Telefon, im Tippen gestartet
    spieler.src = `${tonAdresse(karte.id, m.id)}${m.sekunde != null ? `#t=${m.sekunde}` : ""}`;
    void spieler.play().catch(() => undefined);
  }

  /** Lädt der Ton nicht, fragt ein kleiner Bereich nach dem Grund (etwa: die Transkription lässt dich nicht zu) */
  async function tonFehler(): Promise<void> {
    const m = karte.transkripte.find((x) => x.id === spielt);
    spielt = null;
    if (!m) return;
    try {
      const antwort = await fetch(tonAdresse(karte.id, m.id), { headers: { Range: "bytes=0-0" } });
      const grund = antwort.ok ? "" : ((await antwort.json().catch(() => ({}))) as { detail?: string }).detail;
      melden(grund ? `Abspielen ging nicht: ${grund}` : "Abspielen ging nicht: der Browser kann diesen Ton nicht abspielen");
    } catch {
      melden("Abspielen ging nicht: die Pinnwand ist nicht erreichbar");
    }
  }

  // ═══ Notiz ═══════════════════════════════════════════════════════════════════════════════════════════════════════

  function notizAendern(m: TranskriptMarke, feld: HTMLInputElement): void {
    const neu = feld.value.trim();
    if (neu !== (m.notiz ?? "")) void notizSetzen(karte.id, m.id, neu);
  }

  const vorschlag = new Vorschlagslauf<{ text: string }>();
  /** zu welcher Stelle der Vorschlag gehört */
  let vorschlagFuer = $state<string | null>(null);
  $effect(() => () => {
    vorschlag.schliessen();
    steuerung?.abort();
    clearTimeout(uhr);
  });

  function notizVorschlagen(m: TranskriptMarke): void {
    if (vorschlagFuer === m.id && vorschlag.offen) {
      vorschlag.schliessen();
      return;
    }
    vorschlagFuer = m.id;
    void vorschlag.holen(notizHolen(karte.id, m.id));
  }

  async function vorschlagUebernehmen(m: TranskriptMarke, notiz: string): Promise<void> {
    if (await notizSetzen(karte.id, m.id, notiz)) vorschlag.schliessen();
  }
</script>

<section class="pw-abschnitt" aria-label="Transkripte">
  <div class="etikett">Transkripte<Hilfepunkt thema="transkripte" abschnitt="verknuepfen" /> {#if karte.transkripte.length}<span class="zaehler">{karte.transkripte.length}</span>{/if}</div>
  <audio bind:this={spieler} preload="none" onended={() => (spielt = null)} onerror={() => spielt && void tonFehler()}></audio>
  {#each karte.transkripte as m (m.id)}
    <div class="pw-transkript" class:spielt={spielt === m.id}>
      <div class="pw-anhang">
        <i class="fa-solid fa-wave-square"></i>
        <span class="name" title={m.name}>{m.name}</span>
        <span class="meta">{m.sekunde != null ? `bei ${stelleText(m.sekunde)}` : "ganzes Transkript"}</span>
        <button class="knopf ohne symbol klein" title={spielt === m.id ? "Anhalten" : m.sekunde != null ? "Abspielen ab der Stelle" : "Abspielen"}
                aria-pressed={spielt === m.id} onclick={() => abspielen(m)}><i class="fa-solid {spielt === m.id ? 'fa-pause' : 'fa-play'}"></i></button>
        <a class="knopf ohne symbol klein" href={inTranskription(m)} target="_blank" rel="noopener" title="In der Transkription öffnen"><i class="fa-solid fa-arrow-up-right-from-square"></i></a>
        {#if schreiben}
          <button class="knopf ohne symbol klein" title="Lösen (Rückgängig möglich)" onclick={() => loesen(karte.id, m.id)}><i class="fa-solid fa-xmark"></i></button>
        {/if}
      </div>
      {#if m.text}
        <div class="pw-transkript-text">{#if m.sprecher}<span class="sprecher">{m.sprecher}:</span>{/if} "{m.text}"</div>
      {/if}
      {#if schreiben}
        <div class="pw-transkript-notiz">
          <input class="eingabe" value={m.notiz ?? ""} placeholder="Notiz zur Stelle" aria-label="Notiz zu {m.name}" use:verwerfbar
                 onchange={(e) => notizAendern(m, e.currentTarget)} onkeydown={(e) => { if (enter(e)) verlassen(e.currentTarget); }} />
          {#if ki}
            <button class="knopf ohne symbol klein" title="Notiz vorschlagen (über die Leitstelle)" aria-pressed={vorschlagFuer === m.id && vorschlag.offen}
                    onclick={() => notizVorschlagen(m)}><i class="fa-solid fa-wand-magic-sparkles"></i></button>
          {/if}
        </div>
      {:else if m.notiz}
        <div class="pw-transkript-text">{m.notiz}</div>
      {/if}
      {#if vorschlagFuer === m.id && vorschlag.offen}
        <Vorschlag titel="Vorschlag: Notiz aus dem Gespräch um die Stelle" lauf={vorschlag} nochmal={() => notizVorschlagen(m)}>
          {#snippet children(v)}<div class="pw-vorschlag-text">{v.text}</div>{/snippet}
          {#snippet knoepfe(v)}<button class="knopf klein" onclick={() => vorschlagUebernehmen(m, v.text)}>Als Notiz übernehmen</button>{/snippet}
        </Vorschlag>
      {/if}
    </div>
  {/each}

  {#if schreiben}
    <Suchfeld klasse="pw-detail-suche" symbol={sucht ? "fa-spinner fa-spin-pulse" : "fa-wave-square"} placeholder="In Transkripten suchen und eine Stelle verknüpfen"
              aria-label="In Transkripten suchen" bind:wert={text} oninput={eingabe} {@attach verwerfen} />
    {#if suchFehler}
      <div class="hinweis warnung"><i class="fa-solid fa-triangle-exclamation"></i><div>{suchFehler}</div></div>
    {:else if seite}
      <div class="pw-transkript-treffer" aria-label="Treffer">
        {#each seite.treffer as t (t.transkript)}
          <div class="kopf">
            <span class="name" title={t.name}>{t.name}</span><span class="meta">{stelleText(t.dauerS)}</span>
            <button class="knopf ohne klein" onclick={() => anhaengen(t.transkript, null)}>Ganzes verknüpfen</button>
          </div>
          {#each t.fundstellen as f, i (i)}
            <button class="fundstelle" title="Diese Stelle verknüpfen" onclick={() => anhaengen(t.transkript, f.zeit)}>
              <span class="zeit">{stelleText(f.zeit)}</span><span class="ausschnitt">{f.ausschnitt}</span></button>
          {/each}
        {:else}
          <div class="pw-vorschlag-text">Kein Transkript passt zu "{text.trim()}".</div>
        {/each}
      </div>
    {/if}
  {/if}
</section>
