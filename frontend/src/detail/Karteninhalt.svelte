<script lang="ts">
  // Inhalt des Kartendetails: jedes Feld an Ort und Stelle bearbeitbar (kein Lese- oder Bearbeitungsmodus), Abschnitte
  // der Module nur, wenn das Modul im Board an ist. Jede Änderung läuft über einen Anwendungsfall mit Rückgängig; der
  // Status über denselben Weg wie das Ziehen (Gruppe zieht mit, Abschluss, Timer). Felder, die beim Verlassen speichern,
  // verwerfen mit Escape (M-125). Im Kopf: Arbeit oder Idee, Duplizieren, Verweis kopieren, Vollbild, Schließen.
  import { darf, kartenNummer, umzugsziele, zeitDerGruppe, zeitDerKarte } from "../daten/abfragen";
  import { artSetzen, bearbeiten, duplizieren, verschieben, type Kartenaenderung } from "../daten/anwendung/karten.svelte";
  import { melden } from "../daten/anwendung/meldung.svelte";
  import { inPapierkorb } from "../daten/anwendung/papierkorb.svelte";
  import { uhr } from "../daten/uhr.svelte";
  import { alterTage, datumJahr } from "../daten/format";
  import { konto, mitKonto, stand } from "../daten/stand.svelte";
  import { PRIORITAETEN } from "../anzeige";
  import type { Board, Karte, Prioritaet } from "../modell";
  import { alterung } from "../regeln/board";
  import { tageZwischen } from "../regeln/tage";
  import Person from "../board/Person.svelte";
  import DatumFeld from "../teile/DatumFeld.svelte";
  import Farbwahl from "../teile/Farbwahl.svelte";
  import type { MarkdownOptionen } from "../teile/markdown";
  import Personenwahl from "../teile/Personenwahl.svelte";
  import { verlassen, verwerfbar } from "../teile/verwerfen";
  import { kopieren } from "../teile/zwischenablage";
  import { boardPfad, gehe } from "../weg.svelte";
  import Aktivitaet from "./Aktivitaet.svelte";
  import Anhaenge from "./Anhaenge.svelte";
  import Checkliste from "./Checkliste.svelte";
  import Textfeld from "./Textfeld.svelte";
  import Umziehen from "./Umziehen.svelte";
  import Verknuepfte from "./Verknuepfte.svelte";
  import Zeiterfassung from "./Zeiterfassung.svelte";

  let { karte: k, board, vollbild = $bindable(false), schliessen }: {
    karte: Karte; board: Board; vollbild?: boolean; schliessen: () => void;
  } = $props();

  const spalte = $derived(board.spalten.find((s) => s.id === k.spalte)!);
  const teilen = $derived(stand.gruppen.find((g) => g.id === k.gruppe)?.zeitTeilen ?? false);
  const imStatus = $derived(alterTage(k.bewegtAm));
  const erstellt = $derived(k.verlauf.find((e) => e.text === "hat die Karte angelegt")?.von);
  const schreiben = $derived(darf(board, "karten.bearbeiten"));
  let zuweisen = $state("");

  /** Mitglieder des Boards als Kandidaten fürs Zuweisen */
  const mitglieder = $derived(mitKonto(board).map((m) => ({ kennung: konto(m.konto).kellerwolke, name: konto(m.konto).name, konto: m.konto })));

  /** Erwähnungen in Texten: @Anna, @anna.berger oder @AB findet das Mitglied, der volle Name steht im Hinweis */
  const optionen: MarkdownOptionen = $derived({
    erwaehnung: (wort: string) => mitKonto(board).map((m) => konto(m.konto))
      .find((p) => [p.name.split(" ")[0], p.kellerwolke, p.kuerzel].some((x) => x.toLowerCase() === wort.toLowerCase()))?.name,
  });

  /** Änderung eines Felds; lehnt der Server wegen einer fremden Änderung desselben Felds ab, fragt das Detail nach */
  function setzen(aenderung: Kartenaenderung, text: string): Promise<boolean> {
    return bearbeiten(k.id, aenderung, text, { beiKonflikt: () => (konflikt = { aenderung, text }) });
  }

  /** kurzes Feld (Titel, Blockiert, eigene Felder) beim Verlassen: nur Geändertes speichern */
  function feldText(e: Event & { currentTarget: HTMLInputElement }): string {
    return e.currentTarget.value.trim();
  }

  function enterVerlaesst(e: KeyboardEvent & { currentTarget: HTMLInputElement }): void {
    if (e.key === "Enter") verlassen(e.currentTarget);
  }

  function titelAendern(e: Event & { currentTarget: HTMLInputElement }): void {
    const t = feldText(e);
    // ein leerer Titel wird abgewiesen (die alte App speicherte ihn)
    if (!t) { e.currentTarget.value = k.titel; return; }
    if (t !== k.titel) setzen({ titel: t }, "Titel geändert");
  }

  async function kopieAnlegen(): Promise<void> {
    const kopie = await duplizieren(k.id);
    if (kopie) gehe(boardPfad(board.kuerzel, kartenNummer(kopie)));
  }

  /** die Adresse der Karte; die Meldung sagt, was kopiert wurde (über http im Heimnetz der Ersatzweg im Klick) */
  async function verweisKopieren(): Promise<void> {
    const adresse = `${location.origin}${boardPfad(board.kuerzel, kartenNummer(k))}`;
    const ok = await kopieren(adresse);
    melden(ok ? `Verweis auf ${k.schluessel} kopiert: ${adresse}` : `Kopieren ging nicht; der Verweis auf ${k.schluessel} lautet ${adresse}`);
  }

  function wegwerfen(): void {
    inPapierkorb([k.id]);
    schliessen();
  }

  // ═══ Konflikt (M-55): der Server hat eine Änderung abgelehnt, weil jemand anders dasselbe Feld inzwischen geändert hat ══

  // (das Detail baut sich je Karte neu auf: ein Konflikt gilt nur für die Karte, an der er entstand)
  let konflikt = $state<{ aenderung: Kartenaenderung; text: string } | null>(null);
  /** offen: die Wahl, in welches Board die Karte zieht */
  let umzug = $state(false);

  function jetzigeBehalten(): void {
    konflikt = null;
    melden(`Der jetzige Stand von ${k.schluessel} bleibt; deine Änderung ist verworfen`);
  }

  async function meineUebernehmen(): Promise<void> {
    const kf = konflikt;
    if (kf && await bearbeiten(k.id, kf.aenderung, kf.text, { ueberschreiben: true })) konflikt = null;
  }
</script>

<div class="pw-detail-kopf">
  <span class="pw-schluessel pw-detail-schluessel">{k.schluessel}</span>
  <span class="zustand" data-farbe={spalte.farbe}><span class="pw-farbpunkt"></span>{spalte.name}</span>
  <span class="pw-umschalter" title={board.module.zeiterfassung ? "Arbeit hat Zeiterfassung, eine Idee nicht; Umschalten hält laufende Timer an und bucht"
                                                                : "Arbeit oder Idee; nur Arbeit lässt sich mit anderen Karten verknüpfen"}>
    <button class:an={k.art === "arbeit"} disabled={!schreiben} onclick={() => artSetzen(k.id, "arbeit")}><i class="fa-solid fa-briefcase"></i>Arbeit</button>
    <button class="idee" class:an={k.art === "idee"} disabled={!schreiben} onclick={() => artSetzen(k.id, "idee")}><i class="fa-solid fa-lightbulb"></i>Idee</button>
  </span>
  <span class="rechts">
    {#if board.module.vorlesen}<button class="knopf ohne symbol klein" title="Karte vorlesen"><i class="fa-solid fa-volume-high"></i></button>{/if}
    {#if darf(board, "karten.anlegen")}
      <button class="knopf ohne symbol klein" title="Duplizieren: Kopie in derselben Spalte, ohne Zeiten, Kommentare und Anhänge" onclick={kopieAnlegen}><i class="fa-regular fa-copy"></i></button>
    {/if}
    {#if umzugsziele(k).length}
      <button class="knopf ohne symbol klein" aria-pressed={umzug} title="In ein anderes Board, etwa vom Ideenboard aufs Arbeitsboard"
              onclick={() => (umzug = !umzug)}><i class="fa-solid fa-arrow-right-arrow-left"></i></button>
    {/if}
    <button class="knopf ohne symbol klein" title="Verweis kopieren ({k.schluessel})" onclick={verweisKopieren}><i class="fa-solid fa-link"></i></button>
    <button class="knopf ohne symbol klein" title={vollbild ? "Als Leiste" : "Vollbild"} onclick={() => (vollbild = !vollbild)}><i class="fa-solid {vollbild ? 'fa-compress' : 'fa-expand'}"></i></button>
    <button class="knopf ohne symbol klein" title="Schließen (Escape)" onclick={schliessen}><i class="fa-solid fa-xmark"></i></button>
  </span>
</div>

<div class="pw-detail-inhalt">
  {#if umzug}<Umziehen karte={k} schliessen={() => (umzug = false)} />{/if}
  {#if konflikt}
    <div class="hinweis warnung"><i class="fa-solid fa-code-merge"></i>
      <div><b>{k.schluessel} wurde inzwischen geändert.</b> Deine Änderung ({konflikt.text}) ist nicht gespeichert, damit
        nichts still überschrieben wird; oben steht der jetzige Stand.</div>
      <span class="rechts"><button class="knopf klein" onclick={jetzigeBehalten}>Jetzige behalten</button>
        <button class="knopf haupt klein" disabled={!schreiben} onclick={meineUebernehmen}>Meine übernehmen</button></span>
    </div>
  {/if}
  <input class="pw-detail-titel" value={k.titel} disabled={!schreiben} aria-label="Titel" use:verwerfbar onchange={titelAendern} onkeydown={enterVerlaesst} />

  <Textfeld name="Beschreibung" text={k.beschreibung} leer="Keine Beschreibung." {schreiben} vorlesen={board.module.vorlesen} {optionen}
            speichern={(t) => setzen({ beschreibung: t || undefined }, "Beschreibung gespeichert")} />
  <Textfeld name="Notizen" text={k.notizen} leer="Keine Notizen." {schreiben} nurVollbild {optionen}
            speichern={(t) => setzen({ notizen: t || undefined }, "Notizen gespeichert")} />

  <section class="pw-abschnitt">
    <div class="etikett">Angaben</div>
    <div class="pw-felder">
      <span class="name"><i class="fa-solid fa-table-columns"></i>Status</span>
      <span class="wert"><select class="eingabe" value={k.spalte} disabled={!darf(board, "karten.verschieben")} aria-label="Status"
                                 onchange={(e) => verschieben(k.id, e.currentTarget.value)}>
        {#each board.spalten as s (s.id)}<option value={s.id}>{s.name}</option>{/each}</select></span>
      <span class="name"><i class="fa-solid fa-flag"></i>Priorität</span>
      <span class="wert"><select class="eingabe" value={k.prioritaet} disabled={!schreiben} aria-label="Priorität"
                                 onchange={(e) => setzen({ prioritaet: e.currentTarget.value as Prioritaet }, "Priorität gesetzt")}>
        {#each PRIORITAETEN as [w, n] (w)}<option value={w}>{n}</option>{/each}</select></span>
      <span class="name"><i class="fa-solid fa-play"></i>Start</span>
      <span class="wert"><DatumFeld tag={k.start ?? ""} leerErlaubt titel="Start wie 28.10.2026; leer: kein Start"
                                    ontag={(t) => setzen({ start: t || undefined }, t ? `Start ${datumJahr(t, true)}` : "Start entfernt")} /></span>
      <span class="name"><i class="fa-regular fa-calendar"></i>Fällig</span>
      <span class="wert"><DatumFeld tag={k.faellig ?? ""} leerErlaubt titel="Fällig wie 29.10.2026; leer: nicht fällig"
                                    ontag={(t) => setzen({ faellig: t || undefined }, t ? `fällig ${datumJahr(t, true)}` : "Fälligkeit entfernt")} /></span>
      <span class="name"><i class="fa-solid fa-user"></i>Zuständig</span>
      <span class="wert pw-detail-personen">
        {#each k.zustaendig as p (p)}
          <span class="chip"><Person id={p} />{konto(p).name}
            {#if schreiben}<button class="knopf ohne symbol klein" title="{konto(p).name} nicht mehr zuständig"
              onclick={() => setzen({ zustaendig: k.zustaendig.filter((x) => x !== p) }, `${konto(p).name} nicht mehr zuständig`)}><i class="fa-solid fa-xmark"></i></button>{/if}</span>
        {/each}
        {#if schreiben}
          <Personenwahl kandidaten={mitglieder} ausser={k.zustaendig} bind:text={zuweisen} platzhalter="Mitglied des Boards zuweisen"
                        waehlen={(p) => p.konto && setzen({ zustaendig: [...k.zustaendig, p.konto] }, `${p.name} zuständig`)} />
        {/if}
      </span>
      <span class="name"><i class="fa-solid fa-tag"></i>Labels</span>
      <span class="wert pw-detail-labels">
        {#each board.labels as lab (lab.id)}
          <button class="pw-label" class:aus={!k.labels.includes(lab.id)} data-farbe={lab.farbe} disabled={!schreiben}
                  title={k.labels.includes(lab.id) ? "Label entfernen" : "Label setzen"} aria-pressed={k.labels.includes(lab.id)}
                  onclick={() => setzen({ labels: k.labels.includes(lab.id) ? k.labels.filter((x) => x !== lab.id) : [...k.labels, lab.id] },
                                        k.labels.includes(lab.id) ? `Label ${lab.name} entfernt` : `Label ${lab.name} gesetzt`)}>{lab.name}</button>
        {/each}
      </span>
      <span class="name"><i class="fa-solid fa-ban"></i>Blockiert</span>
      <span class="wert"><input class="eingabe" value={k.blockiert ?? ""} placeholder="Grund, wenn die Karte wartet" disabled={!schreiben} aria-label="Blockiert"
                                use:verwerfbar onkeydown={enterVerlaesst}
                                onchange={(e) => { const t = feldText(e); if (t !== (k.blockiert ?? "")) setzen({ blockiert: t || undefined }, t ? `blockiert: ${t}` : "nicht mehr blockiert"); }} /></span>
      <span class="name"><i class="fa-solid fa-palette"></i>Cover</span>
      <span class="wert"><Farbwahl wert={k.cover} keine kompakt wofuer="Cover" waehlen={(f) => setzen({ cover: f }, f ? "Cover gesetzt" : "Cover entfernt")} /></span>
      {#each board.felder as f (f.id)}
        <span class="name"><i class="fa-solid {f.art === 'zahl' ? 'fa-hashtag' : f.art === 'auswahl' ? 'fa-list' : f.art === 'datum' ? 'fa-calendar-day' : 'fa-font'}"></i>{f.name}</span>
        <span class="wert">
          {#if f.art === "auswahl"}
            <select class="eingabe" value={k.felder[f.id] ?? ""} disabled={!schreiben} aria-label={f.name}
                    onchange={(e) => setzen({ felder: { ...k.felder, [f.id]: e.currentTarget.value } }, `${f.name} gesetzt`)}>
              <option value=""></option>{#each f.optionen ?? [] as o (o)}<option value={o}>{o}</option>{/each}</select>
          {:else if f.art === "datum"}
            <DatumFeld tag={k.felder[f.id] ?? ""} leerErlaubt ontag={(t) => setzen({ felder: { ...k.felder, [f.id]: t } }, `${f.name} gesetzt`)} />
          {:else}
            <input class="eingabe" value={k.felder[f.id] ?? ""} inputmode={f.art === "zahl" ? "numeric" : undefined} disabled={!schreiben} aria-label={f.name}
                   use:verwerfbar onkeydown={enterVerlaesst}
                   onchange={(e) => { const t = feldText(e); if (t !== (k.felder[f.id] ?? "")) setzen({ felder: { ...k.felder, [f.id]: t } }, `${f.name} gesetzt`); }} />
          {/if}
        </span>
      {/each}
    </div>
    <div class="pw-alterung">
      <span class="pw-angabe {alterung(imStatus, board.einstellungen)}" title="Sanduhr nach den Schwellen des Boards"><i class="fa-solid fa-hourglass-half"></i>Im Status {imStatus} {imStatus === 1 ? "Tag" : "Tage"}</span>
      <span class="pw-angabe flaeche"><i class="fa-solid fa-route"></i>Durchlaufzeit {tageZwischen(k.erstelltAm.slice(0, 10), k.abgeschlossen ?? uhr.heute)} Tage</span>
      <span class="pw-angabe flaeche"><i class="fa-solid fa-seedling"></i>Erstellt {datumJahr(k.erstelltAm, true)}{#if erstellt} von {konto(erstellt).kuerzel}{/if}</span>
    </div>
  </section>

  {#if board.module.zeiterfassung && k.art === "arbeit"}
    <Zeiterfassung karte={k} {board} gruppenSek={teilen ? zeitDerGruppe(k) - zeitDerKarte(k.id) : 0} />
  {/if}

  {#if k.art === "arbeit"}
    <Verknuepfte karte={k} {board} {schreiben} />
  {/if}

  <Checkliste karte={k} {schreiben} ki={board.module.ki} />

  <Anhaenge karte={k} {board} {schreiben} />

  {#if board.module.transkripte}
    <section class="pw-abschnitt">
      <div class="etikett">Transkripte</div>
      {#each k.transkripte as t (t.stelle)}
        <div class="pw-anhang"><i class="fa-solid fa-wave-square"></i><span class="name">{t.aufnahme} <span class="schwach">bei {t.stelle}: "{t.text}"</span></span>
          <button class="knopf ohne symbol klein" title="Abspielen ab der Stelle"><i class="fa-solid fa-play"></i></button></div>
      {/each}
      <label class="suche pw-detail-suche"><i class="fa-solid fa-wave-square"></i><input placeholder="In Transkripten suchen und eine Stelle verknüpfen" /></label>
    </section>
  {/if}

  <Aktivitaet karte={k} {board} {optionen} />
</div>

<div class="pw-detail-fuss">
  {#if darf(board, "karten.loeschen")}
    <button class="knopf ohne gefahr klein" onclick={wegwerfen}><i class="fa-solid fa-trash-can"></i>In den Papierkorb</button>
  {/if}
  <span class="schwach pw-detail-hinweis">Jedes Feld speichert für sich; jede Änderung lässt sich in der Meldung rückgängig machen.</span>
</div>
