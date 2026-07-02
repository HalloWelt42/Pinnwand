<script lang="ts">
  // Benachrichtigungs-Glocke: fremde Ereignisse auf den eigenen Karten (aus dem
  // Aktivitaetsprotokoll). Gelesen-Stand ist browser-lokal je Person; als Marker
  // dient der Zeitstempel des juengsten gesehenen Eintrags - so gibt es keinen
  // Versatz zwischen Browser- und Server-Uhr.
  import { ladeGlocke } from './api'
  import type { Aktivitaet } from './types'
  import { oeffneKarte } from './navigation.svelte'
  import { leseText, schreibeText } from './uiSpeicher'
  import { isoKurz } from './zeit'

  let { kuerzel }: { kuerzel: string | null } = $props()

  let eintraege = $state<Aktivitaet[]>([])
  let offen = $state(false)

  async function laden(): Promise<void> {
    if (!kuerzel) {
      eintraege = []
      return
    }
    try {
      const seit = leseText('pw_glocke_' + kuerzel) || null
      eintraege = await ladeGlocke(kuerzel, seit)
    } catch {
      eintraege = []
    }
  }
  $effect(() => {
    void kuerzel
    laden()
  })
  $effect(() => {
    const iv = setInterval(laden, 60_000)
    const beiFokus = () => laden()
    window.addEventListener('focus', beiFokus)
    return () => {
      clearInterval(iv)
      window.removeEventListener('focus', beiFokus)
    }
  })

  function alleGelesen(): void {
    if (!kuerzel || !eintraege.length) return
    schreibeText('pw_glocke_' + kuerzel, eintraege[0].zeit)
    eintraege = []
    offen = false
  }
  function oeffne(a: Aktivitaet): void {
    if (a.board_id) oeffneKarte(a.board_id, a.karte_id)
    offen = false
  }
  function wann(a: Aktivitaet): string {
    return `${isoKurz(a.zeit.slice(0, 10))} ${a.zeit.slice(11, 16)}`
  }
</script>

{#if kuerzel}
  <div class="glocke">
    <button class="gbtn" class:hat={eintraege.length > 0} aria-label="Benachrichtigungen"
      title="Benachrichtigungen: Neues auf deinen Karten" onclick={() => (offen = !offen)}>
      <i class="fa-solid fa-bell" aria-hidden="true"></i>
      {#if eintraege.length}<span class="badge">{eintraege.length > 99 ? '99+' : eintraege.length}</span>{/if}
    </button>
    {#if offen}
      <div class="back" role="presentation" onclick={() => (offen = false)}></div>
      <div class="panel" role="dialog" aria-label="Benachrichtigungen">
        <div class="pkopf">
          <span class="pt"><i class="fa-solid fa-bell" aria-hidden="true"></i> Neues auf deinen Karten</span>
          {#if eintraege.length}
            <button class="lesen" onclick={alleGelesen}>Alles gelesen</button>
          {/if}
        </div>
        {#if eintraege.length}
          <ul>
            {#each eintraege as a (a.id)}
              <li>
                <button class="zeile" onclick={() => oeffne(a)}>
                  <span class="kopfzeile">
                    {#if a.karte_schluessel}<span class="key">{a.karte_schluessel}</span>{/if}
                    <span class="titel">{a.karte_titel ?? a.karte_id}</span>
                    <span class="zeit">{wann(a)}</span>
                  </span>
                  <span class="text">{#if a.kuerzel}<b>{a.kuerzel}</b>{': '}{/if}{a.text}</span>
                </button>
              </li>
            {/each}
          </ul>
        {:else}
          <p class="leer">Nichts Neues.</p>
        {/if}
      </div>
    {/if}
  </div>
{/if}

<style>
  .glocke { position: relative; }
  .gbtn {
    position: relative; width: 32px; height: 32px; border: 1px solid var(--border);
    border-radius: var(--r-m); background: var(--surface-2); color: var(--text-3); font-size: 13px;
  }
  .gbtn:hover { color: var(--text-1); border-color: var(--border-2); }
  .gbtn.hat { color: var(--hl-primary-text); border-color: var(--hl-primary); }
  .badge {
    position: absolute; top: -6px; right: -6px; min-width: 16px; height: 16px; padding: 0 4px;
    border-radius: 999px; background: var(--gefahr); color: #fff; font-size: 9.5px; font-weight: 700;
    display: flex; align-items: center; justify-content: center;
  }
  .back { position: fixed; inset: 0; z-index: 49; }
  .panel {
    position: absolute; top: 38px; right: 0; z-index: 50; width: 340px; max-height: 60vh;
    display: flex; flex-direction: column;
    background: var(--surface-3); border: 1px solid var(--border-2); border-radius: var(--r-l);
    box-shadow: var(--schatten-pop); padding: 10px;
  }
  .pkopf { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 8px; }
  .pt { font-family: var(--font-display); font-size: 12px; color: var(--text-1); display: flex; align-items: center; gap: 7px; }
  .lesen { border: 1px solid var(--border); background: var(--surface-1); color: var(--text-2); border-radius: var(--r-m); padding: 4px 9px; font-size: 11.5px; }
  .lesen:hover { color: var(--hl-primary-text); border-color: var(--hl-primary); }
  ul { list-style: none; margin: 0; padding: 0; overflow-y: auto; display: flex; flex-direction: column; gap: 4px; }
  .zeile {
    width: 100%; display: flex; flex-direction: column; gap: 2px; text-align: left;
    background: var(--surface-2); border: 1px solid transparent; border-radius: var(--r-s);
    padding: 7px 9px; color: var(--text-1); font-size: 12px;
  }
  .zeile:hover { border-color: var(--border-2); background: var(--surface-1); }
  .kopfzeile { display: flex; align-items: center; gap: 7px; min-width: 0; }
  .key { font-family: var(--font-mono); font-size: 10px; color: var(--text-3); flex: none; }
  .titel { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-weight: 500; }
  .zeit { font-size: 10px; color: var(--text-3); flex: none; font-variant-numeric: tabular-nums; }
  .text { color: var(--text-2); font-size: 11.5px; }
  .text b { color: var(--hl-primary-text); font-weight: 600; }
  .leer { color: var(--text-3); font-size: 12px; margin: 2px 0 4px; }
</style>
