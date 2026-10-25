<script lang="ts">
  // Karte am Telefon, reduziert auf das, was man unterwegs tut: lesen (Titel, Beschreibung, Angaben), verschieben mit
  // großem Knopf, Timer starten oder anhalten, Checkliste abhaken, Kommentare lesen und schreiben. Bearbeiten der Felder
  // bleibt am Rechner. Der Status ändert sich über denselben Weg wie das Ziehen im Board.
  import { ICH } from "../../beispiel/daten";
  import { alterTage, datum, dauer, faelligText, uhrzeit, wann } from "../../beispiel/format";
  import { board, karte as holeKarte, konto } from "../../beispiel/stand.svelte";
  import Person from "../../board/Person.svelte";
  import { boardPfad, wert } from "../../weg.svelte";
  import { anhalten, kartenzeit, kommentieren, laufende, starten, stoppen, telefon } from "./aktionen.svelte";
  import TelefonSchale from "./TelefonSchale.svelte";
  import Verschieben from "./Verschieben.svelte";
  import { telPfad } from "./weg";

  let { kartenId, entwurf = "" }: { kartenId: string; entwurf?: string } = $props();
  /** woher man kam (Heute, Hinweise), sonst führt Zurück ins Board */
  const von = $derived(wert("von"));

  const k = $derived(holeKarte(kartenId)!);
  const b = $derived(board(k.board));
  const spalte = $derived(b.spalten.find((s) => s.id === k.spalte)!);
  const zurueck = $derived(von === "heute" ? telPfad("/heute") : von === "hinweise" ? telPfad("/hinweise") : telPfad(boardPfad(b.kuerzel)));
  const labels = $derived(k.labels.map((l) => b.labels.find((x) => x.id === l)).filter((l) => l !== undefined));
  const felder = $derived(b.felder.filter((f) => k.felder[f.id]));
  const faellig = $derived(k.faellig && !spalte.erledigt ? faelligText(k.faellig) : null);
  const alter = $derived(alterTage(k.bewegtAm));
  const punkte = $derived(k.checkliste.filter((p) => p.erledigt).length);
  const mitZeit = $derived(b.module.zeiterfassung && k.art === "arbeit");
  const laeuftHier = $derived(k.laeuft?.konto === ICH);
  const pausiertHier = $derived(telefon.pausiert === k.id);
  const andererTimer = $derived(laufende()?.id !== k.id ? laufende() : undefined);
  const gesamt = $derived(kartenzeit(k));
  const anteil = $derived(k.schaetzungMin ? gesamt / 60 / k.schaetzungMin : 0);
  const PRIO = { keine: ["Keine", ""], niedrig: ["Niedrig", ""], mittel: ["Mittel", ""], hoch: ["Hoch", "warnung"], dringend: ["Dringend", "gefahr"] } as const;

  let blattOffen = $state(false);
  $effect(() => { blattOffen = entwurf === "verschieben"; });
  let kommentar = $state("");

  function senden(): void {
    if (!kommentar.trim()) return;
    kommentieren(k.id, kommentar);
    kommentar = "";
  }
  const erwaehnungen = (text: string): string =>
    text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/@(\w+)/g, '<span class="erwaehnt">@$1</span>');
</script>

<TelefonSchale titel={k.schluessel} unter={b.name} reiter="boards" {zurueck} karte={k.id}>
  <section class="pw-tel-kopfblock">
    {#if labels.length}<div class="labels">{#each labels as l (l.id)}<span class="pw-label" data-farbe={l.farbe}>{l.name}</span>{/each}</div>{/if}
    <h2 class="pw-tel-kartentitel">{k.titel}</h2>
    {#if k.art === "idee"}<span class="pw-angabe pw-tel-idee"><i class="fa-solid fa-lightbulb"></i>Idee</span>{/if}
    {#if k.blockiert}<div class="hinweis gefahr"><i class="fa-solid fa-ban"></i><div><b>Blockiert:</b> {k.blockiert}</div></div>{/if}
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
      <span class="wert">{#if PRIO[k.prioritaet][1]}<span class="pw-angabe {PRIO[k.prioritaet][1]}">{PRIO[k.prioritaet][0]}</span>{:else}{PRIO[k.prioritaet][0]}{/if}</span>
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
            <span class="zustand laeuft"><i class="fa-solid fa-circle-play"></i>Läuft seit {uhrzeit(k.laeuft!.seit)}</span>
          {:else if pausiertHier}
            <span class="zustand pausiert"><i class="fa-solid fa-circle-pause"></i>Angehalten</span>
          {:else}
            <span class="zustand">Gesamt</span>
          {/if}
          <b class="zahl stand">{dauer(gesamt, true)}</b>
        </div>
        {#if k.schaetzungMin}
          <div class="pw-fortschritt zeit" class:ueber={anteil > 1}><span style="width: {Math.min(100, anteil * 100)}%"></span></div>
          <span class="schaetzung" class:warnung={anteil > 1}>{Math.round(anteil * 100)} % von <span class="zahl">{dauer(k.schaetzungMin * 60)}</span> Std{anteil > 1 ? ", überschritten" : ""}</span>
        {/if}
        <div class="knoepfe">
          {#if laeuftHier}
            <button class="knopf" onclick={anhalten}><i class="fa-solid fa-pause"></i>Anhalten</button>
            <button class="knopf" onclick={stoppen}><i class="fa-solid fa-stop"></i>Stopp</button>
          {:else if pausiertHier}
            <button class="knopf" onclick={() => starten(k.id)}><i class="fa-solid fa-play"></i>Fortsetzen</button>
            <button class="knopf" onclick={stoppen}><i class="fa-solid fa-stop"></i>Stopp</button>
          {:else if !spalte.erledigt}
            <button class="knopf" onclick={() => starten(k.id)}><i class="fa-solid fa-play"></i>Start</button>
          {/if}
          <a class="knopf ohne" href={telPfad("/zeiten", { karte: k.schluessel })}><i class="fa-solid fa-plus"></i>Nachbuchen</a>
        </div>
        {#if andererTimer && !spalte.erledigt}
          <span class="schwach klein">Start hält {andererTimer.schluessel} an und bucht dessen Zeit.</span>
        {/if}
      </div>
    </section>
  {/if}

  {#if k.checkliste.length}
    <section class="pw-tel-abschnitt" aria-label="Checkliste">
      <div class="etikett">Checkliste<span class="zaehler" class:erfolg={punkte === k.checkliste.length}>{punkte}/{k.checkliste.length}</span></div>
      <div class="pw-fortschritt"><span style="width: {(100 * punkte) / k.checkliste.length}%"></span></div>
      {#each k.checkliste as p, i (i)}
        <label class="pw-tel-punkt" class:erledigt={p.erledigt}><input type="checkbox" bind:checked={p.erledigt} /><span>{p.text}</span></label>
      {/each}
    </section>
  {/if}

  {#if k.beschreibung}
    <section class="pw-tel-abschnitt" aria-label="Beschreibung">
      <div class="etikett">Beschreibung</div>
      <div class="pw-tel-text">{@html k.beschreibung}</div>
    </section>
  {/if}

  <section class="pw-tel-abschnitt" aria-label="Kommentare">
    <div class="etikett">Kommentare<span class="zaehler">{k.kommentare.length}</span></div>
    {#each k.kommentare as c, i (i)}
      <div class="pw-tel-kommentar">
        <Person id={c.von} />
        <div class="blase"><div class="kopfzeile"><b>{konto(c.von).name}</b><span>{wann(c.zeit)}</span></div>
          <div>{@html erwaehnungen(c.text)}</div></div>
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
