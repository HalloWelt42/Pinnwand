<script lang="ts">
  import {
    ladePersonen, ladeUrlaubskonten, ladeLaender, ladeFeiertage,
    type Person, type Urlaubskonto, type Feiertag, type Region,
  } from '../../api'
  import { personSicht } from '../../personSicht.svelte'
  import { aktiveRolle, eigenePersonId as leiteEigeneId } from '../../identitaet'
  import { auth } from '../../auth.svelte'
  import PersonenVerwaltung from './PersonenVerwaltung.svelte'
  import WochenOverrideBlock from './WochenOverrideBlock.svelte'
  import UrlaubVerwaltung from './UrlaubVerwaltung.svelte'
  import FeiertageImport from './FeiertageImport.svelte'
  import AbwesenheitKonfig from './AbwesenheitKonfig.svelte'

  // Orchestrator der Planung: lädt die geteilten Daten (Personen, Konten,
  // Länder, Feiertage), leitet die Rechte ab und delegiert die Abschnitte
  // an fokussierte Unterkomponenten.
  let { boardId }: { boardId: string } = $props()
  $effect(() => void boardId)

  const jahr = new Date().getFullYear()

  let personen = $state<Person[]>([])
  // Rolle/Identität konsistent zur App: bei aktivem Login zählt die angemeldete
  // Person, sonst die gewählte Personen-Sicht ("Alle" == Admin-Vollsicht).
  const eigenePersonId = $derived(leiteEigeneId(auth, personSicht.id))
  const istAdmin = $derived(aktiveRolle(auth, personen, personSicht.id) === 'admin')
  // Mitarbeiter pflegen ausschließlich ihre eigenen Planungsdaten (Self-Service).
  const nurEigene = $derived(!istAdmin && eigenePersonId !== null)
  const sichtbarePersonen = $derived(nurEigene ? personen.filter((p) => p.id === eigenePersonId) : personen)

  let konten = $state<Record<string, Urlaubskonto>>({})
  let laender = $state<Record<string, Region[]>>({})
  let feiertage = $state<Feiertag[]>([])
  let meldung = $state('')

  const deRegionen = $derived(laender['DE'] ?? [])

  function melde(text: string): void {
    meldung = text
  }

  async function ladenPersonen(): Promise<void> {
    personen = await ladePersonen()
    await ladenKonten()
  }
  async function ladenKonten(): Promise<void> {
    try {
      const liste = await ladeUrlaubskonten(jahr)
      konten = Object.fromEntries(liste.map((k) => [k.person_id, k]))
    } catch { /* Planung bleibt nutzbar */ }
  }
  async function feiertageNeuLaden(): Promise<void> {
    feiertage = await ladeFeiertage(`${jahr}-01-01`, `${jahr}-12-31`)
  }

  $effect(() => { ladenPersonen() })
  $effect(() => {
    ladeLaender().then((d) => (laender = d.laender)).catch(() => {})
    feiertageNeuLaden().catch(() => {})
  })
</script>

<div class="planung">
  {#if meldung}<p class="meldung">{meldung}</p>{/if}

  <PersonenVerwaltung {personen} {sichtbarePersonen} {nurEigene} {istAdmin} neuLaden={ladenPersonen} />

  <WochenOverrideBlock {personen} {sichtbarePersonen} {nurEigene} {eigenePersonId} {melde} />

  <UrlaubVerwaltung
    {personen}
    {sichtbarePersonen}
    {nurEigene}
    {eigenePersonId}
    {konten}
    {deRegionen}
    {jahr}
    personenNeuLaden={ladenPersonen}
    kontenNeuLaden={ladenKonten}
    {feiertageNeuLaden}
    {melde}
  />

  {#if istAdmin}
    <FeiertageImport {laender} {feiertage} {jahr} {melde} {feiertageNeuLaden} />
    <AbwesenheitKonfig kontenNeuLaden={ladenKonten} />
  {/if}
</div>

<style>
  .planung { height: 100%; overflow-y: auto; padding: 16px; max-width: 920px; }
  .meldung { color: var(--ok); font-size: 12px; margin: 0 0 10px; }
</style>
