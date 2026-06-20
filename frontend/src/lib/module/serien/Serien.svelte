<script lang="ts">
  import { ladeBoard, ladeSerien, erstelleSerie, aktualisiereSerie, loescheSerie, serieVorschau, serieVorbuchen, type Serie } from '../../api'
  import type { Spalte } from '../../types'
  import { isoKurz } from '../../zeit'

  let { boardId }: { boardId: string } = $props()

  const WD = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So']

  let serien = $state<Serie[]>([])
  let spalten = $state<Spalte[]>([])
  let vorschau = $state<Record<string, string[]>>({})
  let meldung = $state('')

  // Formular
  let titel = $state('')
  let typ = $state<'taeglich' | 'woechentlich' | 'monatlich'>('woechentlich')
  let intervall = $state(1)
  let wochentage = $state<number[]>([])
  let monatstag = $state(1)
  let uhrzeit = $state('')
  let dauerMin = $state(30)
  let spalteId = $state('')
  let vorlaufTage = $state(21)
  let wochenendenUeberspringen = $state(false)

  async function laden(): Promise<void> {
    serien = await ladeSerien(boardId)
    const b = await ladeBoard(boardId)
    spalten = b.spalten
    if (!spalteId && spalten[0]) spalteId = spalten[0].id
  }
  $effect(() => {
    void boardId
    laden()
  })

  function wtUmschalten(i: number): void {
    wochentage = wochentage.includes(i) ? wochentage.filter((x) => x !== i) : [...wochentage, i].sort()
  }

  async function anlegen(): Promise<void> {
    if (!titel.trim()) return
    await erstelleSerie({
      board_id: boardId,
      spalte_id: spalteId || null,
      titel: titel.trim(),
      typ,
      intervall,
      wochentage: typ === 'woechentlich' ? wochentage : [],
      monatstag: typ === 'monatlich' ? monatstag : null,
      uhrzeit: uhrzeit || null,
      dauer_min: dauerMin || null,
      vorlauf_tage: vorlaufTage,
      wochenenden_ueberspringen: wochenendenUeberspringen,
    })
    titel = ''
    uhrzeit = ''
    wochentage = []
    meldung = 'Serie angelegt und vorgebucht.'
    await laden()
  }

  async function umschaltenAktiv(s: Serie): Promise<void> {
    await aktualisiereSerie(s.id, { aktiv: !s.aktiv })
    await laden()
  }
  async function entfernen(s: Serie): Promise<void> {
    await loescheSerie(s.id)
    await laden()
  }
  async function vorbuchen(s: Serie): Promise<void> {
    const { erzeugt } = await serieVorbuchen(s.id)
    meldung = erzeugt ? `${erzeugt} Termine vorgebucht.` : 'Bereits aktuell - nichts Neues.'
  }
  async function zeigeVorschau(s: Serie): Promise<void> {
    vorschau = { ...vorschau, [s.id]: (await serieVorschau(s.id, 30)).termine }
  }

  function rhythmus(s: Serie): string {
    const iv = s.intervall > 1 ? `alle ${s.intervall} ` : ''
    if (s.typ === 'taeglich') return `${iv}Tage`.trim()
    if (s.typ === 'monatlich') return `${iv}Monate, Tag ${s.monatstag ?? '-'}`.trim()
    const tage = s.wochentage.length ? s.wochentage.map((i) => WD[i]).join(', ') : 'wie Start'
    return `${iv}Wochen (${tage})`.trim()
  }
</script>

<div class="serien">
  <section class="neu">
    <p class="sec">Neue Serie</p>
    <div class="form">
      <input class="f titel" placeholder="Titel (z.B. REKO-Telko)" bind:value={titel} />
      <select class="f" bind:value={typ}>
        <option value="taeglich">täglich</option>
        <option value="woechentlich">wöchentlich</option>
        <option value="monatlich">monatlich</option>
      </select>
      <label class="f mini">Intervall <input type="number" min="1" bind:value={intervall} /></label>
      {#if typ === 'woechentlich'}
        <div class="wd">
          {#each WD as w, i (w)}
            <button type="button" class="wdb" class:an={wochentage.includes(i)} onclick={() => wtUmschalten(i)}>{w}</button>
          {/each}
        </div>
      {/if}
      {#if typ === 'monatlich'}
        <label class="f mini">Monatstag <input type="number" min="1" max="31" bind:value={monatstag} /></label>
      {/if}
      <label class="f mini">Uhrzeit <input type="time" bind:value={uhrzeit} /></label>
      <label class="f mini">Dauer (min) <input type="number" min="0" bind:value={dauerMin} /></label>
      <select class="f" bind:value={spalteId}>
        {#each spalten as s (s.id)}<option value={s.id}>{s.titel}</option>{/each}
      </select>
      <label class="f mini">Vorlauf (Tage) <input type="number" min="0" bind:value={vorlaufTage} /></label>
      <label class="f chk"><input type="checkbox" bind:checked={wochenendenUeberspringen} /> Wochenenden überspringen</label>
      <button class="btn primaer" onclick={anlegen}>Anlegen + vorbuchen</button>
    </div>
    {#if meldung}<p class="meldung">{meldung}</p>{/if}
  </section>

  <section class="liste">
    <p class="sec">Serien dieses Boards</p>
    {#if !serien.length}<p class="leer">Noch keine Serien.</p>{/if}
    {#each serien as s (s.id)}
      <div class="serie" class:aus={!s.aktiv}>
        <div class="kopf">
          <span class="t">{s.uhrzeit ? s.uhrzeit + ' ' : ''}{s.titel}</span>
          <span class="rhy">{rhythmus(s)}{#if s.dauer_min} &middot; {s.dauer_min} min{/if}</span>
          <span class="akt">
            <button class="ic" title="Vorschau" onclick={() => zeigeVorschau(s)}><i class="fa-solid fa-calendar-day" aria-hidden="true"></i></button>
            <button class="ic" title="Jetzt vorbuchen" onclick={() => vorbuchen(s)}><i class="fa-solid fa-bolt" aria-hidden="true"></i></button>
            <button class="ic" title={s.aktiv ? 'Pausieren' : 'Aktivieren'} onclick={() => umschaltenAktiv(s)}><i class="fa-solid {s.aktiv ? 'fa-pause' : 'fa-play'}" aria-hidden="true"></i></button>
            <button class="ic rot" title="Löschen" onclick={() => entfernen(s)}><i class="fa-solid fa-trash" aria-hidden="true"></i></button>
          </span>
        </div>
        {#if vorschau[s.id]}
          <div class="vs">{vorschau[s.id].slice(0, 8).map(isoKurz).join(' · ') || 'keine kommenden Termine'}</div>
        {/if}
      </div>
    {/each}
  </section>
</div>

<style>
  .serien {
    height: 100%;
    overflow-y: auto;
    padding: 16px;
    max-width: 900px;
  }
  .sec {
    font-family: var(--font-display);
    font-size: 11px;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: var(--text-3);
    margin: 0 0 8px;
  }
  .neu {
    margin-bottom: 18px;
  }
  .form {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    align-items: center;
  }
  .f {
    border: 1px solid var(--border-2);
    background: var(--surface-2);
    color: var(--text-1);
    border-radius: var(--r-m);
    padding: 7px 9px;
    font-size: 12.5px;
  }
  .f.titel {
    flex: 1;
    min-width: 200px;
  }
  .f.mini {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    color: var(--text-3);
    font-size: 11.5px;
  }
  .f.mini input {
    width: 64px;
    border: none;
    background: transparent;
    color: var(--text-1);
    font-size: 12.5px;
  }
  .f.chk {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    color: var(--text-2);
    font-size: 12px;
    border: none;
    background: transparent;
  }
  .wd {
    display: flex;
    gap: 3px;
  }
  .wdb {
    width: 32px;
    height: 32px;
    border-radius: var(--r-s);
    border: 1px solid var(--border-2);
    background: var(--surface-2);
    color: var(--text-2);
    font-size: 11px;
  }
  .wdb.an {
    background: var(--hl-primary);
    color: var(--hl-on-primary);
    border-color: transparent;
  }
  .btn {
    border: 1px solid var(--border);
    border-radius: var(--r-m);
    padding: 8px 13px;
    font-size: 12.5px;
  }
  .btn.primaer {
    background: var(--hl-primary);
    color: var(--hl-on-primary);
    border-color: transparent;
    font-weight: 500;
  }
  .meldung {
    margin-top: 8px;
    font-size: 12px;
    color: var(--ok);
  }
  .leer {
    color: var(--text-3);
    font-size: 12.5px;
  }
  .serie {
    border: 1px solid var(--border);
    background: var(--surface-col);
    border-radius: var(--r-m);
    padding: 10px 12px;
    margin-bottom: 6px;
  }
  .serie.aus {
    opacity: 0.55;
  }
  .kopf {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .t {
    font-weight: 500;
    color: var(--text-1);
    font-size: 13px;
  }
  .rhy {
    font-size: 11.5px;
    color: var(--text-3);
  }
  .akt {
    margin-left: auto;
    display: flex;
    gap: 2px;
  }
  .ic {
    width: 28px;
    height: 28px;
    border-radius: var(--r-s);
    border: none;
    background: transparent;
    color: var(--text-3);
    font-size: 12px;
  }
  .ic:hover {
    background: var(--surface-3);
    color: var(--hl-primary-text);
  }
  .ic.rot:hover {
    color: var(--gefahr);
  }
  .vs {
    margin-top: 8px;
    font-size: 11.5px;
    color: var(--text-2);
    font-family: var(--font-mono);
  }
</style>
