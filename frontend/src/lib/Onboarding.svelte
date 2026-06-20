<script lang="ts">
  import { erstelleMappe, erstellePerson, ladeLaender, feiertageUebernehmen, type Region } from './api'

  let { onFertig, onGeheZu }: { onFertig: () => void; onGeheZu: (ansicht: string) => void } = $props()

  interface Schritt {
    id: string
    titel: string
    text: string
    ansicht?: string
  }

  const SCHRITTE: Schritt[] = [
    { id: 'willkommen', titel: 'Willkommen bei Pinnwand', text: 'Eine lokale, modulare Plattform für Aufgaben, Zeiten und Planung. Diese kurze Einrichtung legt direkt die Grundlagen an. Du kannst sie jederzeit überspringen und alles später ändern.' },
    { id: 'mappe', titel: 'Projektmappe', text: 'Eine Mappe bündelt zusammengehörige Boards. Lege optional gleich eine eigene Mappe an (sonst nutzt du die vorhandene).' },
    { id: 'personen', titel: 'Personen und Wochenstunden', text: 'Lege die Personen an, deren Zeiten du planst. Das Wochen-Soll je Wochentag stellst du anschließend unter Planung ein.', ansicht: 'planung' },
    { id: 'feiertage', titel: 'Feiertage und Region', text: 'Importiere die Feiertage deiner Region - sie werden im Kalender berücksichtigt und reduzieren das Soll.', ansicht: 'planung' },
    { id: 'serien', titel: 'Wiederkehrende Termine', text: 'Unter Serien richtest du wiederkehrende Termine/Aufgaben ein (z.B. eine wöchentliche Telefonkonferenz). Sie werden automatisch als Karten mit Fälligkeit und Soll vorgebucht.', ansicht: 'serien' },
    { id: 'token', titel: 'Agenten-Zugriff (optional)', text: 'KI-Werkzeuge können über die Agenten-API das Board befüllen und lesen. Ein Zugriffs-Token legst du bei Bedarf in den Einstellungen an (dort brauchst du dein Admin-Token).', ansicht: 'einstellungen' },
    { id: 'ki', titel: 'KI ist optional', text: 'Vorlesen, Spracheingabe, semantische Suche und Transkriptionen sind optional. Ohne die Dienste läuft alles weiter. Der Dienste-Status unten in der Seitenleiste zeigt, was erreichbar ist. Hilfe findest du jederzeit über das Fragezeichen.' },
  ]

  let i = $state(0)
  const aktuell = $derived(SCHRITTE[i])
  const letzter = $derived(i === SCHRITTE.length - 1)

  // Mappe
  let mappeName = $state('')
  let mappeMeldung = $state('')
  async function mappeAnlegen(): Promise<void> {
    const t = mappeName.trim()
    if (!t) return
    try {
      await erstelleMappe(t)
      mappeMeldung = `Mappe "${t}" angelegt.`
      mappeName = ''
    } catch {
      mappeMeldung = 'Anlegen fehlgeschlagen.'
    }
  }

  // Personen
  let pName = $state('')
  let pKuerzel = $state('')
  let angelegtePersonen = $state<string[]>([])
  async function personHinzufuegen(): Promise<void> {
    const n = pName.trim()
    if (!n) return
    try {
      await erstellePerson({ name: n, kuerzel: pKuerzel.trim() || null })
      angelegtePersonen = [...angelegtePersonen, n]
      pName = ''
      pKuerzel = ''
    } catch { /* still */ }
  }

  // Feiertage
  let laender = $state<Record<string, Region[]>>({})
  let ftLand = $state('DE')
  let ftRegion = $state('')
  let ftJahr = $state(new Date().getFullYear())
  let ftMeldung = $state('')
  const regionen = $derived(laender[ftLand] ?? [])
  $effect(() => {
    ladeLaender().then((d) => (laender = d.laender)).catch(() => {})
  })
  async function feiertageImportieren(): Promise<void> {
    try {
      const r = await feiertageUebernehmen(ftLand, ftRegion || null, ftJahr)
      ftMeldung = `${r.uebernommen} Feiertage für ${ftJahr} übernommen.`
    } catch {
      ftMeldung = 'Import fehlgeschlagen.'
    }
  }

  function weiter(): void {
    if (letzter) onFertig()
    else i += 1
  }
  function gehe(): void {
    if (aktuell.ansicht) onGeheZu(aktuell.ansicht)
  }
</script>

<div class="overlay" role="presentation">
  <div class="karte" role="dialog" aria-label="Einrichtung">
    <div class="punkte">
      {#each SCHRITTE as _, n (n)}<span class="pkt" class:an={n === i}></span>{/each}
    </div>
    <h2>{aktuell.titel}</h2>
    <p>{aktuell.text}</p>

    {#if aktuell.id === 'mappe'}
      <div class="form">
        <input placeholder="Mappenname (z.B. Kundenprojekt)" bind:value={mappeName} onkeydown={(e) => { if (e.key === 'Enter') mappeAnlegen() }} />
        <button class="geist" onclick={mappeAnlegen}>Anlegen</button>
      </div>
      {#if mappeMeldung}<p class="ok">{mappeMeldung}</p>{/if}
    {:else if aktuell.id === 'personen'}
      <div class="form">
        <input placeholder="Name" bind:value={pName} onkeydown={(e) => { if (e.key === 'Enter') personHinzufuegen() }} />
        <input class="kz" placeholder="Kürzel" bind:value={pKuerzel} onkeydown={(e) => { if (e.key === 'Enter') personHinzufuegen() }} />
        <button class="geist" onclick={personHinzufuegen}>Hinzufügen</button>
      </div>
      {#if angelegtePersonen.length}<p class="ok">Angelegt: {angelegtePersonen.join(', ')}</p>{/if}
    {:else if aktuell.id === 'feiertage'}
      <div class="form">
        <select bind:value={ftLand}>
          {#each Object.keys(laender) as l (l)}<option value={l}>{l}</option>{/each}
        </select>
        <select bind:value={ftRegion}>
          <option value="">ganzes Land</option>
          {#each regionen as r (r.code)}<option value={r.code}>{r.name}</option>{/each}
        </select>
        <input class="jahr" type="number" min="2000" max="2100" bind:value={ftJahr} />
        <button class="geist" onclick={feiertageImportieren}>Importieren</button>
      </div>
      {#if ftMeldung}<p class="ok">{ftMeldung}</p>{/if}
    {/if}

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
  .karte { width: 480px; max-width: 92vw; background: var(--surface-col); border: 1px solid var(--border-2); border-radius: var(--r-xl); padding: 22px; box-shadow: var(--schatten-pop); }
  .punkte { display: flex; gap: 5px; margin-bottom: 14px; }
  .pkt { width: 18px; height: 4px; border-radius: 2px; background: var(--border-2); }
  .pkt.an { background: var(--hl-primary); }
  h2 { margin: 0 0 8px; font-family: var(--font-display); font-size: 18px; color: var(--text-1); }
  p { margin: 0 0 16px; font-size: 13.5px; line-height: 1.6; color: var(--text-2); }
  .form { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 10px; }
  .form input, .form select {
    flex: 1; min-width: 0; border: 1px solid var(--border); background: var(--surface-2); color: var(--text-1);
    border-radius: var(--r-m); padding: 8px 10px; font-size: 12.5px;
  }
  .form .kz { flex: 0 0 90px; }
  .form .jahr { flex: 0 0 90px; }
  .ok { color: var(--ok); font-size: 12px; margin: 0 0 16px; }
  .fuss { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-top: 6px; }
  .rechts { display: flex; gap: 8px; }
  button { border-radius: var(--r-m); padding: 8px 14px; font-size: 12.5px; border: 1px solid var(--border); }
  .text { border: none; background: transparent; color: var(--text-3); }
  .geist { background: transparent; color: var(--text-2); border-color: var(--border-2); }
  .primaer { background: var(--hl-primary); color: var(--hl-on-primary); border-color: transparent; font-weight: 500; }
</style>
