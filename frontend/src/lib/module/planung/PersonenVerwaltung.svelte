<script lang="ts">
  import {
    erstellePerson, aktualisierePerson, loeschePerson, setzePersonPasswort,
    type Person,
  } from '../../api'
  import { zeigeToast } from '../../toaster.svelte'
  import { WOCHENTAGE_KURZ } from '../../zeit'

  // Personenliste mit Wochen-Soll (Stunden je Wochentag), Anlegen und
  // Zwei-Schritt-Löschen sowie Rollen und Passwörter (nur für Admins).
  let { personen, sichtbarePersonen, nurEigene, istAdmin, neuLaden }: {
    personen: Person[]
    sichtbarePersonen: Person[]
    nurEigene: boolean
    istAdmin: boolean
    neuLaden: () => Promise<void>
  } = $props()

  const WD = WOCHENTAGE_KURZ

  let neuerName = $state('')
  let neuesKuerzel = $state('')

  async function personAnlegen(): Promise<void> {
    if (!neuerName.trim()) return
    await erstellePerson({ name: neuerName.trim(), kuerzel: neuesKuerzel.trim() || null })
    neuerName = ''
    neuesKuerzel = ''
    await neuLaden()
  }
  async function stundeAendern(p: Person, i: number, wert: number): Promise<void> {
    const ws = [...p.wochenstunden]
    ws[i] = wert
    await aktualisierePerson(p.id, { wochenstunden: ws })
    await neuLaden()
  }
  // Löschen ist endgültig (inkl. Urlaubshistorie) - darum ein echter
  // Zwei-Schritt statt Sofort-Löschung am Papierkorb-Icon.
  let loeschPersonId = $state<string | null>(null)
  async function personEntfernen(p: Person): Promise<void> {
    try {
      await loeschePerson(p.id)
      await neuLaden()
    } catch (e) {
      zeigeToast(e instanceof Error ? e.message : 'Person konnte nicht gelöscht werden.')
    } finally {
      loeschPersonId = null
    }
  }

  // Passwörter (für das echte Login). Entwurf je Person bis zum Speichern.
  let pwEntwurf = $state<Record<string, string>>({})
  async function passwortSetzen(p: Person): Promise<void> {
    const pw = (pwEntwurf[p.id] ?? '').trim()
    if (!pw) return
    try {
      await setzePersonPasswort(p.id, pw)
      pwEntwurf[p.id] = ''
      await neuLaden()
      zeigeToast(`Passwort für ${p.name} gesetzt.`)
    } catch (e) {
      zeigeToast(e instanceof Error ? e.message : 'Passwort konnte nicht gesetzt werden.')
    }
  }
  async function passwortEntfernen(p: Person): Promise<void> {
    try {
      await setzePersonPasswort(p.id, '')
      await neuLaden()
      zeigeToast(`Passwort für ${p.name} entfernt.`)
    } catch (e) {
      zeigeToast(e instanceof Error ? e.message : 'Passwort konnte nicht entfernt werden.')
    }
  }

  async function rolleAendern(p: Person, wert: string): Promise<void> {
    const rolle = wert === 'admin' ? 'admin' : 'mitarbeiter'
    if (rolle === p.rolle) return
    // Aussperr-Schutz: den letzten Admin nicht herabstufen (serverseitig zusätzlich erzwungen).
    if (p.rolle === 'admin' && rolle === 'mitarbeiter' && personen.filter((x) => x.rolle === 'admin').length <= 1) {
      zeigeToast('Mindestens ein Admin muss bestehen bleiben.')
      await neuLaden() // setzt das Select optisch zurück
      return
    }
    try {
      await aktualisierePerson(p.id, { rolle })
      await neuLaden()
    } catch (e) {
      zeigeToast(e instanceof Error ? e.message : 'Rolle konnte nicht geändert werden.')
      await neuLaden()
    }
  }
</script>

<section class="block">
  <p class="sec">Personen und Wochen-Soll (Stunden je Wochentag)</p>
  <div class="tab">
    <div class="kopf"><span class="pn">Person</span>{#each WD as w (w)}<span class="wd">{w}</span>{/each}<span class="pw"></span></div>
    {#each sichtbarePersonen as p (p.id)}
      <div class="zeile">
        <span class="pn"><b>{p.kuerzel ?? ''}</b> {p.name}</span>
        {#each p.wochenstunden as h, i (i)}
          <input class="hw" type="number" min="0" max="24" step="0.5" value={h} onchange={(e) => stundeAendern(p, i, parseFloat(e.currentTarget.value) || 0)} />
        {/each}
        <span class="pw">{#if !nurEigene}<button class="del" aria-label="Person löschen" onclick={() => (loeschPersonId = loeschPersonId === p.id ? null : p.id)}><i class="fa-solid fa-trash" aria-hidden="true"></i></button>{/if}</span>
      </div>
      {#if loeschPersonId === p.id}
        <div class="ploeschen">
          <span>"{p.name}" samt Urlaubshistorie und Planungsdaten endgültig löschen?</span>
          <button class="btn geist" onclick={() => (loeschPersonId = null)}>Abbrechen</button>
          <button class="btn gefahr" onclick={() => personEntfernen(p)}>Endgültig löschen</button>
        </div>
      {/if}
    {/each}
  </div>
  {#if !nurEigene}
    <div class="neu">
      <input placeholder="Name" bind:value={neuerName} />
      <input class="kz" placeholder="Kürzel" bind:value={neuesKuerzel} />
      <button class="btn primaer" onclick={personAnlegen}>Person hinzufügen</button>
    </div>
  {/if}
</section>

{#if istAdmin}
  <section class="block">
    <p class="sec">Rollen und Passwörter</p>
    <p class="rhint">
      Admins sehen die Verwaltung (Einstellungen, Planung, Labels), Mitarbeiter nur den
      Arbeitsbereich. Hier vergibst du Passwörter; ist die Anmeldung aktiv (Einstellungen),
      melden sich Personen mit Name oder Kürzel und Passwort an, und die Rollen werden
      serverseitig durchgesetzt.
    </p>
    <div class="rollen">
      {#each personen as p (p.id)}
        <div class="rrow">
          <span class="pn"><b>{p.kuerzel ?? ''}</b> {p.name}</span>
          <select class="rsel" value={p.rolle} onchange={(e) => rolleAendern(p, e.currentTarget.value)} aria-label="Rolle">
            <option value="admin">Admin</option>
            <option value="mitarbeiter">Mitarbeiter</option>
          </select>
          <input
            class="pwfeld"
            type="password"
            autocomplete="new-password"
            placeholder={p.hat_passwort ? 'Neues Passwort' : 'Passwort setzen'}
            bind:value={pwEntwurf[p.id]}
            onkeydown={(e) => { if (e.key === 'Enter') passwortSetzen(p) }}
          />
          <button class="pwbtn" onclick={() => passwortSetzen(p)} disabled={!(pwEntwurf[p.id] ?? '').trim()}>Speichern</button>
          {#if p.hat_passwort}
            <span class="pwja" title="Passwort gesetzt"><i class="fa-solid fa-key" aria-hidden="true"></i></span>
            <button class="pwweg" onclick={() => passwortEntfernen(p)} title="Passwort entfernen" aria-label="Passwort entfernen"><i class="fa-solid fa-xmark" aria-hidden="true"></i></button>
          {/if}
        </div>
      {/each}
    </div>
  </section>
{/if}

<style>
  .sec { font-family: var(--font-display); font-size: 11px; letter-spacing: 0.04em; text-transform: uppercase; color: var(--text-3); margin: 0 0 8px; }
  .block { margin-bottom: 22px; }
  .rhint { font-size: 12px; color: var(--text-3); line-height: 1.55; margin: 0 0 10px; max-width: 70ch; }
  .rollen { border: 1px solid var(--border); border-radius: var(--r-l); overflow: hidden; background: var(--surface-col); }
  .rrow { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; padding: 7px 10px; font-size: 12.5px; }
  .rrow + .rrow { border-top: 1px solid var(--border); }
  .rrow .pn { flex: 1; min-width: 140px; }
  .rsel { border: 1px solid var(--border-2); background: var(--surface-2); color: var(--text-1); border-radius: var(--r-s); padding: 5px 8px; font-size: 12px; }
  .pwfeld { width: 150px; border: 1px solid var(--border-2); background: var(--surface-2); color: var(--text-1); border-radius: var(--r-s); padding: 5px 8px; font-size: 12px; }
  .pwbtn { border: 1px solid var(--border); background: var(--surface-2); color: var(--text-2); border-radius: var(--r-s); padding: 5px 10px; font-size: 12px; }
  .pwbtn:disabled { opacity: 0.5; }
  .pwja { color: var(--ok, #2e7d32); }
  .pwweg { border: 1px solid var(--border); background: var(--surface-2); color: var(--text-3); border-radius: var(--r-s); width: 26px; height: 26px; }
  .pwweg:hover { color: var(--gefahr, #e5484d); }
  .tab { border: 1px solid var(--border); border-radius: var(--r-l); overflow: hidden; background: var(--surface-col); }
  .kopf, .zeile { display: grid; grid-template-columns: 1fr repeat(7, 52px) 40px; align-items: center; gap: 6px; padding: 6px 10px; }
  .kopf { border-bottom: 1px solid var(--border); font-size: 10.5px; color: var(--text-3); text-transform: uppercase; }
  .zeile { border-top: 1px solid var(--border); font-size: 12.5px; }
  .kopf .wd, .zeile .hw { text-align: center; }
  .pn { color: var(--text-1); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .hw { width: 48px; border: 1px solid var(--border-2); background: var(--surface-2); color: var(--text-1); border-radius: var(--r-s); padding: 4px; font-size: 12px; font-family: var(--font-mono); }
  .del { border: none; background: transparent; color: var(--text-3); font-size: 11px; }
  .del:hover { color: var(--gefahr); }
  .neu { display: flex; gap: 8px; margin-top: 10px; flex-wrap: wrap; }
  .neu input { border: 1px solid var(--border-2); background: var(--surface-2); color: var(--text-1); border-radius: var(--r-m); padding: 7px 9px; font-size: 12.5px; }
  .neu .kz { width: 90px; }
  .btn { border: 1px solid var(--border); background: var(--surface-2); color: var(--text-2); border-radius: var(--r-m); padding: 7px 12px; font-size: 12.5px; }
  .btn.primaer { background: var(--hl-primary); color: var(--hl-on-primary); border-color: transparent; font-weight: 500; }
  .btn.geist { background: transparent; color: var(--text-2); }
  .btn.gefahr { background: var(--gefahr); border-color: transparent; color: #fff; font-weight: 500; }
  .ploeschen { display: flex; align-items: center; gap: 10px; padding: 8px 10px; border-top: 1px solid var(--border); font-size: 12px; color: var(--gefahr); background: color-mix(in srgb, var(--gefahr) 7%, transparent); }
  .ploeschen span { flex: 1; }
</style>
