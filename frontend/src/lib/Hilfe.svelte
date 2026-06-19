<script lang="ts">
  let { onSchliessen }: { onSchliessen: () => void } = $props()

  interface Thema {
    titel: string
    text: string
  }

  const THEMEN: Thema[] = [
    { titel: 'Heute (Was steht an)', text: 'Startansicht mit ueberfaelligen, heute und diese Woche faelligen, laufenden und liegengebliebenen Aufgaben. Klick oeffnet die Karte. Vorlesen liest den Tagesueberblick.' },
    { titel: 'Board', text: 'Kanban mit Spalten und Karten. Karten per Drag-and-drop verschieben, Spalten einklappen. Eine Spalte kann als Erledigt-Spalte markiert werden (Kebab-Menue).' },
    { titel: 'Karte bearbeiten', text: 'Karte anklicken oeffnet die Detailansicht. Beschreibung ganz oben als Markdown (Split-Editor, Vollbild, Auto-Speichern). Zeiterfassung mit Start/Pause, Schaetzung als Soll. Labels, Checkliste, Kommentare.' },
    { titel: 'Zeiten', text: 'Wochen-Stundenzettel mit Soll/Ist je Karte. Zeiten nachtragen und korrigieren (Dauer als 1:30 oder 1,5).' },
    { titel: 'Kalender', text: 'Jahres-Heatmap und Monat. Wochenenden, Feiertage (rot) und Urlaub (amber, Person waehlbar) sind eingefaerbt.' },
    { titel: 'Flow', text: 'Abhaengigkeitsdiagramm: ordnet die Karten automatisch nach Reihenfolge an (links nach rechts) und hebt den kritischen Pfad hervor (laengste Kette, gewichtet nach Schaetzung). Status je Karte: startklar, blockiert oder erledigt. Zyklen werden gewarnt. Abhaengigkeiten legst du im Karten-Detail unter "Abhaengigkeiten" an. Klick auf eine Karte oeffnet sie.' },
    { titel: 'Serien', text: 'Wiederkehrende Termine/Aufgaben (taeglich/woechentlich/monatlich, Wochentage, Uhrzeit, Dauer). Werden automatisch als Karten vorgebucht.' },
    { titel: 'Suche', text: 'Freitextsuche ueber alle Karteninhalte. Mit lokalem Whisper auch per Mikrofon. Mit Qdrant + Embeddings zusaetzlich semantisch.' },
    { titel: 'Transkripte', text: 'Transkriptionen aus dem Sprachdienst durchsuchen, anzeigen, vorlesen und das Original-Audio abspielen.' },
    { titel: 'Planung', text: 'Personen mit Wochen-Soll je Wochentag, Urlaub (auch halbe Tage) und Feiertags-Import (Land/Region) mit Vorschau vor Uebernahme.' },
    { titel: 'Berichte', text: 'Stundenzettel, Soll/Ist, Kapazitaet und Zeit je Person/Karte als PDF, CSV oder Markdown. Erzeugte Berichte landen unveraenderlich im Archiv.' },
    { titel: 'Einstellungen und Sicherung', text: 'Unter Einstellungen erstellst du Snapshots (Datenbank, Berichts-Archiv, Konfigurationsvorlage). Beim Start wird hoechstens taeglich automatisch gesichert. Vor jeder Wiederherstellung wird der aktuelle Stand gesichert; die Wiederherstellung zeigt vorher eine Vorschau mit den Unterschieden.' },
    { titel: 'KI ist optional', text: 'LLM, Vorlesen, Spracheingabe und semantische Suche sind optional. Ohne die Dienste laeuft alles weiter; der Dienste-Status unten in der Seitenleiste zeigt, was erreichbar ist.' },
    { titel: 'Agenten-API', text: 'Unter /api/agent koennen KI-Werkzeuge Zeiten buchen, Aufgaben anlegen/erledigen und suchen (Token mit Scopes, Audit-Log, Trockenlauf). Zusaetzlich MCP-Server und OpenAI-Tools.' },
  ]

  let frage = $state('')
  const treffer = $derived(
    THEMEN.filter((t) => {
      const q = frage.trim().toLowerCase()
      return !q || t.titel.toLowerCase().includes(q) || t.text.toLowerCase().includes(q)
    }),
  )
</script>

<svelte:window onkeydown={(e) => { if (e.key === 'Escape') onSchliessen() }} />
<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
<div class="overlay" role="presentation" onclick={onSchliessen}>
  <!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
  <div class="panel" role="dialog" aria-label="Hilfe" tabindex="-1" onclick={(e) => e.stopPropagation()}>
    <header>
      <h2><i class="fa-solid fa-circle-question" aria-hidden="true"></i> Hilfe</h2>
      <button class="x" aria-label="Schliessen" onclick={onSchliessen}><i class="fa-solid fa-xmark" aria-hidden="true"></i></button>
    </header>
    <input class="suche" placeholder="Hilfe durchsuchen ..." bind:value={frage} aria-label="Hilfe durchsuchen" />
    <div class="liste">
      {#each treffer as t (t.titel)}
        <article><h3>{t.titel}</h3><p>{t.text}</p></article>
      {/each}
      {#if !treffer.length}<p class="leer">Nichts gefunden.</p>{/if}
    </div>
  </div>
</div>

<style>
  .overlay { position: fixed; inset: 0; z-index: 80; background: rgba(0, 0, 0, 0.4); display: flex; justify-content: flex-end; }
  .panel { width: 460px; max-width: 92vw; height: 100%; background: var(--surface-col); border-left: 1px solid var(--border); display: flex; flex-direction: column; }
  header { display: flex; align-items: center; justify-content: space-between; padding: 14px 16px; border-bottom: 1px solid var(--border); }
  header h2 { margin: 0; font-family: var(--font-display); font-size: 15px; color: var(--text-1); display: flex; align-items: center; gap: 8px; }
  .x { border: none; background: transparent; color: var(--text-3); font-size: 15px; }
  .suche { margin: 12px 16px; border: 1px solid var(--border-2); background: var(--surface-2); color: var(--text-1); border-radius: var(--r-m); padding: 9px 11px; font-size: 13px; }
  .liste { overflow-y: auto; padding: 0 16px 16px; display: flex; flex-direction: column; gap: 12px; }
  article h3 { margin: 0 0 3px; font-size: 13px; color: var(--hl-primary-text); font-family: var(--font-display); }
  article p { margin: 0; font-size: 12.5px; line-height: 1.55; color: var(--text-2); }
  .leer { color: var(--text-3); font-size: 12.5px; }
</style>
