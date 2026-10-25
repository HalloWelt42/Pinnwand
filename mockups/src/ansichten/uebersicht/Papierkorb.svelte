<script lang="ts">
  // Papierkorb eines Boards: gelöschte Karten und Spalten mit allem, was dranhängt (Zeiten, Kommentare, Anhänge,
  // Verknüpfungen), wer sie wann gelöscht hat und wo sie lagen. Wiederherstellen bringt alles an die alte Stelle zurück,
  // mit demselben Schlüssel. Endgültig entfernen gibt es nur mit dem Recht "Papierkorb leeren" und nur nach einer
  // Rückfrage in der Fläche, die nennt, was verloren geht.
  import { ICH, SERIEN } from "../../beispiel/daten";
  import { datum, dauer, wann } from "../../beispiel/format";
  import { board as holeBoard, konto, stand } from "../../beispiel/stand.svelte";
  import Person from "../../board/Person.svelte";
  import type { Karte } from "../../modell";
  import { eintragName, entfernen, uebersicht, wiederherstellen } from "./aktionen.svelte";
  import Meldung from "./Meldung.svelte";
  import type { Geloescht } from "./modell";
  import NebenKopf from "./NebenKopf.svelte";

  let { boardId, entwurf = "" }: { boardId: string; entwurf?: string } = $props();
  const b = $derived(holeBoard(boardId));
  const eintraege = $derived(uebersicht.papierkorb.filter((e) => e.board === b.id));
  const rolle = $derived(b.rollen.find((r) => r.id === b.mitglieder.find((m) => m.konto === ICH)?.rolle));
  const darfLeeren = $derived(!!rolle?.rechte.includes("papierkorb.leeren"));

  /** offene Rückfrage: Kennung eines Eintrags oder "alle" */
  let rueckfrage = $state("");
  $effect(() => { rueckfrage = entwurf === "rueckfrage" ? "p-134" : ""; });

  function sekunden(e: Geloescht): number {
    return e.karten.reduce((s, k) => s + k.erfasstSek, 0);
  }
  function jePerson(e: Geloescht): { konto: string; sek: number }[] {
    const m = new Map<string, number>();
    for (const z of e.zeiten) m.set(z.konto, (m.get(z.konto) ?? 0) + z.sekunden);
    return [...m].map(([k, sek]) => ({ konto: k, sek }));
  }
  function verknuepft(k: Karte): string[] {
    return k.gruppe ? stand.karten.filter((x) => x.gruppe === k.gruppe && x.id !== k.id).map((x) => x.schluessel) : [];
  }
  function serie(k: Karte): string {
    return SERIEN.find((s) => s.id === k.serie)?.titel ?? "";
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
  /** was beim endgültigen Entfernen verloren geht, in Worten */
  function verlust(liste: Geloescht[]): string {
    const karten = liste.flatMap((e) => e.karten);
    const sek = liste.reduce((s, e) => s + sekunden(e), 0);
    const personen = [...new Set(liste.flatMap((e) => e.zeiten.map((z) => z.konto)))].map((p) => konto(p).name);
    const kommentare = karten.reduce((s, k) => s + k.kommentare.length, 0);
    const anhaenge = karten.reduce((s, k) => s + k.anhaenge.length, 0);
    const gruppe = [...new Set(karten.flatMap(verknuepft))];
    const teile = [
      ...(liste.some((e) => e.art === "spalte") || karten.length > 1 ? [`${karten.length} Karten`] : []),
      ...(sek ? [`${dauer(sek)} gebuchte Zeit${personen.length ? ` aus den Zeitkonten von ${aufzaehlen(personen)}` : ""}`] : []),
      ...(kommentare ? [`${kommentare} ${kommentare === 1 ? "Kommentar" : "Kommentare"}`] : []),
      ...(anhaenge ? [`${anhaenge} ${anhaenge === 1 ? "Anhang" : "Anhänge"} in der Kellerwolke`] : []),
      ...(gruppe.length ? [`die Verknüpfung mit ${aufzaehlen(gruppe)}`] : []),
    ];
    return teile.length ? `Verloren gehen ${aufzaehlen(teile)}.` : "";
  }
</script>

{#snippet dran(k: Karte, e: Geloescht)}
  {@const punkte = k.checkliste.filter((p) => p.erledigt).length}
  {@const gruppe = verknuepft(k)}
  <div class="dran">
    {#each k.labels as l (l)}{@const lab = b.labels.find((x) => x.id === l)}{#if lab}<span class="pw-label" data-farbe={lab.farbe}>{lab.name}</span>{/if}{/each}
    {#if k.zustaendig.length}<span class="pw-personen" title={k.zustaendig.map((p) => konto(p).name).join(", ")}>{#each k.zustaendig as p (p)}<Person id={p} />{/each}</span>{/if}
    {#if k.erfasstSek}
      {@const personen = e.zeiten.filter((z) => z.karte === k.id).length ? jePerson({ ...e, zeiten: e.zeiten.filter((z) => z.karte === k.id) }) : []}
      <span class="pw-angabe flaeche" title="Gebuchte Zeit; zählt bis zum endgültigen Entfernen in den Zeitkonten">
        <i class="fa-regular fa-clock"></i>{dauer(k.erfasstSek)}{#if personen.length}<span class="schwach">({personen.map((p) => `${konto(p.konto).kuerzel} ${dauer(p.sek)}`).join(", ")})</span>{/if}</span>
    {/if}
    {#if k.kommentare.length}<span class="pw-angabe flaeche"><i class="fa-regular fa-comment"></i>{k.kommentare.length} {k.kommentare.length === 1 ? "Kommentar" : "Kommentare"}</span>{/if}
    {#if k.anhaenge.length}<span class="pw-angabe flaeche" title={k.anhaenge.map((a) => a.name).join(", ")}><i class="fa-solid fa-paperclip"></i>{k.anhaenge.length} {k.anhaenge.length === 1 ? "Anhang" : "Anhänge"}</span>{/if}
    {#if k.checkliste.length}<span class="pw-angabe flaeche"><i class="fa-regular fa-square-check"></i>{punkte}/{k.checkliste.length}</span>{/if}
    {#if gruppe.length}<span class="pw-angabe flaeche" title="Verknüpfte Aufgaben mit geteilter Zeit; Wiederherstellen fügt die Karte wieder in die Gruppe">
      <i class="fa-solid fa-link pw-akzent"></i>mit {gruppe.join(", ")}</span>{/if}
    {#if k.serie}<span class="pw-angabe flaeche" title="Der Tag wird von der Serie ausgelassen; Wiederherstellen hebt das auf">
      <i class="fa-solid fa-repeat"></i>Serie {serie(k)}, {datum(k.faellig ?? "", true)} ausgelassen</span>{/if}
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
            <div class="unterkarte"><span class="name"><span class="pw-schluessel">{x.schluessel}</span> {x.titel}</span>{@render dran(x, e)}</div>
          {/each}
        {:else}
          {@render dran(k, e)}
        {/if}
        {#if rueckfrage === e.id}{@render rueckfrageFlaeche([e], eintragName(e))}{/if}
      </article>
    {:else}
      <div class="leer"><i class="fa-solid fa-trash-can"></i><h2>Der Papierkorb ist leer</h2>
        <p>Gelöschte Karten und Spalten dieses Boards landen hier und lassen sich mit allem, was dranhängt, wiederherstellen.</p></div>
    {/each}
  </div>
  <Meldung />
</div>
