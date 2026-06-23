<script lang="ts">
  import {
    ladeBerichtTypen, ladeArchiv, erzeugeBericht, archivDownloadUrl, ladePersonen,
    type BerichtTyp, type ArchivEintrag, type Person, type KiVorschlag,
  } from '../../api'
  import { ymd, montagDer, addTage, isoDatumZeit } from '../../zeit'
  import KiAssistent from '../../ki/KiAssistent.svelte'

  let { boardId }: { boardId: string } = $props()
  $effect(() => void boardId)

  let typen = $state<BerichtTyp[]>([])
  let personen = $state<Person[]>([])
  let archiv = $state<ArchivEintrag[]>([])

  const heute = new Date()
  const montag = montagDer(heute)
  let typ = $state('stundenzettel')
  let format = $state('pdf')
  let von = $state(ymd(montag))
  let bis = $state(ymd(addTage(montag, 6)))
  let person = $state('')
  let archivieren = $state(true)
  let meldung = $state('')

  $effect(() => {
    ladeBerichtTypen().then((d) => (typen = d.typen)).catch(() => {})
    ladePersonen().then((p) => (personen = p)).catch(() => {})
    aktualisiereArchiv()
  })

  async function aktualisiereArchiv(): Promise<void> {
    archiv = await ladeArchiv().catch(() => [])
  }

  function herunterladen(blob: Blob, dateiname: string): void {
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = dateiname
    a.click()
    URL.revokeObjectURL(url)
  }

  async function erzeugen(): Promise<void> {
    meldung = ''
    try {
      const { blob, dateiname } = await erzeugeBericht({
        typ, format, von, bis, person: person || null, archivieren,
      })
      herunterladen(blob, dateiname)
      meldung = archivieren ? 'Bericht erzeugt, heruntergeladen und archiviert.' : 'Bericht erzeugt und heruntergeladen.'
      if (archivieren) await aktualisiereArchiv()
    } catch {
      meldung = 'Bericht konnte nicht erzeugt werden.'
    }
  }

  // KI-Berichts-Finder: aus einem Wunsch das Formular ausfuellen; der Mensch bestaetigt je Feld.
  function kiBerichtKontext(): Record<string, unknown> {
    return {
      heute: ymd(new Date()),
      formate: ['pdf', 'csv', 'markdown'],
      typen: typen.map((t) => ({ id: t.id, name: t.titel })),
      personen: personen.map((p) => ({ kuerzel: p.kuerzel ?? '', name: p.name })),
    }
  }
  function kiBerichtUebernehmen(gewaehlt: KiVorschlag[]): void {
    for (const v of gewaehlt) {
      const i = v.id.indexOf(':')
      const art = v.id.slice(0, i)
      const wert = v.id.slice(i + 1)
      if (art === 'typ') typ = wert
      else if (art === 'format') format = wert
      else if (art === 'von') von = wert
      else if (art === 'bis') bis = wert
      else if (art === 'person') person = wert
    }
  }

  const brauchtZeitraum = $derived(typ !== 'soll_ist')

  function groesse(b: number): string {
    return b > 1024 ? `${Math.round(b / 1024)} KB` : `${b} B`
  }
</script>

<div class="berichte">
  <section class="block">
    <p class="sec">Bericht erzeugen</p>
    <div class="form">
      <select bind:value={typ}>
        {#each typen as t (t.id)}<option value={t.id}>{t.titel}</option>{/each}
      </select>
      <select bind:value={format}>
        <option value="pdf">PDF</option>
        <option value="csv">CSV</option>
        <option value="markdown">Markdown</option>
      </select>
      {#if brauchtZeitraum}
        <label class="mini">von <input type="date" bind:value={von} /></label>
        <label class="mini">bis <input type="date" bind:value={bis} /></label>
      {/if}
      {#if typ === 'stundenzettel'}
        <select bind:value={person}>
          <option value="">alle Personen</option>
          {#each personen as p (p.id)}<option value={p.kuerzel ?? ''}>{p.name}</option>{/each}
        </select>
      {/if}
      <label class="chk"><input type="checkbox" bind:checked={archivieren} /> archivieren</label>
      <KiAssistent typ="bericht" titel="Bericht aus Wunsch" platzhalter="z.B. Stundenzettel fuer MP im Januar als PDF" uebernehmenText="Formular fuellen" kontext={kiBerichtKontext} onUebernehmen={kiBerichtUebernehmen} />
      <button class="btn primaer" onclick={erzeugen}>Erzeugen</button>
    </div>
    {#if meldung}<p class="meldung">{meldung}</p>{/if}
  </section>

  <section class="block">
    <p class="sec">Berichts-Archiv (Nachweise)</p>
    {#if !archiv.length}<p class="leer">Noch keine archivierten Berichte.</p>{/if}
    {#each archiv as b (b.id)}
      <a class="eintrag" href={archivDownloadUrl(b.id)} download>
        <span class="bt">{b.titel}</span>
        <span class="bz">{b.zeitraum}</span>
        <span class="bf">{b.format.toUpperCase()}</span>
        <span class="bd">{isoDatumZeit(b.erstellt_am)}</span>
        <span class="bg">{groesse(b.groesse)}</span>
        <i class="fa-solid fa-download" aria-hidden="true"></i>
      </a>
    {/each}
  </section>
</div>

<style>
  .berichte { height: 100%; overflow-y: auto; padding: 16px; max-width: 920px; }
  .sec { font-family: var(--font-display); font-size: 11px; letter-spacing: 0.04em; text-transform: uppercase; color: var(--text-3); margin: 0 0 8px; }
  .block { margin-bottom: 22px; }
  .form { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
  .form select, .form input { border: 1px solid var(--border-2); background: var(--surface-2); color: var(--text-1); border-radius: var(--r-m); padding: 7px 9px; font-size: 12.5px; }
  .mini { display: inline-flex; align-items: center; gap: 6px; color: var(--text-3); font-size: 11.5px; }
  .chk { display: inline-flex; align-items: center; gap: 6px; color: var(--text-2); font-size: 12px; }
  .btn { border: 1px solid var(--border); border-radius: var(--r-m); padding: 8px 13px; font-size: 12.5px; }
  .btn.primaer { background: var(--hl-primary); color: var(--hl-on-primary); border-color: transparent; font-weight: 500; }
  .meldung { margin-top: 8px; font-size: 12px; color: var(--ok); }
  .leer { color: var(--text-3); font-size: 12.5px; }
  .eintrag { display: grid; grid-template-columns: 1fr 150px 56px 130px 70px 20px; align-items: center; gap: 10px; text-decoration: none; color: var(--text-1); border: 1px solid var(--border); background: var(--surface-col); border-radius: var(--r-m); padding: 9px 12px; margin-bottom: 5px; font-size: 12.5px; }
  .eintrag:hover { background: var(--surface-3); }
  .bt { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .bz, .bd, .bg { color: var(--text-3); font-size: 11.5px; }
  .bf { color: var(--hl-primary-text); font-size: 11px; }
  .eintrag i { color: var(--text-3); }
</style>
