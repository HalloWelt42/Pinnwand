<script lang="ts">
  // App und Verbindungen: die Einstellungen der ganzen Pinnwand (für alle, die sie nutzen), aus dem Gerüst des Appkerns:
  // Verbindungen zu Kellerwolke, Leitstelle, Transkription und der App Vorlesen, KI an der Karte, Zugang, Sicherung.
  // Je Gruppe ein Bereich mit Hilfepunkt; geänderte Werte stehen im Entwurf, bis die Leiste unten sie speichert.
  import { EinstellungsZeile, einstellungen, einstellungenLaden, einstellungenSpeichern, einstellungenVerwerfen,
           Hilfepunkt } from "appkern-oberflaeche";
  import type { Feld } from "appkern-oberflaeche";
  import { melden } from "../../../daten/anwendung/meldung.svelte";

  /** Gruppen in ihrer Folge mit dem passenden Abschnitt der Hilfe; was keiner Gruppe angehört, steht unter "Weitere" */
  const GRUPPEN: [string, string, string, string][] = [
    ["Verbindungen", "fa-plug", "module", "verbindungen"],
    ["KI an der Karte", "fa-wand-magic-sparkles", "ki", "voraussetzungen"],
    ["Zugang", "fa-user-shield", "einstellungen", "app"],
    ["Sicherung", "fa-box-archive", "einstellungen", "sicherung"],
  ];
  let ladeFehler = $state("");
  $effect(() => {
    void einstellungenLaden().then(() => (ladeFehler = "")).catch(() => (ladeFehler = "Die Einstellungen ließen sich nicht laden; die Pinnwand antwortet gerade nicht."));
  });
  const gruppen = $derived.by(() => {
    const bekannt = GRUPPEN.map(([name]) => name);
    const weitere = einstellungen.felder.filter((f) => !bekannt.includes(f.gruppe ?? ""));
    const liste: { name: string; symbol: string; thema: string; abschnitt: string; felder: Feld[] }[] = GRUPPEN.map(([name, symbol, thema, abschnitt]) => ({
      name, symbol, thema, abschnitt, felder: einstellungen.felder.filter((f) => f.gruppe === name),
    }));
    if (weitere.length) liste.push({ name: "Weitere", symbol: "fa-sliders", thema: "einstellungen", abschnitt: "app", felder: weitere });
    return liste.filter((g) => g.felder.length);
  });
  const offen = $derived(Object.keys(einstellungen.entwurf).length);

  async function speichern(): Promise<void> {
    try {
      const n = await einstellungenSpeichern();
      melden(`${n} ${n === 1 ? "Einstellung" : "Einstellungen"} gespeichert`);
    } catch (f) {
      melden(`Nicht gespeichert: ${f instanceof Error ? f.message : "die Pinnwand antwortet nicht"}`);
    }
  }
</script>

<div class="rollfeld">
  <div class="pw-verwaltung-flaeche">
    <p class="pw-verwaltung-satz"><i class="fa-solid fa-circle-info"></i>Diese Einstellungen gelten für die ganze Pinnwand und alle, die sie nutzen.
      Anmelden können sich nur du und die Konten unter Zugang, Weitere Konten.<Hilfepunkt thema="einstellungen" abschnitt="app" /></p>
    {#if ladeFehler}<div class="hinweis warnung"><i class="fa-solid fa-triangle-exclamation"></i><div>{ladeFehler}</div></div>{/if}
    {#each gruppen as g (g.name)}
      <section class="bereich" aria-label={g.name}>
        <h2 class="etikett pw-app-gruppe"><i class="fa-solid {g.symbol}"></i>{g.name}<Hilfepunkt thema={g.thema} abschnitt={g.abschnitt} titel="Hilfe zu {g.name}" /></h2>
        {#each g.felder as f (f.name)}<EinstellungsZeile feld={f} {melden} />{/each}
      </section>
    {/each}
  </div>
  {#if offen}
    <div class="pw-app-leiste" role="status">
      <span><b>{offen}</b> {offen === 1 ? "Änderung" : "Änderungen"} noch nicht gespeichert</span>
      <button class="knopf ohne" onclick={einstellungenVerwerfen}>Verwerfen</button>
      <button class="knopf haupt" onclick={speichern}><i class="fa-solid fa-floppy-disk"></i>Speichern</button>
    </div>
  {/if}
</div>
