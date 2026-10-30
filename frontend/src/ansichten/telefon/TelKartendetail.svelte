<script lang="ts">
  // Karte am Telefon, reduziert auf das, was man unterwegs tut: lesen (Titel, Beschreibung, Angaben), verschieben mit
  // großem Knopf, Timer starten oder anhalten, Checkliste abhaken, Kommentare lesen und schreiben; Titel, Beschreibung,
  // Fällig und Zuständig über "Bearbeiten" (eigener Weg), alles Weitere am Rechner. Der Status ändert sich über denselben
  // Weg wie das Ziehen im Board.
  import { PRIORITAETEN } from "../../anzeige";
  import { markdownHtml } from "../../teile/markdown";
  import { darf, kartenName, kartenNummer, timerErlaubt, timerVon, zeitDerKarte } from "../../daten/abfragen";
  import { bearbeiten, kommentieren } from "../../daten/anwendung/karten.svelte";
  import { anhalten, fortsetzen, starten, stoppen } from "../../daten/anwendung/timer.svelte";
  import { ICH } from "../../daten/ich";
  import { alterTage, datum, dauer, faelligText, uhrzeit, wann } from "../../daten/format";
  import { board, karte as holeKarte, konto, stand } from "../../daten/stand.svelte";
  import Person from "../../board/Person.svelte";
  import { boardPfad, gehe, wert } from "../../weg.svelte";
  import TelefonSchale from "./TelefonSchale.svelte";
  import Verschieben from "./Verschieben.svelte";
  import { telPfad } from "./weg";

  let { kartenId }: { kartenId: string } = $props();
  /** woher man kam (Heute, Hinweise), sonst führt Zurück ins Board */
  const von = $derived(wert("von"));

  // fehlt die Karte (in den Papierkorb gelegt, Anlegen rückgängig gemacht), führt die Ansicht zu den Boards zurück
  const da = $derived(!!holeKarte(kartenId));
  $effect(() => { if (!da) gehe(telPfad("/boards"), true); });
  const k = $derived(holeKarte(kartenId)!);
  const b = $derived(board(k.board));
  const spalte = $derived(b.spalten.find((s) => s.id === k.spalte)!);
  const zurueck = $derived(von === "heute" ? telPfad("/heute") : von === "hinweise" ? telPfad("/hinweise") : telPfad(boardPfad(b.kuerzel)));
  const labels = $derived(k.labels.map((l) => b.labels.find((x) => x.id === l)).filter((l) => l !== undefined));
  const felder = $derived(b.felder.filter((f) => k.felder[f.id]));
  const faellig = $derived(k.faellig && !spalte.erledigt ? faelligText(k.faellig) : null);
  const alter = $derived(alterTage(k.bewegtAm));
  const punkte = $derived(k.checkliste.filter((p) => p.erledigt).length);
  /** Zeit zeigen Karten in Boards mit Zeiterfassung, die Arbeit sind; starten lässt sich nur, wo ein Timer laufen darf */
  const mitZeit = $derived(b.module.zeiterfassung && k.art === "arbeit");
  const timer = $derived(timerVon(ICH));
  const laeuftHier = $derived(timer?.karte === k.id && !!timer.seit);
  const angehaltenHier = $derived(timer?.karte === k.id && !timer.seit);
  const andererTimer = $derived(timer && timer.karte !== k.id ? kartenName(timer.karte).schluessel : "");
  const gesamt = $derived(zeitDerKarte(k.id));
  const anteil = $derived(k.schaetzungMin ? gesamt / 60 / k.schaetzungMin : 0);
  const prioName = $derived(PRIORITAETEN.find(([p]) => p === k.prioritaet)?.[1] ?? "");
  const PRIO_KLASSE: Partial<Record<string, string>> = { hoch: "warnung", dringend: "gefahr" };

  let blattOffen = $state(false);
  let kommentar = $state("");

  /** das Feld leert sich erst, wenn der Kommentar gespeichert ist (bei getrennter Verbindung bleibt der Text stehen) */
  async function senden(): Promise<void> {
    if (await kommentieren(k.id, kommentar)) kommentar = "";
  }

  function abhaken(i: number): void {
    const liste = k.checkliste.map((p, j) => (j === i ? { ...p, erledigt: !p.erledigt } : p));
    bearbeiten(k.id, { checkliste: liste }, liste[i].erledigt ? `Punkt "${liste[i].text}" erledigt` : `Punkt "${liste[i].text}" wieder offen`);
  }
  /** Beschreibung und Kommentare sind Markdown, dargestellt mit demselben sicheren Darsteller wie am Rechner */
  const md = { erwaehnung: (w: string) => stand.konten.find((x) => x.name.split(" ")[0].toLowerCase() === w.toLowerCase())?.name };
</script>

{#if da}
  <TelefonSchale titel={k.schluessel} kopierbar unter={b.name} reiter="boards" {zurueck} karte={k.id}>
    <section class="pw-tel-kopfblock">
      {#if labels.length}<div class="labels">{#each labels as l (l.id)}<span class="pw-label" data-farbe={l.farbe}>{l.name}</span>{/each}</div>{/if}
      <h2 class="pw-tel-kartentitel">{k.titel}</h2>
      {#if k.art === "idee"}<span class="pw-angabe pw-tel-idee"><i class="fa-solid fa-lightbulb"></i>Idee</span>{/if}
      {#if k.blockiert}<div class="hinweis gefahr"><i class="fa-solid fa-ban"></i><div><b>Blockiert:</b> {k.blockiert}</div></div>{/if}
      {#if darf(b, "karten.bearbeiten")}
        <a class="knopf pw-tel-breit" href={telPfad(boardPfad(b.kuerzel, `${kartenNummer(k)}/bearbeiten`), von ? { von } : {})}>
          <i class="fa-solid fa-pen"></i>Bearbeiten</a>
      {/if}
    </section>

    <section class="pw-tel-abschnitt" aria-label="Status">
      <div class="etikett">Status</div>
      <div class="pw-tel-status">
        <span class="zustand" data-farbe={spalte.farbe}><span class="pw-farbpunkt"></span>{spalte.name}</span>
        {#if spalte.erledigt && k.abgeschlossen}
          <span class="schwach">erledigt {datum(k.abgeschlossen, true)}</span>
        {:else}
          <span class="schwach">{#if alter === 0}seit heute{:else}seit <span class="zahl">{alter}</span> {alter === 1 ? "Tag" : "Tagen"}{/if}</span>
        {/if}
      </div>
      <button class="knopf haupt pw-tel-breit" onclick={() => (blattOffen = true)}><i class="fa-solid fa-arrow-right-arrow-left"></i>Verschieben nach</button>
    </section>

    <section class="pw-tel-abschnitt" aria-label="Angaben">
      <div class="etikett">Angaben</div>
      <div class="pw-tel-angaben">
        <span class="name"><i class="fa-regular fa-calendar"></i>Fällig</span>
        <span class="wert">{#if k.faellig}{#if faellig?.klasse}<span class="pw-angabe {faellig.klasse}">{faellig.text}</span>{/if}{datum(k.faellig, true)}{:else}<span class="schwach">ohne</span>{/if}</span>
        <span class="name"><i class="fa-solid fa-flag"></i>Priorität</span>
        <span class="wert">{#if PRIO_KLASSE[k.prioritaet]}<span class="pw-angabe {PRIO_KLASSE[k.prioritaet]}">{prioName}</span>{:else}{prioName}{/if}</span>
        <span class="name"><i class="fa-solid fa-user"></i>Zuständig</span>
        <span class="wert personen">
          {#each k.zustaendig as p (p)}<span class="person"><Person id={p} />{konto(p).name}</span>{:else}<span class="schwach">niemand</span>{/each}
        </span>
        {#each felder as f (f.id)}
          <span class="name"><i class="fa-solid {f.art === 'zahl' ? 'fa-hashtag' : f.art === 'auswahl' ? 'fa-list' : 'fa-font'}"></i>{f.name}</span>
          <span class="wert">{k.felder[f.id]}</span>
        {/each}
      </div>
    </section>

    {#if mitZeit}
      <section class="pw-tel-abschnitt" aria-label="Zeiterfassung">
        <div class="etikett">Zeit</div>
        <div class="pw-tel-uhr" class:laeuft={laeuftHier}>
          <div class="oben">
            {#if laeuftHier}
              <span class="zustand laeuft"><i class="fa-solid fa-circle-play"></i>Läuft seit {uhrzeit(timer!.seit!)}</span>
            {:else if angehaltenHier}
              <span class="zustand pausiert"><i class="fa-solid fa-circle-pause"></i>Angehalten</span>
            {:else}
              <span class="zustand">Gesamt</span>
            {/if}
            <b class="zahl stand">{dauer(gesamt, true)}</b>
          </div>
          {#if k.schaetzungMin}
            <div class="pw-fortschritt zeit" class:ueber={anteil > 1}><span style="width: {Math.min(100, anteil * 100)}%"></span></div>
            <span class="schaetzung" class:warnung={anteil > 1}>{Math.round(anteil * 100)} % von <span class="zahl">{dauer(k.schaetzungMin * 60)}</span> Stunden{anteil > 1 ? ", überschritten" : ""}</span>
          {/if}
          <div class="knoepfe">
            {#if laeuftHier}
              <button class="knopf" onclick={anhalten}><i class="fa-solid fa-pause"></i>Anhalten</button>
              <button class="knopf" onclick={stoppen}><i class="fa-solid fa-stop"></i>Stopp</button>
            {:else if angehaltenHier}
              <button class="knopf" onclick={fortsetzen}><i class="fa-solid fa-play"></i>Fortsetzen</button>
              <button class="knopf" onclick={stoppen}><i class="fa-solid fa-stop"></i>Stopp</button>
            {:else if timerErlaubt(k)}
              <button class="knopf" onclick={() => starten(k.id)}><i class="fa-solid fa-play"></i>Start</button>
            {/if}
            {#if timerErlaubt(k)}
              <a class="knopf ohne" href={telPfad("/zeiten", { karte: k.schluessel })}><i class="fa-solid fa-plus"></i>Nachbuchen</a>
            {/if}
          </div>
          {#if andererTimer && timerErlaubt(k)}
            <span class="schwach klein">Start beendet deinen Timer auf {andererTimer} und bucht ihn.</span>
          {/if}
        </div>
      </section>
    {/if}

    {#if k.checkliste.length}
      <section class="pw-tel-abschnitt" aria-label="Checkliste">
        <div class="etikett">Checkliste<span class="zaehler" class:erfolg={punkte === k.checkliste.length}>{punkte}/{k.checkliste.length}</span></div>
        <div class="pw-fortschritt"><span style="width: {(100 * punkte) / k.checkliste.length}%"></span></div>
        {#each k.checkliste as p, i (i)}
          <label class="pw-tel-punkt" class:erledigt={p.erledigt}><input type="checkbox" checked={p.erledigt} onchange={() => abhaken(i)} /><span>{p.text}</span></label>
        {/each}
      </section>
    {/if}

    {#if k.beschreibung}
      <section class="pw-tel-abschnitt" aria-label="Beschreibung">
        <div class="etikett">Beschreibung</div>
        <div class="pw-tel-text pw-md">{@html markdownHtml(k.beschreibung, md)}</div>
      </section>
    {/if}

    <section class="pw-tel-abschnitt" aria-label="Kommentare">
      <div class="etikett">Kommentare<span class="zaehler">{k.kommentare.length}</span></div>
      {#each k.kommentare as c, i (i)}
        <div class="pw-tel-kommentar">
          <Person id={c.von} />
          <div class="blase"><div class="kopfzeile"><b>{konto(c.von).name}</b><span>{wann(c.zeit)}</span></div>
            <div class="pw-md">{@html markdownHtml(c.text, md)}</div></div>
        </div>
      {/each}
      <div class="pw-tel-schreiben">
        <textarea class="eingabe" rows="2" bind:value={kommentar} placeholder="Kommentar schreiben; mit @ erwähnen"></textarea>
        <button class="knopf" disabled={!kommentar.trim()} onclick={senden}><i class="fa-solid fa-paper-plane"></i>Senden</button>
      </div>
    </section>

    {#snippet blatt()}
      {#if blattOffen}<Verschieben karte={k} schliessen={() => (blattOffen = false)} />{/if}
    {/snippet}
  </TelefonSchale>
{/if}
