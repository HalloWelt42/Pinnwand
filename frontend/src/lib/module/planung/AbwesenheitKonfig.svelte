<script lang="ts">
  import {
    ladeAbwesenheitstypen, aktualisiereAbwesenheitstyp, ladeTagesregeln, setzeTagesregel, loescheTagesregel,
    type AbwesenheitTyp, type Tagesregel,
  } from '../../api'
  import FarbWahl from '../../FarbWahl.svelte'
  import { WOCHENTAGE_KURZ } from '../../zeit'

  // Konfiguration: Abwesenheits-Arten (Farbe, Anrechnung) sowie globale
  // Halbtags- und Sonderregeln (nur für Admins).
  let { kontenNeuLaden }: {
    kontenNeuLaden: () => Promise<void>
  } = $props()

  let abwTypen = $state<AbwesenheitTyp[]>([])
  let regeln = $state<Tagesregel[]>([])
  let rArt = $state<'jahrestag' | 'wochentag'>('jahrestag')
  let rMonat = $state(12)
  let rTag = $state(24)
  let rWochentag = $state(4)
  let rAnteil = $state(0.5)
  let rNotiz = $state('')

  async function ladenKonfig(): Promise<void> {
    abwTypen = await ladeAbwesenheitstypen().catch(() => [])
    regeln = await ladeTagesregeln().catch(() => [])
  }
  async function anrechnenAendern(t: AbwesenheitTyp, wert: boolean): Promise<void> {
    await aktualisiereAbwesenheitstyp(t.code, { anrechnen: wert })
    await ladenKonfig()
    await kontenNeuLaden()
  }
  async function farbeAendern(t: AbwesenheitTyp, wert: string): Promise<void> {
    await aktualisiereAbwesenheitstyp(t.code, { farbe: wert })
    await ladenKonfig()
  }
  async function regelHinzufuegen(): Promise<void> {
    const d: Partial<Tagesregel> = rArt === 'jahrestag'
      ? { art: 'jahrestag', monat: rMonat, tag: rTag, anteil: rAnteil, notiz: rNotiz || null }
      : { art: 'wochentag', wochentag: rWochentag, anteil: rAnteil, notiz: rNotiz || null }
    await setzeTagesregel(d)
    rNotiz = ''
    await ladenKonfig()
  }
  async function regelLoeschen(id: string): Promise<void> {
    await loescheTagesregel(id)
    await ladenKonfig()
  }
  async function brueckeUmschalten(r: Tagesregel): Promise<void> {
    await setzeTagesregel({ ...r, aktiv: !r.aktiv })
    await ladenKonfig()
  }

  const MON = ['', 'Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez']
  const WDV = WOCHENTAGE_KURZ
  function regelText(r: Tagesregel): string {
    if (r.art === 'jahrestag') return `${r.tag}. ${MON[r.monat ?? 0]} (jährlich)`
    if (r.art === 'wochentag') return `jeden ${WDV[r.wochentag ?? 0]}`
    return 'Brückentage'
  }

  $effect(() => { ladenKonfig() })
</script>

<section class="block">
  <p class="sec">Abwesenheits-Arten</p>
  <div class="atab">
    {#each abwTypen as t (t.code)}
      <div class="azeile">
        <span class="cfarbe" style="background:{t.farbe}" title={t.farbe}></span>
        <span class="aname">{t.name}</span>
        <FarbWahl value={t.farbe} mitKeine={false} onWahl={(c) => { if (c) farbeAendern(t, c) }} />
        <span class="adez">{t.anwesend ? 'gilt als anwesend' : t.reduziert_soll ? 'reduziert Soll' : ''}</span>
        <label class="chk"><input type="checkbox" checked={t.anrechnen} onchange={(e) => anrechnenAendern(t, e.currentTarget.checked)} /> zählt gegen Urlaubsanspruch</label>
      </div>
    {/each}
  </div>
</section>

<section class="block">
  <p class="sec">Halbtags- und Sonderregeln</p>
  <p class="hinweis">Gelten global für alle. Anteil 0,5 = halber Tag, 0 = frei.</p>
  <div class="rliste">
    {#each regeln as r (r.id)}
      <div class="rzeile">
        {#if r.art === 'brueckentag'}
          <label class="chk"><input type="checkbox" checked={r.aktiv} onchange={() => brueckeUmschalten(r)} /> Brückentage automatisch frei</label>
        {:else}
          <span class="rtext">{regelText(r)} - {r.anteil === 0 ? 'frei' : 'halber Tag'}{r.notiz ? ' (' + r.notiz + ')' : ''}</span>
          <button class="del" aria-label="Regel löschen" onclick={() => regelLoeschen(r.id)}><i class="fa-solid fa-xmark" aria-hidden="true"></i></button>
        {/if}
      </div>
    {/each}
  </div>
  <div class="reihe rneu">
    <select bind:value={rArt}>
      <option value="jahrestag">fester Jahrestag</option>
      <option value="wochentag">Wochentag</option>
    </select>
    {#if rArt === 'jahrestag'}
      <select bind:value={rMonat}>{#each MON.slice(1) as m, i (i)}<option value={i + 1}>{m}</option>{/each}</select>
      <input class="kz" type="number" min="1" max="31" bind:value={rTag} aria-label="Tag" />
    {:else}
      <select bind:value={rWochentag}>{#each WDV as w, i (i)}<option value={i}>{w}</option>{/each}</select>
    {/if}
    <select bind:value={rAnteil}><option value={0.5}>halber Tag</option><option value={0}>frei</option></select>
    <input placeholder="Notiz" bind:value={rNotiz} />
    <button class="btn primaer" onclick={regelHinzufuegen}>Regel hinzufügen</button>
  </div>
</section>

<style>
  .sec { font-family: var(--font-display); font-size: 11px; letter-spacing: 0.04em; text-transform: uppercase; color: var(--text-3); margin: 0 0 8px; }
  .block { margin-bottom: 22px; }
  .hinweis { font-size: 11.5px; color: var(--text-3); line-height: 1.55; margin: 8px 0 0; max-width: 80ch; }
  .atab { border: 1px solid var(--border); border-radius: var(--r-l); overflow: hidden; background: var(--surface-col); }
  .azeile { display: grid; grid-template-columns: 36px 160px 1fr auto; align-items: center; gap: 10px; padding: 7px 12px; border-top: 1px solid var(--border); font-size: 12.5px; }
  .azeile:first-child { border-top: none; }
  .cfarbe { width: 28px; height: 24px; border: 1px solid var(--border-2); border-radius: var(--r-s); background: none; padding: 0; }
  .aname { color: var(--text-1); }
  .adez { color: var(--text-3); font-size: 11.5px; }
  .rliste { display: flex; flex-direction: column; gap: 5px; margin-bottom: 10px; }
  .rzeile { display: flex; align-items: center; gap: 8px; border: 1px solid var(--border); background: var(--surface-col); border-radius: var(--r-m); padding: 7px 11px; font-size: 12.5px; }
  .rtext { flex: 1; color: var(--text-1); }
  .del { border: none; background: transparent; color: var(--text-3); font-size: 11px; }
  .del:hover { color: var(--gefahr); }
  .reihe { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
  .reihe input, .reihe select { border: 1px solid var(--border-2); background: var(--surface-2); color: var(--text-1); border-radius: var(--r-m); padding: 7px 9px; font-size: 12.5px; }
  .rneu .kz { width: 64px; }
  .btn { border: 1px solid var(--border); background: var(--surface-2); color: var(--text-2); border-radius: var(--r-m); padding: 7px 12px; font-size: 12.5px; }
  .btn.primaer { background: var(--hl-primary); color: var(--hl-on-primary); border-color: transparent; font-weight: 500; }
</style>
