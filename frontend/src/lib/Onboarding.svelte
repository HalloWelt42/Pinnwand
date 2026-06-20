<script lang="ts">
  let { onFertig, onGeheZu }: { onFertig: () => void; onGeheZu: (ansicht: string) => void } = $props()

  interface Schritt {
    titel: string
    text: string
    ansicht?: string
  }

  const SCHRITTE: Schritt[] = [
    { titel: 'Willkommen bei Pinnwand', text: 'Eine lokale, modulare Plattform für Aufgaben, Zeiten und Planung. Diese kurze Einführung zeigt die wichtigsten Bereiche. Du kannst sie jederzeit überspringen.' },
    { titel: 'Board und Spalten', text: 'Im Board legst du Aufgaben an und verschiebst sie per Drag-and-drop. Markiere im Spalten-Menü eine Spalte als Erledigt-Spalte - das nutzen Auswertung und Schnell-Erledigt.', ansicht: 'board' },
    { titel: 'Personen und Wochenstunden', text: 'Unter Planung legst du Personen mit ihrem Wochen-Soll je Wochentag an, trägst Urlaub ein (auch halbe Tage) und importierst Feiertage (Vorschau vor Übernahme).', ansicht: 'planung' },
    { titel: 'Wiederkehrende Termine', text: 'Unter Serien richtest du wiederkehrende Termine/Aufgaben ein (z.B. eine wöchentliche Telefonkonferenz). Sie werden automatisch als Karten mit Fälligkeit und Soll vorgebucht.', ansicht: 'serien' },
    { titel: 'Auswertung und Berichte', text: 'Zeiten zeigt den Wochen-Stundenzettel mit Soll/Ist. Unter Berichte erzeugst du PDF/CSV/Markdown und legst sie als Nachweis im Archiv ab.', ansicht: 'berichte' },
    { titel: 'KI ist optional', text: 'Vorlesen, Spracheingabe, semantische Suche und Transkriptionen sind optional. Ohne die Dienste läuft alles weiter. Der Dienste-Status unten in der Seitenleiste zeigt, was erreichbar ist. Hilfe findest du jederzeit über das Fragezeichen.' },
  ]

  let i = $state(0)
  const aktuell = $derived(SCHRITTE[i])
  const letzter = $derived(i === SCHRITTE.length - 1)

  function weiter(): void {
    if (letzter) onFertig()
    else i += 1
  }
  function gehe(): void {
    if (aktuell.ansicht) onGeheZu(aktuell.ansicht)
  }
</script>

<div class="overlay" role="presentation">
  <div class="karte" role="dialog" aria-label="Einführung">
    <div class="punkte">
      {#each SCHRITTE as _, n (n)}<span class="pkt" class:an={n === i}></span>{/each}
    </div>
    <h2>{aktuell.titel}</h2>
    <p>{aktuell.text}</p>
    <div class="fuss">
      <button class="text" onclick={onFertig}>Überspringen</button>
      <div class="rechts">
        {#if aktuell.ansicht}<button class="geist" onclick={gehe}>Dorthin</button>{/if}
        {#if i > 0}<button class="geist" onclick={() => (i -= 1)}>Zurück</button>{/if}
        <button class="primaer" onclick={weiter}>{letzter ? 'Los geht es' : 'Weiter'}</button>
      </div>
    </div>
  </div>
</div>

<style>
  .overlay { position: fixed; inset: 0; z-index: 90; background: rgba(0, 0, 0, 0.5); display: flex; align-items: center; justify-content: center; }
  .karte { width: 460px; max-width: 92vw; background: var(--surface-col); border: 1px solid var(--border-2); border-radius: var(--r-xl); padding: 22px; box-shadow: var(--schatten-pop); }
  .punkte { display: flex; gap: 5px; margin-bottom: 14px; }
  .pkt { width: 20px; height: 4px; border-radius: 2px; background: var(--border-2); }
  .pkt.an { background: var(--hl-primary); }
  h2 { margin: 0 0 8px; font-family: var(--font-display); font-size: 18px; color: var(--text-1); }
  p { margin: 0 0 20px; font-size: 13.5px; line-height: 1.6; color: var(--text-2); }
  .fuss { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
  .rechts { display: flex; gap: 8px; }
  button { border-radius: var(--r-m); padding: 8px 14px; font-size: 12.5px; border: 1px solid var(--border); }
  .text { border: none; background: transparent; color: var(--text-3); }
  .geist { background: transparent; color: var(--text-2); border-color: var(--border-2); }
  .primaer { background: var(--hl-primary); color: var(--hl-on-primary); border-color: transparent; font-weight: 500; }
</style>
