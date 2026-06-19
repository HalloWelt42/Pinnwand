<script lang="ts">
  import {
    ladeSnapshots, backupZustand, erzeugeSnapshot, snapshotVorschau,
    snapshotDownloadUrl, stelleSnapshotWiederHer, loescheSnapshot,
    ladeAgentTokens, erstelleAgentToken, widerrufeAgentToken, AuthFehler,
    type SnapshotInfo, type BackupZustand, type BackupVorschau, type AgentToken,
  } from '../../api'

  let { boardId }: { boardId: string } = $props()
  $effect(() => void boardId)

  let snapshots = $state<SnapshotInfo[]>([])
  let zustand = $state<BackupZustand | null>(null)
  let notiz = $state('')
  let meldung = $state('')
  let arbeitet = $state(false)

  // Aufgeklappte Vorschau (zugleich Wiederherstellungs-Dialog) je Snapshot.
  let offen = $state<string | null>(null)
  let vorschau = $state<BackupVorschau | null>(null)
  let vorschauLaedt = $state(false)
  // Bestaetigung des Loeschens (kein Browser-Dialog).
  let loeschBestaetigung = $state<string | null>(null)

  const ART_LABEL: Record<string, string> = {
    manuell: 'Manuell',
    automatisch: 'Automatisch',
    vor_wiederherstellung: 'Vor Wiederherstellung',
  }

  $effect(() => { neuLaden() })

  async function neuLaden(): Promise<void> {
    snapshots = await ladeSnapshots().catch(() => [])
    zustand = await backupZustand().catch(() => null)
  }

  function datum(s: string): string {
    return s.replace('T', ' ').slice(0, 16)
  }
  function groesse(b: number): string {
    return b > 1024 * 1024 ? `${(b / 1024 / 1024).toFixed(1)} MB` : b > 1024 ? `${Math.round(b / 1024)} KB` : `${b} B`
  }
  function summe(z: Record<string, number> | undefined): number {
    if (!z) return 0
    return Object.values(z).reduce((a, n) => a + Math.max(n, 0), 0)
  }

  async function jetztSichern(): Promise<void> {
    arbeitet = true
    meldung = ''
    try {
      await erzeugeSnapshot(notiz.trim())
      notiz = ''
      meldung = 'Snapshot erstellt.'
      await neuLaden()
    } catch {
      meldung = 'Snapshot konnte nicht erstellt werden.'
    } finally {
      arbeitet = false
    }
  }

  async function vorschauOeffnen(id: string): Promise<void> {
    if (offen === id) { offen = null; vorschau = null; return }
    offen = id
    vorschau = null
    vorschauLaedt = true
    try {
      vorschau = await snapshotVorschau(id)
    } catch {
      meldung = 'Vorschau konnte nicht geladen werden.'
      offen = null
    } finally {
      vorschauLaedt = false
    }
  }

  async function wiederherstellen(id: string): Promise<void> {
    arbeitet = true
    meldung = ''
    try {
      const e = await stelleSnapshotWiederHer(id)
      meldung = `Wiederhergestellt. Vorheriger Stand wurde als Sicherheits-Snapshot gesichert.`
      void e
      offen = null
      vorschau = null
      await neuLaden()
    } catch {
      meldung = 'Wiederherstellung fehlgeschlagen.'
    } finally {
      arbeitet = false
    }
  }

  async function loeschen(id: string): Promise<void> {
    arbeitet = true
    try {
      await loescheSnapshot(id)
      loeschBestaetigung = null
      if (offen === id) { offen = null; vorschau = null }
      await neuLaden()
    } catch {
      meldung = 'Snapshot konnte nicht geloescht werden.'
    } finally {
      arbeitet = false
    }
  }

  // --- Agenten-Zugriff (Token-Verwaltung) ---
  let adminToken = $state(localStorage.getItem('pw_admin_token') ?? '')
  let tokens = $state<AgentToken[]>([])
  let tokenGeladen = $state(false)
  let tokenFehler = $state('')
  let neuName = $state('')
  let neuRead = $state(true)
  let neuWrite = $state(true)
  let neuAdmin = $state(false)
  let neuesGeheimnis = $state<{ name: string; token: string } | null>(null)

  async function tokensLaden(): Promise<void> {
    tokenFehler = ''
    neuesGeheimnis = null
    if (!adminToken.trim()) { tokenFehler = 'Bitte ein Verwaltungs-Token eingeben.'; return }
    try {
      tokens = await ladeAgentTokens(adminToken.trim())
      tokenGeladen = true
      localStorage.setItem('pw_admin_token', adminToken.trim())
    } catch (e) {
      tokenGeladen = false
      tokenFehler = e instanceof AuthFehler ? e.message : 'Agenten-API nicht erreichbar.'
    }
  }

  async function tokenErstellen(): Promise<void> {
    tokenFehler = ''
    if (!neuName.trim()) { tokenFehler = 'Bitte einen Namen vergeben.'; return }
    const scopes = [neuRead && 'read', neuWrite && 'write', neuAdmin && 'admin'].filter(Boolean) as string[]
    try {
      const t = await erstelleAgentToken(adminToken.trim(), neuName.trim(), scopes)
      neuName = ''
      // Erst die Liste auffrischen (setzt das Geheimnis zurueck), dann das neue Geheimnis anzeigen.
      await tokensLaden()
      neuesGeheimnis = { name: t.name, token: t.token }
    } catch (e) {
      tokenFehler = e instanceof AuthFehler ? e.message : 'Token konnte nicht erstellt werden.'
    }
  }

  async function tokenWiderrufen(id: string): Promise<void> {
    try {
      await widerrufeAgentToken(adminToken.trim(), id)
      await tokensLaden()
    } catch {
      tokenFehler = 'Token konnte nicht widerrufen werden.'
    }
  }

  // Tabellen-Zaehler aus Snapshot und aktuellem Stand fuer die Vorschau zusammenfuehren.
  function zeilen(v: BackupVorschau): { name: string; snap: number; akt: number }[] {
    const keys = new Set<string>([...Object.keys(v.snapshot.zaehler), ...Object.keys(v.aktuell.zaehler)])
    return [...keys].sort().map((name) => ({
      name,
      snap: v.snapshot.zaehler[name] ?? 0,
      akt: v.aktuell.zaehler[name] ?? 0,
    }))
  }
</script>

<div class="einstellungen">
  <section class="block">
    <p class="sec">Datensicherung</p>
    <p class="hint">
      Ein Snapshot sichert Datenbank, Berichts-Archiv und Konfigurationsvorlage in einer Datei.
      Beim Start wird hoechstens einmal taeglich automatisch gesichert; die letzten automatischen Snapshots bleiben erhalten.
      Vor jeder Wiederherstellung wird der aktuelle Stand automatisch gesichert.
    </p>
    {#if zustand}
      <p class="stand">
        Aktueller Stand: Version {zustand.version} - {summe(zustand.zaehler)} Datensaetze, {zustand.berichte} Berichte im Archiv.
      </p>
    {/if}
    <div class="form">
      <input class="notiz" placeholder="Notiz (optional)" bind:value={notiz} maxlength="200" aria-label="Notiz" />
      <button class="btn primaer" onclick={jetztSichern} disabled={arbeitet}>
        <i class="fa-solid fa-floppy-disk" aria-hidden="true"></i> Snapshot erstellen
      </button>
    </div>
    {#if meldung}<p class="meldung">{meldung}</p>{/if}
  </section>

  <section class="block">
    <p class="sec">Snapshots</p>
    {#if !snapshots.length}<p class="leer">Noch keine Snapshots vorhanden.</p>{/if}
    {#each snapshots as s (s.id)}
      <div class="snap" class:auf={offen === s.id}>
        <div class="kopf">
          <span class="art art-{s.art}">{ART_LABEL[s.art] ?? s.art}</span>
          <span class="zeit">{datum(s.erstellt_am)}</span>
          <span class="notizt">{s.notiz}</span>
          <span class="ver">v{s.version}</span>
          <span class="gr">{groesse(s.groesse)}</span>
          <div class="aktionen">
            <button class="ibtn" title="Vorschau und Wiederherstellung" aria-label="Vorschau" onclick={() => vorschauOeffnen(s.id)}>
              <i class="fa-solid fa-rotate-left" aria-hidden="true"></i>
            </button>
            <a class="ibtn" href={snapshotDownloadUrl(s.id)} download title="Herunterladen" aria-label="Herunterladen">
              <i class="fa-solid fa-download" aria-hidden="true"></i>
            </a>
            <button class="ibtn gefahr" title="Loeschen" aria-label="Loeschen" onclick={() => (loeschBestaetigung = loeschBestaetigung === s.id ? null : s.id)}>
              <i class="fa-solid fa-trash" aria-hidden="true"></i>
            </button>
          </div>
        </div>

        {#if loeschBestaetigung === s.id}
          <div class="bestaetigung">
            <span>Diesen Snapshot dauerhaft loeschen?</span>
            <button class="btn klein gefahr" onclick={() => loeschen(s.id)} disabled={arbeitet}>Loeschen</button>
            <button class="btn klein" onclick={() => (loeschBestaetigung = null)}>Abbrechen</button>
          </div>
        {/if}

        {#if offen === s.id}
          <div class="vorschau">
            {#if vorschauLaedt}
              <p class="leer">Vorschau wird geladen ...</p>
            {:else if vorschau}
              {#if vorschau.warnungen.length}
                <div class="warnung">
                  <i class="fa-solid fa-triangle-exclamation" aria-hidden="true"></i>
                  <ul>{#each vorschau.warnungen as w (w)}<li>{w}</li>{/each}</ul>
                </div>
              {/if}
              <table class="diff">
                <thead><tr><th>Bereich</th><th>im Snapshot</th><th>aktuell</th></tr></thead>
                <tbody>
                  {#each zeilen(vorschau) as r (r.name)}
                    <tr class:geaendert={r.snap !== r.akt}>
                      <td>{r.name}</td><td>{r.snap}</td><td>{r.akt}</td>
                    </tr>
                  {/each}
                  <tr class:geaendert={vorschau.snapshot.berichte !== vorschau.aktuell.berichte}>
                    <td>Berichte (Archiv)</td><td>{vorschau.snapshot.berichte}</td><td>{vorschau.aktuell.berichte}</td>
                  </tr>
                </tbody>
              </table>
              <p class="ersetzt">
                Beim Wiederherstellen werden die aktuellen Daten durch den Stand des Snapshots ersetzt.
                Der jetzige Stand wird zuvor automatisch gesichert.
              </p>
              <div class="vfuss">
                <button class="btn primaer" onclick={() => wiederherstellen(s.id)} disabled={arbeitet}>
                  <i class="fa-solid fa-rotate-left" aria-hidden="true"></i> Diesen Stand wiederherstellen
                </button>
                <button class="btn" onclick={() => vorschauOeffnen(s.id)}>Schliessen</button>
              </div>
            {/if}
          </div>
        {/if}
      </div>
    {/each}
  </section>

  <section class="block">
    <p class="sec">Agenten-Zugriff (API-Token)</p>
    <p class="hint">
      KI-Werkzeuge koennen ueber die Agenten-API Aufgaben anlegen, Zeiten buchen und suchen.
      Die Verwaltung erfordert ein Token mit Admin-Recht. Das einfachste ist das in der Konfiguration
      gesetzte Verwaltungs-Token (PINNWAND_AGENT_TOKEN aus der .env). Das Token wird nur lokal in diesem
      Browser gespeichert.
    </p>
    <div class="form">
      <input class="notiz" type="password" placeholder="Verwaltungs-Token" bind:value={adminToken} aria-label="Verwaltungs-Token" />
      <button class="btn primaer" onclick={tokensLaden}>
        <i class="fa-solid fa-key" aria-hidden="true"></i> Laden
      </button>
    </div>
    {#if tokenFehler}<p class="fehler">{tokenFehler}</p>{/if}

    {#if tokenGeladen}
      <div class="tokenneu">
        <input class="tname" placeholder="Name (z.B. LM Studio)" bind:value={neuName} aria-label="Name des Tokens" />
        <label class="chk"><input type="checkbox" bind:checked={neuRead} /> lesen</label>
        <label class="chk"><input type="checkbox" bind:checked={neuWrite} /> schreiben</label>
        <label class="chk"><input type="checkbox" bind:checked={neuAdmin} /> admin</label>
        <button class="btn" onclick={tokenErstellen}>Token erstellen</button>
      </div>

      {#if neuesGeheimnis}
        <div class="geheimnis">
          <p><i class="fa-solid fa-circle-info" aria-hidden="true"></i> Neues Token fuer "{neuesGeheimnis.name}" - jetzt kopieren, es wird nicht erneut angezeigt:</p>
          <code>{neuesGeheimnis.token}</code>
        </div>
      {/if}

      {#if !tokens.length}<p class="leer">Noch keine Token vergeben.</p>{/if}
      {#each tokens as t (t.id)}
        <div class="trow" class:inaktiv={!t.aktiv}>
          <span class="tn">{t.name}</span>
          <span class="ts">{t.scopes.join(', ')}</span>
          <span class="td">{t.zuletzt_genutzt ? 'zuletzt ' + datum(t.zuletzt_genutzt) : 'nie genutzt'}</span>
          <span class="tstatus">{t.aktiv ? 'aktiv' : 'widerrufen'}</span>
          {#if t.aktiv}
            <button class="ibtn gefahr" title="Widerrufen" aria-label="Widerrufen" onclick={() => tokenWiderrufen(t.id)}>
              <i class="fa-solid fa-ban" aria-hidden="true"></i>
            </button>
          {:else}<span></span>{/if}
        </div>
      {/each}
    {/if}
  </section>
</div>

<style>
  .einstellungen { height: 100%; overflow-y: auto; padding: 16px; max-width: 920px; }
  .sec { font-family: var(--font-display); font-size: 11px; letter-spacing: 0.04em; text-transform: uppercase; color: var(--text-3); margin: 0 0 8px; }
  .block { margin-bottom: 26px; }
  .hint { font-size: 12px; color: var(--text-3); line-height: 1.55; margin: 0 0 10px; max-width: 70ch; }
  .stand { font-size: 12.5px; color: var(--text-2); margin: 0 0 10px; }
  .form { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
  .notiz { flex: 1; min-width: 220px; border: 1px solid var(--border-2); background: var(--surface-2); color: var(--text-1); border-radius: var(--r-m); padding: 8px 10px; font-size: 12.5px; }
  .btn { border: 1px solid var(--border); border-radius: var(--r-m); padding: 8px 13px; font-size: 12.5px; display: inline-flex; align-items: center; gap: 7px; }
  .btn.primaer { background: var(--hl-primary); color: var(--hl-on-primary); border-color: transparent; font-weight: 500; }
  .btn.klein { padding: 5px 10px; font-size: 11.5px; }
  .btn.gefahr { color: var(--gefahr, #e5484d); border-color: var(--gefahr, #e5484d); background: transparent; }
  .meldung { margin-top: 9px; font-size: 12px; color: var(--ok); }
  .leer { color: var(--text-3); font-size: 12.5px; }

  .snap { border: 1px solid var(--border); background: var(--surface-col); border-radius: var(--r-m); margin-bottom: 6px; }
  .snap.auf { border-color: var(--border-2); }
  .kopf { display: grid; grid-template-columns: 130px 130px 1fr 60px 70px auto; align-items: center; gap: 10px; padding: 9px 12px; font-size: 12.5px; }
  .art { font-size: 10.5px; padding: 2px 7px; border-radius: 999px; text-align: center; font-family: var(--font-display); }
  .art-manuell { background: var(--hl-primary-weich, rgba(99,102,241,0.16)); color: var(--hl-primary-text); }
  .art-automatisch { background: var(--surface-3); color: var(--text-3); }
  .art-vor_wiederherstellung { background: rgba(245,158,11,0.16); color: #f59e0b; }
  .zeit { color: var(--text-2); }
  .notizt { color: var(--text-3); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .ver, .gr { color: var(--text-3); font-size: 11.5px; }
  .aktionen { display: inline-flex; gap: 4px; justify-self: end; }
  .ibtn { border: 1px solid var(--border); background: var(--surface-2); color: var(--text-2); border-radius: var(--r-s, 6px); width: 30px; height: 30px; display: inline-flex; align-items: center; justify-content: center; }
  .ibtn:hover { background: var(--surface-3); }
  .ibtn.gefahr:hover { color: var(--gefahr, #e5484d); }

  .bestaetigung { display: flex; align-items: center; gap: 10px; padding: 8px 12px; border-top: 1px solid var(--border); font-size: 12px; color: var(--text-2); }
  .vorschau { border-top: 1px solid var(--border); padding: 12px; }
  .warnung { display: flex; gap: 8px; background: rgba(245,158,11,0.1); border: 1px solid rgba(245,158,11,0.3); border-radius: var(--r-m); padding: 8px 11px; margin-bottom: 10px; color: #f59e0b; font-size: 12px; }
  .warnung ul { margin: 0; padding-left: 16px; }
  .diff { width: 100%; border-collapse: collapse; font-size: 12px; }
  .diff th { text-align: left; color: var(--text-3); font-weight: 500; font-size: 11px; padding: 4px 8px; border-bottom: 1px solid var(--border); }
  .diff td { padding: 3px 8px; color: var(--text-2); border-bottom: 1px solid var(--border); }
  .diff td:nth-child(2), .diff td:nth-child(3), .diff th:nth-child(2), .diff th:nth-child(3) { text-align: right; width: 110px; }
  .diff tr.geaendert td { color: var(--hl-primary-text); }
  .ersetzt { font-size: 11.5px; color: var(--text-3); margin: 10px 0; line-height: 1.5; }
  .vfuss { display: flex; gap: 8px; }

  .fehler { margin-top: 8px; font-size: 12px; color: var(--gefahr, #e5484d); }
  .tokenneu { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; margin: 12px 0; }
  .tname { border: 1px solid var(--border-2); background: var(--surface-2); color: var(--text-1); border-radius: var(--r-m); padding: 8px 10px; font-size: 12.5px; min-width: 200px; }
  .chk { display: inline-flex; align-items: center; gap: 6px; color: var(--text-2); font-size: 12px; }
  .geheimnis { background: var(--surface-2); border: 1px solid var(--border-2); border-radius: var(--r-m); padding: 10px 12px; margin-bottom: 12px; }
  .geheimnis p { margin: 0 0 6px; font-size: 12px; color: var(--text-2); }
  .geheimnis code { display: block; font-family: var(--font-mono, monospace); font-size: 12px; color: var(--hl-primary-text); word-break: break-all; background: var(--surface-3); padding: 8px 10px; border-radius: var(--r-s, 6px); }
  .trow { display: grid; grid-template-columns: 1fr 150px 160px 90px 32px; align-items: center; gap: 10px; padding: 8px 12px; border: 1px solid var(--border); background: var(--surface-col); border-radius: var(--r-m); margin-bottom: 5px; font-size: 12.5px; }
  .trow.inaktiv { opacity: 0.55; }
  .tn { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .ts { color: var(--hl-primary-text); font-size: 11.5px; }
  .td, .tstatus { color: var(--text-3); font-size: 11.5px; }
</style>
