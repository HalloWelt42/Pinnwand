<script lang="ts">
  import type { Board, Projektmappe } from './types'
  import { abmelden } from './api'
  import { auth } from './auth.svelte'
  import { theme, wechsleTheme } from './theme/theme.svelte'
  import { VERSION } from './version'
  import DiensteStatus from './DiensteStatus.svelte'

  // Schmaler Ausschnitt einer Ansicht - mehr braucht die Navigation nicht.
  interface AnsichtsEintrag {
    id: string
    titel: string
    icon: string
  }

  interface Props {
    // Sichtbare Ansichten (bereits nach Rolle gefiltert).
    ansichten: AnsichtsEintrag[]
    aktiveAnsicht: string
    // Ob die aktive Ansicht boardgebunden ist (steuert die Mappen-Navigation).
    boardgebunden: boolean
    mappen: Projektmappe[]
    aktiveMappe: Projektmappe | null
    boards: Board[]
    aktivesBoard: Board | null
    railEin: boolean
    railBreite: number
    // App-weite Aktionen: die App führt die Änderung aus (Server + Zustand),
    // die Seitenleiste kümmert sich nur um ihre Eingabe-/Bestätigungsdialoge.
    onWaehleMappe: (m: Projektmappe) => Promise<void>
    onMappeErstellen: (titel: string) => Promise<Projektmappe>
    onMappeUmbenennen: (id: string, titel: string) => Promise<void>
    onMappeLoeschen: (id: string) => Promise<void>
    onBoardErstellen: (titel: string) => Promise<void>
    onBoardUmbenennen: (id: string, titel: string) => Promise<void>
    onBoardLoeschen: (id: string) => Promise<void>
    onMitglieder: (m: Projektmappe) => void
    onDokumente: () => void
    onHilfe: () => void
  }

  let {
    ansichten,
    aktiveAnsicht = $bindable(),
    boardgebunden,
    mappen,
    aktiveMappe,
    boards,
    aktivesBoard = $bindable(),
    railEin = $bindable(),
    railBreite,
    onWaehleMappe,
    onMappeErstellen,
    onMappeUmbenennen,
    onMappeLoeschen,
    onBoardErstellen,
    onBoardUmbenennen,
    onBoardLoeschen,
    onMitglieder,
    onDokumente,
    onHilfe,
  }: Props = $props()

  // Pflege-Zustand der Seitenleiste: Umbenennen-/Löschen-Dialoge und die
  // Neu-Anlegen-Felder leben nur hier.
  let bearbeiteBoardId = $state<string | null>(null)
  let loescheBoardId = $state<string | null>(null)
  let boardEntwurf = $state('')
  let neuesBoard = $state(false)
  let neuerBoardTitel = $state('')
  let bearbeiteMappeId = $state<string | null>(null)
  let loescheMappeId = $state<string | null>(null)
  let mappeEntwurf = $state('')
  let neueMappe = $state(false)
  let neuerMappeTitel = $state('')

  // Beim Mappenwechsel offene Board-Pflege schließen (sie gehört zur alten Mappe).
  function boardPflegeZuruecksetzen(): void {
    bearbeiteBoardId = null
    loescheBoardId = null
    neuesBoard = false
  }

  async function waehleMappe(m: Projektmappe): Promise<void> {
    boardPflegeZuruecksetzen()
    await onWaehleMappe(m)
  }

  async function neueMappeErstellen(): Promise<void> {
    const t = neuerMappeTitel.trim()
    if (!t) return
    const ziel = await onMappeErstellen(t)
    neuerMappeTitel = ''
    neueMappe = false
    boardPflegeZuruecksetzen()
    await onWaehleMappe(ziel)
  }

  async function mappeSpeichern(id: string): Promise<void> {
    const t = mappeEntwurf.trim()
    if (t) await onMappeUmbenennen(id, t)
    bearbeiteMappeId = null
  }

  async function mappeLoeschenBestaetigt(id: string): Promise<void> {
    const warAktiv = aktiveMappe?.id === id
    // Dialog auch bei Server-Ablehnung schliessen (Meldung kommt zentral als Toast).
    try {
      await onMappeLoeschen(id)
      if (warAktiv) boardPflegeZuruecksetzen()
    } finally {
      loescheMappeId = null
    }
  }

  async function neuesBoardErstellen(): Promise<void> {
    const t = neuerBoardTitel.trim()
    if (!t || !aktiveMappe) return
    await onBoardErstellen(t)
    neuerBoardTitel = ''
    neuesBoard = false
  }

  async function boardSpeichern(id: string): Promise<void> {
    const t = boardEntwurf.trim()
    if (t) await onBoardUmbenennen(id, t)
    bearbeiteBoardId = null
  }

  async function boardLoeschenBestaetigt(id: string): Promise<void> {
    // Dialog auch bei Server-Ablehnung schliessen (Meldung kommt zentral als Toast).
    try {
      await onBoardLoeschen(id)
    } finally {
      loescheBoardId = null
    }
  }

  async function abmeldenUndNeu(): Promise<void> {
    await abmelden()
    location.reload()
  }
</script>

<aside class="rail" class:zu={!railEin} style={railEin ? `flex-basis:${railBreite}px` : ''}>
  <div class="marke">
    <img class="logo" src="/favicon.svg" alt="" />
    <span class="name">Pinnwand <span class="ver">v{VERSION}</span></span>
    <button class="railtog" aria-label="Seitenleiste ein- oder ausklappen" onclick={() => (railEin = !railEin)}>
      <i class="fa-solid {railEin ? 'fa-angles-left' : 'fa-angles-right'}" aria-hidden="true"></i>
    </button>
  </div>

  <p class="rubrik">Ansichten</p>
  <nav>
    {#each ansichten as a (a.id)}
      <button class="zeile menu" class:aktiv={aktiveAnsicht === a.id} onclick={() => (aktiveAnsicht = a.id)} title={a.titel}>
        <i class={a.icon} aria-hidden="true"></i><span>{a.titel}</span>
      </button>
    {/each}
  </nav>

  {#if boardgebunden}
  <p class="rubrik">Projektmappen</p>
  <nav>
    {#each mappen as m (m.id)}
      {#if bearbeiteMappeId === m.id}
        <!-- svelte-ignore a11y_autofocus -->
        <input class="feld" bind:value={mappeEntwurf} aria-label="Mappe umbenennen" autofocus
          onkeydown={(e) => { if (e.key === 'Enter') mappeSpeichern(m.id); if (e.key === 'Escape') (bearbeiteMappeId = null) }}
          onblur={() => mappeSpeichern(m.id)} />
      {:else if loescheMappeId === m.id}
        <div class="confirm">
          <span>Mappe samt allen Boards und Karten löschen?</span>
          <div class="reihe">
            <button class="mini gefahr" onclick={() => mappeLoeschenBestaetigt(m.id)}>Löschen</button>
            <button class="mini geist" onclick={() => (loescheMappeId = null)}>Abbrechen</button>
          </div>
        </div>
      {:else}
        <div class="zeile board mappe" class:aktiv={aktiveMappe?.id === m.id}>
          <button class="bname" onclick={() => waehleMappe(m)} title={m.titel}>
            <i class="fa-solid {aktiveMappe?.id === m.id ? 'fa-folder-open' : 'fa-folder'}" aria-hidden="true"></i><span>{m.titel}</span>
          </button>
          <div class="aktionen">
            <!-- Mitglieder-Pflege auch fuer Mitglieder der Mappe (Server prueft). -->
            <button class="ic" aria-label="Projekt-Mitglieder" title="Wer sieht dieses Projekt" onclick={() => onMitglieder(m)}><i class="fa-solid fa-users" aria-hidden="true"></i></button>
            <button class="ic" aria-label="Mappe umbenennen" onclick={() => { bearbeiteMappeId = m.id; mappeEntwurf = m.titel }}><i class="fa-solid fa-pen" aria-hidden="true"></i></button>
            {#if mappen.length > 1}
              <button class="ic" aria-label="Mappe löschen" onclick={() => (loescheMappeId = m.id)}><i class="fa-solid fa-trash" aria-hidden="true"></i></button>
            {/if}
          </div>
        </div>

        {#if aktiveMappe?.id === m.id}
          <!-- Unterbaum: Boards + Dokumente dieser Mappe, eingerueckt fuer klare Hierarchie -->
          <div class="unterbaum">
            {#each boards as b (b.id)}
              {#if bearbeiteBoardId === b.id}
                <!-- svelte-ignore a11y_autofocus -->
                <input class="feld" bind:value={boardEntwurf} aria-label="Board umbenennen" autofocus
                  onkeydown={(e) => { if (e.key === 'Enter') boardSpeichern(b.id); if (e.key === 'Escape') (bearbeiteBoardId = null) }}
                  onblur={() => boardSpeichern(b.id)} />
              {:else if loescheBoardId === b.id}
                <div class="confirm">
                  <span>Board und alle Karten löschen?</span>
                  <div class="reihe">
                    <button class="mini gefahr" onclick={() => boardLoeschenBestaetigt(b.id)}>Löschen</button>
                    <button class="mini geist" onclick={() => (loescheBoardId = null)}>Abbrechen</button>
                  </div>
                </div>
              {:else}
                <div class="zeile board" class:aktiv={aktivesBoard?.id === b.id}>
                  <button class="bname" onclick={() => (aktivesBoard = b)} title={b.titel}>
                    <i class="fa-solid fa-table-columns" aria-hidden="true"></i><span>{b.titel}</span>
                  </button>
                  <div class="aktionen">
                    <button class="ic" aria-label="Umbenennen" onclick={() => { bearbeiteBoardId = b.id; boardEntwurf = b.titel }}><i class="fa-solid fa-pen" aria-hidden="true"></i></button>
                    <button class="ic" aria-label="Löschen" onclick={() => (loescheBoardId = b.id)}><i class="fa-solid fa-trash" aria-hidden="true"></i></button>
                  </div>
                </div>
              {/if}
            {/each}

            {#if neuesBoard}
              <!-- svelte-ignore a11y_autofocus -->
              <input class="feld" placeholder="Board-Name" bind:value={neuerBoardTitel} aria-label="Neues Board" autofocus
                onkeydown={(e) => { if (e.key === 'Enter') neuesBoardErstellen(); if (e.key === 'Escape') { neuesBoard = false; neuerBoardTitel = '' } }} />
            {:else}
              <button class="add" onclick={() => (neuesBoard = true)}><i class="fa-solid fa-plus" aria-hidden="true"></i> Board</button>
            {/if}
            <button class="add dokbtn" onclick={onDokumente} title="Dokumente dieser Mappe"><i class="fa-solid fa-folder-open" aria-hidden="true"></i> Dokumente</button>
          </div>
        {/if}
      {/if}
    {/each}

    {#if neueMappe}
      <!-- svelte-ignore a11y_autofocus -->
      <input class="feld" placeholder="Mappen-Name" bind:value={neuerMappeTitel} aria-label="Neue Mappe" autofocus
        onkeydown={(e) => { if (e.key === 'Enter') neueMappeErstellen(); if (e.key === 'Escape') { neueMappe = false; neuerMappeTitel = '' } }} />
    {:else}
      <button class="add" onclick={() => (neueMappe = true)}><i class="fa-solid fa-plus" aria-hidden="true"></i> Mappe</button>
    {/if}
  </nav>
  {/if}

  <div class="fussbereich">
    {#if auth.angemeldet}
      <button class="abmelden" onclick={abmeldenUndNeu} title="Abmelden">
        <i class="fa-solid fa-right-from-bracket" aria-hidden="true"></i>
        <span>{auth.kuerzel ?? auth.name} abmelden</span>
      </button>
    {/if}
    <DiensteStatus />
    <div class="fzeile">
      <button class="thema" onclick={wechsleTheme} aria-label="Theme wechseln">
        <i class={theme.modus === 'dunkel' ? 'fa-solid fa-sun' : 'fa-solid fa-moon'} aria-hidden="true"></i>
        <span>{theme.modus === 'dunkel' ? 'Hell' : 'Dunkel'}</span>
      </button>
      <button class="hilfebtn" onclick={onHilfe} aria-label="Hilfe" title="Hilfe">
        <i class="fa-solid fa-circle-question" aria-hidden="true"></i>
      </button>
    </div>
  </div>
</aside>

<style>
  .rail {
    flex: 0 0 264px;
    background: var(--surface-col);
    padding: 14px 11px;
    display: flex;
    flex-direction: column;
    gap: 2px;
    overflow-y: auto;
  }
  /* Boards + Dokumente eingerueckt unter der aktiven Mappe (klare Hierarchie). */
  .unterbaum {
    display: flex;
    flex-direction: column;
    gap: 2px;
    margin: 2px 0 8px 16px;
  }
  .marke {
    font-family: var(--font-display);
    font-size: 16px;
    font-weight: 600;
    color: var(--text-1);
    display: flex;
    align-items: center;
    gap: 9px;
    padding: 4px 8px 14px;
  }
  .marke .logo {
    width: 22px;
    height: 22px;
    border-radius: 6px;
    display: block;
    flex: none;
  }
  .marke .name {
    display: flex;
    align-items: baseline;
    gap: 8px;
  }
  .railtog {
    margin-left: auto;
    border: none;
    background: transparent;
    color: var(--text-3);
    width: 26px;
    height: 26px;
    border-radius: var(--r-s);
    font-size: 12px;
    flex: none;
  }
  .railtog:hover {
    color: var(--hl-primary-text);
    background: var(--surface-3);
  }
  .rail.zu {
    flex-basis: 58px;
    border-right: 1px solid var(--border);
  }
  .rail.zu .rubrik,
  .rail.zu .marke .name,
  .rail.zu .add,
  .rail.zu .menu span,
  .rail.zu .bname span,
  .rail.zu .aktionen,
  .rail.zu .unterbaum,
  .rail.zu .thema span {
    display: none;
  }
  .rail.zu .marke {
    flex-direction: column;
    justify-content: center;
    gap: 8px;
    padding: 4px 0 12px;
  }
  .rail.zu .railtog {
    margin-left: 0;
  }
  .rail.zu :global(.dienste) {
    display: none;
  }
  .rail.zu .menu,
  .rail.zu .bname,
  .rail.zu .thema {
    justify-content: center;
  }
  .rubrik {
    font-family: var(--font-display);
    font-size: 10.5px;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: var(--text-3);
    margin: 13px 8px 5px;
  }
  nav {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }
  .zeile {
    display: flex;
    align-items: center;
    border-radius: var(--r-m);
  }
  .menu,
  .bname {
    display: flex;
    align-items: center;
    gap: 10px;
    border: none;
    background: transparent;
    color: var(--text-2);
    font-size: 13px;
    text-align: left;
    padding: 8px 9px;
    width: 100%;
    min-width: 0;
  }
  .menu {
    border-radius: var(--r-m);
  }
  .bname span,
  .menu span {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .menu:hover {
    background: var(--surface-3);
    color: var(--text-1);
  }
  .menu.aktiv {
    background: var(--hl-primary-weich);
    color: var(--hl-primary-text);
  }
  .board {
    flex: 1;
  }
  .board.aktiv {
    background: var(--hl-primary-weich);
  }
  .board.aktiv .bname {
    color: var(--hl-primary-text);
  }
  .bname {
    flex: 1;
  }
  .aktionen {
    display: flex;
    gap: 1px;
    padding-right: 4px;
    opacity: 0;
    transition: opacity 0.12s;
  }
  .board:hover .aktionen,
  .board:focus-within .aktionen {
    opacity: 1;
  }
  .ic {
    border: none;
    background: transparent;
    color: var(--text-3);
    width: 24px;
    height: 24px;
    border-radius: var(--r-s);
    font-size: 11px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .ic:hover {
    background: var(--surface-1);
    color: var(--hl-primary-text);
  }
  .add {
    display: flex;
    align-items: center;
    gap: 9px;
    border: 1px dashed var(--border-2);
    background: transparent;
    color: var(--text-3);
    font-size: 13px;
    padding: 7px 9px;
    border-radius: var(--r-m);
    margin-top: 3px;
  }
  .add:hover {
    color: var(--hl-primary-text);
    border-color: var(--hl-primary);
  }
  .feld {
    width: 100%;
    border: 1px solid var(--border-2);
    background: var(--surface-1);
    color: var(--text-1);
    border-radius: var(--r-m);
    padding: 8px 9px;
    font-size: 13px;
  }
  .confirm {
    display: flex;
    flex-direction: column;
    gap: 7px;
    padding: 8px 9px;
    font-size: 12px;
    color: var(--text-2);
  }
  .reihe {
    display: flex;
    gap: 7px;
  }
  .mini {
    border: 1px solid var(--border);
    border-radius: var(--r-s);
    padding: 5px 10px;
    font-size: 12px;
  }
  .mini.geist {
    background: transparent;
    color: var(--text-2);
  }
  .mini.gefahr {
    background: var(--gefahr);
    color: #fff;
    border-color: transparent;
    font-weight: 500;
  }
  .fussbereich {
    margin-top: auto;
    display: flex;
    flex-direction: column;
  }
  .abmelden {
    display: flex;
    align-items: center;
    gap: 8px;
    width: 100%;
    border: 1px solid var(--border);
    background: var(--surface-2);
    color: var(--text-2);
    border-radius: var(--r-m);
    padding: 7px 10px;
    font-size: 12px;
    margin-bottom: 8px;
    overflow: hidden;
    white-space: nowrap;
  }
  .abmelden:hover { background: var(--surface-3); color: var(--text-1); }
  .rail.zu .abmelden span { display: none; }
  .fzeile {
    display: flex;
    gap: 6px;
  }
  .fzeile .thema {
    flex: 1;
  }
  .hilfebtn {
    flex: none;
    width: 38px;
    border: 1px solid var(--border);
    background: var(--surface-2);
    color: var(--text-2);
    border-radius: var(--r-m);
    font-size: 14px;
  }
  .hilfebtn:hover {
    color: var(--hl-primary-text);
    border-color: var(--hl-primary);
  }
  .rail.zu .fzeile {
    flex-direction: column;
  }
  .thema {
    display: flex;
    align-items: center;
    gap: 10px;
    border: 1px solid var(--border);
    background: var(--surface-2);
    color: var(--text-2);
    font-size: 13px;
    padding: 9px 11px;
    border-radius: var(--r-m);
  }
  .thema:hover {
    color: var(--text-1);
    border-color: var(--border-2);
  }
  .ver {
    font-family: var(--font-mono);
    font-size: 10px;
    color: var(--text-3);
    font-weight: 400;
  }
</style>
