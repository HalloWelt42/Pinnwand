<script lang="ts">
  // Inhalt des Kartendetails: jedes Feld an Ort und Stelle bearbeitbar (kein Lese- oder Bearbeitungsmodus), Abschnitte
  // der Module nur, wenn das Modul im Board an ist. Jede Änderung läuft über einen Anwendungsfall mit Rückgängig; der
  // Status über denselben Weg wie das Ziehen (Gruppe zieht mit, Abschluss, Timer). Felder, die beim Verlassen speichern,
  // verwerfen mit Escape (M-125). Im Kopf: Arbeit oder Idee, Duplizieren, Verweis kopieren, Vollbild, Schließen.
  import { Hilfepunkt } from "appkern-oberflaeche";
  import { darf, kartenNummer, umzugsziele, zeitDerGruppe, zeitDerKarte } from "../daten/abfragen";
  import { artSetzen, bearbeiten, duplizieren, verschieben, type Kartenaenderung } from "../daten/anwendung/karten.svelte";
  import { melden } from "../daten/anwendung/meldung.svelte";
  import { kiDa, labelsHolen, Vorschlagslauf, zusammenfassungHolen } from "../daten/anwendung/ki.svelte";
  import { inPapierkorb, karteEndgueltig } from "../daten/anwendung/papierkorb.svelte";
  import Endgueltig from "../teile/Endgueltig.svelte";
  import { transkripteDa } from "../daten/anwendung/transkripte.svelte";
  import { checklisteText, karteText, liest, vorlesen, vorlesenDa } from "../daten/anwendung/vorlesen.svelte";
  import { uhr } from "../daten/uhr.svelte";
  import { alterTage, datumJahr, gesamtnummer } from "../daten/format";
  import { konto, mitKonto, stand } from "../daten/stand.svelte";
  import { PRIORITAETEN } from "../anzeige";
  import type { Board, Karte, Kennung, Prioritaet } from "../modell";
  import { alterung } from "../regeln/board";
  import { tageZwischen } from "../regeln/tage";
  import Person from "../board/Person.svelte";
  import DatumFeld from "../teile/DatumFeld.svelte";
  import Farbwahl from "../teile/Farbwahl.svelte";
  import { markdownText, type MarkdownOptionen } from "../teile/markdown";
  import Personenwahl from "../teile/Personenwahl.svelte";
  import { verlassen, verwerfbar } from "../teile/verwerfen";
  import { kopieren } from "../teile/zwischenablage";
  import Kennungsknopf from "../teile/Kennungsknopf.svelte";
  import { boardPfad, gehe } from "../weg.svelte";
  import Aktivitaet from "./Aktivitaet.svelte";
  import Anhaenge from "./Anhaenge.svelte";
  import Commits from "./Commits.svelte";
  import { commitsDer, commitsImBoard, vorschlaegeDer } from "../daten/anwendung/commits.svelte";
  import Checkliste from "./Checkliste.svelte";
  import Textfeld from "./Textfeld.svelte";
  import Transkripte from "./Transkripte.svelte";
  import Umziehen from "./Umziehen.svelte";
  import Verknuepfte from "./Verknuepfte.svelte";
  import Vorschlag from "./Vorschlag.svelte";
  import Zeiterfassung from "./Zeiterfassung.svelte";
  import { enter } from "../teile/taste";

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
    if (enter(e)) verlassen(e.currentTarget);
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

  // Endgültig löschen ohne Papierkorb (Rechte "Karten löschen" und "Papierkorb leeren"), bestätigt mit dem Schlüssel
  let endgueltig = $state(false);
  // das Detail schließt vorher (wie beim Papierkorb), sonst meldet der Weg die verschwundene Karte statt des Löschens
  function endgueltigLoeschen(bestaetigung: string): Promise<boolean> {
    const id = k.id;
    schliessen();
    return karteEndgueltig(id, bestaetigung);
  }

  // ═══ Konflikt (M-55): der Server hat eine Änderung abgelehnt, weil jemand anders dasselbe Feld inzwischen geändert hat ══

  // (das Detail baut sich je Karte neu auf: ein Konflikt gilt nur für die Karte, an der er entstand)
  let konflikt = $state<{ aenderung: Kartenaenderung; text: string } | null>(null);
  /** offen: die Wahl, in welches Board die Karte zieht */
  let umzug = $state(false);

  // ═══ Vorschläge der KI (Modul KI an der Karte): nur Vorschau, übernommen über bearbeiten mit Rückgängig ═════════════

  const ki = $derived(kiDa(board));
  const zusammenfassung = new Vorschlagslauf<{ text: string }>();
  const labelvorschlag = new Vorschlagslauf<{ labels: Kennung[] }>();
  /** die vorgeschlagenen Labels, die gesetzt werden sollen (anfangs alle) */
  let labelsGewaehlt = $state<Kennung[]>([]);
  const freieLabels = $derived(board.labels.filter((l) => !k.labels.includes(l.id)));
  // schließt das Detail, wartet niemand mehr auf einen Vorschlag
  $effect(() => () => {
    zusammenfassung.schliessen();
    labelvorschlag.schliessen();
  });

  function zusammenfassen(): void {
    void zusammenfassung.holen(zusammenfassungHolen(k.id));
  }

  async function zusammenfassungUebernehmen(text: string): Promise<void> {
    const notizen = [k.notizen?.trim(), `**Zusammenfassung:** ${text}`].filter(Boolean).join("\n\n");
    if (await setzen({ notizen }, "Zusammenfassung in die Notizen übernommen")) zusammenfassung.schliessen();
  }

  async function labelsVorschlagen(): Promise<void> {
    if (await labelvorschlag.holen(labelsHolen(k.id))) labelsGewaehlt = [...(labelvorschlag.wert?.labels ?? [])];
  }

  function labelWaehlen(id: Kennung): void {
    labelsGewaehlt = labelsGewaehlt.includes(id) ? labelsGewaehlt.filter((x) => x !== id) : [...labelsGewaehlt, id];
  }

  async function labelsUebernehmen(): Promise<void> {
    const neu = labelsGewaehlt.filter((l) => !k.labels.includes(l));
    const namen = neu.map((l) => board.labels.find((x) => x.id === l)?.name).join(", ");
    if (await setzen({ labels: [...k.labels, ...neu] }, `${neu.length === 1 ? "Label" : "Labels"} ${namen} gesetzt`)) labelvorschlag.schliessen();
  }

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
  <Kennungsknopf wert={k.schluessel} klasse="pw-detail-schluessel" />
  <span class="zustand" data-farbe={spalte.farbe}><span class="pw-farbpunkt"></span>{spalte.name}</span>
  <span class="pw-umschalter" title={board.module.zeiterfassung ? "Arbeit hat Zeiterfassung, eine Idee nicht; Umschalten hält laufende Timer an und bucht"
                                                                : "Arbeit oder Idee; nur Arbeit lässt sich mit anderen Karten verknüpfen"}>
    <button class:an={k.art === "arbeit"} disabled={!schreiben} onclick={() => artSetzen(k.id, "arbeit")}><i class="fa-solid fa-briefcase"></i>Arbeit</button>
    <button class="idee" class:an={k.art === "idee"} disabled={!schreiben} onclick={() => artSetzen(k.id, "idee")}><i class="fa-solid fa-lightbulb"></i>Idee</button>
  </span>
  <span class="rechts">
    {#if ki}
      <button class="knopf ohne symbol klein" title="Zusammenfassen: Vorschlag aus Beschreibung, Notizen, Checkliste und Kommentaren"
              aria-pressed={zusammenfassung.offen} onclick={() => (zusammenfassung.offen ? zusammenfassung.schliessen() : zusammenfassen())}><i class="fa-solid fa-wand-magic-sparkles"></i></button>
    {/if}
    {#if vorlesenDa(board)}
      <button class="knopf ohne symbol klein" title={liest(`karte-${k.id}`) ? "Vorlesen anhalten" : "Karte vorlesen: Titel, Beschreibung, offene Punkte"}
              aria-pressed={liest(`karte-${k.id}`)} onclick={() => vorlesen(`karte-${k.id}`, karteText(k), board.id)}>
        <i class="fa-solid {liest(`karte-${k.id}`) ? 'fa-stop' : 'fa-volume-high'}"></i></button>
    {/if}
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
  {#if zusammenfassung.offen}
    <Vorschlag titel="Vorschlag: Zusammenfassung aus Beschreibung, Notizen und Kommentaren" lauf={zusammenfassung} nochmal={zusammenfassen}>
      {#snippet children(v)}<div class="pw-vorschlag-text">{v.text}</div>{/snippet}
      {#snippet knoepfe(v)}
        {#if schreiben}<button class="knopf klein" onclick={() => zusammenfassungUebernehmen(v.text)}>In die Notizen übernehmen</button>{/if}
      {/snippet}
    </Vorschlag>
  {/if}
  {#if konflikt}
    <div class="hinweis warnung"><i class="fa-solid fa-code-merge"></i>
      <div><b>{k.schluessel} wurde inzwischen geändert.</b> Deine Änderung ({konflikt.text}) ist nicht gespeichert, damit
        nichts still überschrieben wird; oben steht der jetzige Stand.</div>
      <span class="rechts"><button class="knopf klein" onclick={jetzigeBehalten}>Jetzige behalten</button>
        <button class="knopf haupt klein" disabled={!schreiben} onclick={meineUebernehmen}>Meine übernehmen</button></span>
    </div>
  {/if}
  <Kennungsknopf wert={gesamtnummer(k.nummer)} klasse="pw-gesamtnummer" />
  <input class="pw-detail-titel" value={k.titel} disabled={!schreiben} aria-label="Titel" use:verwerfbar onchange={titelAendern} onkeydown={enterVerlaesst} />

  <Textfeld name="Beschreibung" text={k.beschreibung} leer="Keine Beschreibung." {schreiben} vorlesen={vorlesenDa(board) ? () => vorlesen(`beschreibung-${k.id}`, markdownText(k.beschreibung ?? ""), board.id) : undefined}
            liest={liest(`beschreibung-${k.id}`)} {optionen}
            speichern={(t) => setzen({ beschreibung: t || undefined }, "Beschreibung gespeichert")} />
  <Textfeld name="Notizen" text={k.notizen} leer="Keine Notizen." {schreiben} nurVollbild {optionen}
            vorlesen={vorlesenDa(board) ? () => vorlesen(`notizen-${k.id}`, markdownText(k.notizen ?? ""), board.id) : undefined}
            liest={liest(`notizen-${k.id}`)}
            speichern={(t) => setzen({ notizen: t || undefined }, "Notizen gespeichert")} />

  <section class="pw-abschnitt">
    <div class="etikett">Angaben<Hilfepunkt thema="kartendetail" abschnitt="angaben" /></div>
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
      <span class="wert pw-labelwahl">
        {#each board.labels as lab (lab.id)}
          <button class="pw-label" class:aus={!k.labels.includes(lab.id)} data-farbe={lab.farbe} disabled={!schreiben}
                  title={k.labels.includes(lab.id) ? "Label entfernen" : "Label setzen"} aria-pressed={k.labels.includes(lab.id)}
                  onclick={() => setzen({ labels: k.labels.includes(lab.id) ? k.labels.filter((x) => x !== lab.id) : [...k.labels, lab.id] },
                                        k.labels.includes(lab.id) ? `Label ${lab.name} entfernt` : `Label ${lab.name} gesetzt`)}>{lab.name}</button>
        {/each}
        {#if ki && schreiben && freieLabels.length}
          <button class="knopf ohne symbol klein" title="Labels vorschlagen (über die Leitstelle)" aria-pressed={labelvorschlag.offen}
                  onclick={() => (labelvorschlag.offen ? labelvorschlag.schliessen() : labelsVorschlagen())}><i class="fa-solid fa-wand-magic-sparkles"></i></button>
        {/if}
      </span>
      {#if labelvorschlag.offen}
        <div class="pw-felder-ganz">
          <Vorschlag titel="Vorschlag: Labels aus dem Inhalt der Karte" lauf={labelvorschlag} nochmal={labelsVorschlagen}>
            {#snippet children(v)}
              {#if v.labels.length}
                <div class="pw-labelwahl">
                  {#each v.labels as id (id)}
                    {@const lab = board.labels.find((l) => l.id === id)}
                    {#if lab}
                      <button class="pw-label" class:aus={!labelsGewaehlt.includes(id)} data-farbe={lab.farbe} aria-pressed={labelsGewaehlt.includes(id)}
                              title={labelsGewaehlt.includes(id) ? "Nicht setzen" : "Doch setzen"} onclick={() => labelWaehlen(id)}>{lab.name}</button>
                    {/if}
                  {/each}
                </div>
              {:else}
                <div class="pw-vorschlag-text">Kein weiteres Label passt klar zu dieser Karte.</div>
              {/if}
            {/snippet}
            {#snippet knoepfe(v)}
              {#if v.labels.length}<button class="knopf klein" disabled={!labelsGewaehlt.length} onclick={labelsUebernehmen}>Setzen</button>{/if}
            {/snippet}
          </Vorschlag>
        </div>
      {/if}
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
      <span class="pw-angabe flaeche"><i class="fa-solid fa-seedling"></i>Erstellt {datumJahr(k.erstelltAm, true)}{erstellt ? ` von ${konto(erstellt).kuerzel}` : ""}</span>
    </div>
  </section>

  {#if board.module.zeiterfassung && k.art === "arbeit"}
    <Zeiterfassung karte={k} {board} gruppenSek={teilen ? zeitDerGruppe(k) - zeitDerKarte(k.id) : 0} />
  {/if}

  {#if k.art === "arbeit"}
    <Verknuepfte karte={k} {board} {schreiben} />
  {/if}

  <Checkliste karte={k} {schreiben} {ki} vorlesen={vorlesenDa(board) ? () => vorlesen(`checkliste-${k.id}`, checklisteText(k), board.id) : undefined}
              liest={liest(`checkliste-${k.id}`)} />

  <Anhaenge karte={k} {schreiben} />

  {#if commitsDer(k.id).length || vorschlaegeDer(k.id).length || (schreiben && commitsImBoard(board))}
    <Commits karte={k} {schreiben} />
  {/if}

  {#if transkripteDa(board)}
    <Transkripte karte={k} {schreiben} {ki} />
  {/if}

  <Aktivitaet karte={k} {board} {optionen} />
</div>

{#if endgueltig}
  <Endgueltig frage="{k.schluessel} endgültig löschen?" wort={k.schluessel} knopf="Endgültig löschen" bestaetigen={endgueltigLoeschen}
              abbrechen={() => (endgueltig = false)}>
    Die Karte geht ohne Papierkorb, mit Checkliste, Kommentaren, Anhängen und Verlauf; ein laufender Timer bucht vorher.
    Gebuchte Zeiten bleiben unter ihrem Namen stehen; deine löschst du danach unter Zeiten. Das lässt sich nicht rückgängig machen.
  </Endgueltig>
{/if}
<div class="pw-detail-fuss">
  {#if darf(board, "karten.loeschen")}
    <button class="knopf ohne gefahr klein" onclick={wegwerfen}><i class="fa-solid fa-trash-can"></i>In den Papierkorb</button>
    {#if darf(board, "papierkorb.leeren")}
      <button class="knopf ohne gefahr klein" disabled={endgueltig} onclick={() => (endgueltig = true)}
              title="Ohne Papierkorb und ohne Rückweg; zur Sicherheit tippst du den Schlüssel ein"><i class="fa-solid fa-ban"></i>Endgültig löschen</button>
    {/if}
  {/if}
  <span class="schwach pw-detail-hinweis">Jedes Feld speichert für sich; jede Änderung lässt sich in der Meldung rückgängig machen.</span>
</div>
