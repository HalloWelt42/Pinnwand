<script lang="ts">
  // Papierkorb eines Boards: gelöschte Karten und Spalten mit allem, was dranhängt (Zeiten, Kommentare, Anhänge,
  // Verknüpfungen), wer sie wann gelöscht hat und wo sie lagen. Wiederherstellen bringt alles an die alte Stelle zurück,
  // mit demselben Schlüssel; das darf, wer den Papierkorb sieht. Endgültig entfernen gibt es nur mit dem Recht
  // "Papierkorb leeren" und nach einer Rückfrage in der Fläche, die nennt, was verloren geht; die gebuchte Zeit bleibt.
  import { darf, papierkorbVon } from "../../daten/abfragen";
  import { eintragName, entfernen, wiederherstellen } from "../../daten/anwendung/papierkorb.svelte";
  import { ICH } from "../../daten/ich";
  import { datum, dauer, wann } from "../../daten/format";
  import { board as holeBoard, konto, stand } from "../../daten/stand.svelte";
  import Person from "../../board/Person.svelte";
  import type { Geloescht, Karte } from "../../modell";
  import NebenKopf from "./NebenKopf.svelte";

  let { boardId, entwurf = "" }: { boardId: string; entwurf?: string } = $props();
  const b = $derived(holeBoard(boardId));
  const eintraege = $derived(papierkorbVon(b.id));
  const rolle = $derived(b.rollen.find((r) => r.id === b.mitglieder.find((m) => m.konto === ICH)?.rolle));
  const darfLeeren = $derived(darf(b, "papierkorb.leeren"));

  /** offene Rückfrage in der Fläche: Kennung eines Eintrags oder "alle" (Zustand der Ansicht) */
  let rueckfrage = $state("");
  const rueckfrageVorgefuehrt = $derived(entwurf === "rueckfrage" ? "p-123" : "");
  $effect(() => { rueckfrage = rueckfrageVorgefuehrt; });

  /** gebuchte Zeit einer Karte je Person (bleibt in den Zeiteinträgen, auch im Papierkorb) */
  function zeitenVon(k: Karte): { konto: string; sek: number }[] {
    const m = new Map<string, number>();
    for (const z of stand.zeiteintraege.filter((x) => x.karte === k.id)) m.set(z.konto, (m.get(z.konto) ?? 0) + z.sekunden);
    return [...m].map(([konto, sek]) => ({ konto, sek }));
  }
  function sekunden(k: Karte): number {
    return zeitenVon(k).reduce((s, z) => s + z.sek, 0);
  }
  function verknuepft(k: Karte): string[] {
    return k.gruppe ? stand.karten.filter((x) => x.gruppe === k.gruppe && x.id !== k.id).map((x) => x.schluessel) : [];
  }
  /** Serie einer Serienkarte und was die Serie über ihren Tag weiß */
  function serie(k: Karte): string {
    const s = stand.serien.find((x) => x.id === k.serie);
    if (!s || !k.faellig) return "";
    const tag = datum(k.faellig, true);
    if (s.verworfen.includes(k.faellig)) return `Serie ${s.titel}, ${tag} fand nicht statt`;
    if (s.auslass.some((a) => a.tag === k.faellig)) return `Serie ${s.titel}, ${tag} ausgelassen`;
    return `Serie ${s.titel}, ${tag}`;
  }
  function stelle(e: Geloescht): string {
    if (e.art === "spalte") {
      const vor = b.spalten[e.stelle.platz - 1]?.name;
      const nach = b.spalten[e.stelle.platz]?.name;
      return vor && nach ? `stand zwischen ${vor} und ${nach}` : vor ? `stand nach ${vor}` : "stand vorn";
    }
    const sp = b.spalten.find((s) => s.id === e.stelle.spalte);
    return sp ? `lag in ${sp.name} an ${e.stelle.platz + 1}. Stelle` : "ihre Spalte gibt es nicht mehr, sie kommt in die erste";
  }
  function aufzaehlen(teile: string[]): string {
    return teile.length > 1 ? `${teile.slice(0, -1).join(", ")} und ${teile.at(-1)}` : teile[0] ?? "";
  }
  /** was beim endgültigen Entfernen verloren geht, in Worten; die gebuchte Zeit bleibt */
  function verlust(liste: Geloescht[]): string {
    const karten = liste.flatMap((e) => e.karten);
    const sek = karten.reduce((s, k) => s + sekunden(k), 0);
    const kommentare = karten.reduce((s, k) => s + k.kommentare.length, 0);
    const anhaenge = karten.reduce((s, k) => s + k.anhaenge.length, 0);
    const gruppe = [...new Set(karten.flatMap(verknuepft))];
    const teile = [
      ...(liste.some((e) => e.art === "spalte") || karten.length > 1 ? [`${karten.length} Karten`] : []),
      ...(kommentare ? [`${kommentare} ${kommentare === 1 ? "Kommentar" : "Kommentare"}`] : []),
      ...(anhaenge ? [`${anhaenge} ${anhaenge === 1 ? "Anhang" : "Anhänge"} in der Kellerwolke`] : []),
      ...(gruppe.length ? [`die Verknüpfung mit ${aufzaehlen(gruppe)}`] : []),
    ];
    return (teile.length ? `Verloren gehen ${aufzaehlen(teile)}.` : "")
      + (sek ? ` Die gebuchte Zeit (${dauer(sek)}) bleibt in den Zeitkonten.` : "");
  }
</script>

{#snippet dran(k: Karte)}
  {@const punkte = k.checkliste.filter((p) => p.erledigt).length}
  {@const gruppe = verknuepft(k)}
  <div class="dran">
    {#each k.labels as l (l)}{@const lab = b.labels.find((x) => x.id === l)}{#if lab}<span class="pw-label" data-farbe={lab.farbe}>{lab.name}</span>{/if}{/each}
    {#if k.zustaendig.length}<span class="pw-personen" title={k.zustaendig.map((p) => konto(p).name).join(", ")}>{#each k.zustaendig as p (p)}<Person id={p} />{/each}</span>{/if}
    {#if sekunden(k)}
      {@const personen = zeitenVon(k)}
      <span class="pw-angabe flaeche" title="Gebuchte Zeit; sie bleibt in den Zeitkonten, auch nach dem Entfernen">
        <i class="fa-regular fa-clock"></i>{dauer(sekunden(k))}<span class="schwach">({personen.map((p) => `${konto(p.konto).name} ${dauer(p.sek)}`).join(", ")})</span></span>
    {/if}
    {#if k.kommentare.length}<span class="pw-angabe flaeche"><i class="fa-regular fa-comment"></i>{k.kommentare.length} {k.kommentare.length === 1 ? "Kommentar" : "Kommentare"}</span>{/if}
    {#if k.anhaenge.length}<span class="pw-angabe flaeche" title={k.anhaenge.map((a) => a.name).join(", ")}><i class="fa-solid fa-paperclip"></i>{k.anhaenge.length} {k.anhaenge.length === 1 ? "Anhang" : "Anhänge"}</span>{/if}
    {#if k.checkliste.length}<span class="pw-angabe flaeche"><i class="fa-regular fa-square-check"></i>{punkte}/{k.checkliste.length}</span>{/if}
    {#if gruppe.length}<span class="pw-angabe flaeche" title="Verknüpfte Aufgaben mit geteilter Zeit; Wiederherstellen fügt die Karte wieder in die Gruppe">
      <i class="fa-solid fa-link pw-akzent"></i>mit {gruppe.join(", ")}</span>{/if}
    {#if serie(k)}<span class="pw-angabe flaeche" title="Karte aus einer Serie"><i class="fa-solid fa-repeat"></i>{serie(k)}</span>{/if}
  </div>
{/snippet}

{#snippet rueckfrageFlaeche(liste: Geloescht[], name: string)}
  <div class="bestaetigen" role="alert">
    <i class="fa-solid fa-triangle-exclamation"></i>
    <div class="frage"><b>{name} endgültig entfernen?</b> {verlust(liste)} Das lässt sich nicht rückgängig machen.</div>
    <span class="rechts">
      <button class="knopf klein" onclick={() => (rueckfrage = "")}>Abbrechen</button>
      <button class="knopf gefahr-voll klein" onclick={() => { entfernen(liste.map((e) => e.id)); rueckfrage = ""; }}>
        <i class="fa-solid fa-xmark"></i>Endgültig entfernen</button>
    </span>
  </div>
{/snippet}

<div class="pw-uebersicht-seite">
  <div class="rahmen-kopf">
    <NebenKopf board={b} titel="Papierkorb" symbol="fa-trash-can" angabe="{eintraege.length} {eintraege.length === 1 ? 'Eintrag' : 'Einträge'}"
               erklaerung="Gelöschte Karten und Spalten mit allem, was dranhängt. Wiederherstellen bringt sie mit demselben Schlüssel an die alte Stelle zurück. Endgültig entfernen darf nur, wer das Recht Papierkorb leeren hat{rolle ? ` (deine Rolle: ${rolle.name})` : ''}.">
      {#snippet aktionen()}
        {#if darfLeeren && eintraege.length}
          <button class="knopf ohne gefahr klein" onclick={() => (rueckfrage = "alle")}><i class="fa-solid fa-broom"></i>Papierkorb leeren</button>
        {/if}
      {/snippet}
    </NebenKopf>
  </div>

  <div class="rollfeld">
    {#if rueckfrage === "alle" && eintraege.length}
      <div class="pw-uebersicht-geloescht-alle">{@render rueckfrageFlaeche(eintraege, `Alle ${eintraege.length} Einträge`)}</div>
    {/if}
    {#if !darfLeeren && eintraege.length}
      <div class="hinweis pw-uebersicht-geloescht-alle"><i class="fa-solid fa-lock"></i>
        <div>Wiederherstellen kannst du; endgültig entfernen darf nur, wer das Recht Papierkorb leeren hat.</div></div>
    {/if}
    {#each eintraege as e (e.id)}
      {@const k = e.karten[0]}
      <article class="karte pw-uebersicht-geloescht" class:gewaehlt={rueckfrage === e.id} aria-label={eintragName(e)}>
        <div class="kopfzeile">
          {#if e.art === "spalte" && e.spalte}
            <span class="zustand"><i class="fa-solid fa-table-columns"></i>Spalte</span>
            <span class="name"><span class="pw-farbpunkt" data-farbe={e.spalte.farbe}></span>{e.spalte.name}</span>
            <span class="zaehler">{e.karten.length} Karten</span>
          {:else}
            <span class="zustand"><i class="fa-solid fa-note-sticky"></i>Karte</span>
            <span class="name"><span class="pw-schluessel">{k.schluessel}</span> {k.titel}</span>
          {/if}
          <span class="rechts">
            <button class="knopf klein" title="An die alte Stelle zurück, mit Schlüssel, Zeiten, Kommentaren, Anhängen und Verknüpfungen"
                    onclick={() => wiederherstellen(e.id)}><i class="fa-solid fa-trash-arrow-up"></i>Wiederherstellen</button>
            {#if darfLeeren}
              <button class="knopf ohne gefahr klein" onclick={() => (rueckfrage = e.id)}><i class="fa-solid fa-xmark"></i>Endgültig entfernen</button>
            {/if}
          </span>
        </div>
        <div class="wer"><Person id={e.von} /><span>Gelöscht von {konto(e.von).name} · {wann(e.am)} · {stelle(e)}</span></div>
        {#if e.art === "spalte"}
          {#each e.karten as x (x.id)}
            <div class="unterkarte"><span class="name"><span class="pw-schluessel">{x.schluessel}</span> {x.titel}</span>{@render dran(x)}</div>
          {/each}
        {:else}
          {@render dran(k)}
        {/if}
        {#if rueckfrage === e.id}{@render rueckfrageFlaeche([e], eintragName(e))}{/if}
      </article>
    {:else}
      <div class="leer"><i class="fa-solid fa-trash-can"></i><h2>Der Papierkorb ist leer</h2>
        <p>Gelöschte Karten und Spalten dieses Boards landen hier und lassen sich mit allem, was dranhängt, wiederherstellen.</p></div>
    {/each}
  </div>
</div>
