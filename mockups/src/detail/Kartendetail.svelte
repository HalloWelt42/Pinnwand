<script lang="ts">
  // Kartendetail als Leiste rechts über dem Board: jedes Feld an Ort und Stelle bearbeitbar (kein Lese- oder
  // Bearbeitungsmodus), Abschnitte der Module nur, wenn das Modul im Board an ist. Jede Änderung läuft über einen
  // Anwendungsfall mit Rückgängig; der Status über denselben Weg wie das Ziehen (Gruppe zieht mit, Abschluss, Timer).
  import { darf, zeitDerGruppe, zeitDerKarte } from "../beispiel/abfragen";
  import { artSetzen, bearbeiten, gruppeLoesen, kommentieren, verschieben, zeitTeilen } from "../beispiel/anwendung/karten.svelte";
  import { inPapierkorb } from "../beispiel/anwendung/papierkorb.svelte";
  import { HEUTE, ICH } from "../beispiel/daten";
  import { alterTage, datumJahr, wann } from "../beispiel/format";
  import { gruppenmitglieder, karte as holeKarte, konto, stand } from "../beispiel/stand.svelte";
  import { PRIORITAETEN } from "../anzeige";
  import type { Board, Karte, Prioritaet } from "../modell";
  import { alterung } from "../regeln/board";
  import { tageZwischen } from "../regeln/tage";
  import Person from "../board/Person.svelte";
  import DatumFeld from "../teile/DatumFeld.svelte";
  import Farbwahl from "../teile/Farbwahl.svelte";
  import Personenwahl from "../teile/Personenwahl.svelte";
  import Textfeld from "./Textfeld.svelte";
  import Zeiterfassung from "./Zeiterfassung.svelte";

  let { kartenId, board, voll = false, bearbeiten: bearbeitenEntwurf, konflikt = false, schliessen }: {
    kartenId: string; board: Board; voll?: boolean; bearbeiten?: "beschreibung"; konflikt?: boolean; schliessen: () => void;
  } = $props();

  const k = $derived(holeKarte(kartenId)!);
  const spalte = $derived(board.spalten.find((s) => s.id === k.spalte)!);
  const gruppe = $derived(gruppenmitglieder(k));
  const teilen = $derived(stand.gruppen.find((g) => g.id === k.gruppe)?.zeitTeilen ?? false);
  const imStatus = $derived(alterTage(k.bewegtAm));
  const erstellt = $derived(k.verlauf.find((e) => e.text === "hat die Karte angelegt")?.von);
  const schreiben = $derived(darf(board, "karten.bearbeiten"));
  const SYMBOL = { pdf: "fa-file-pdf", bild: "fa-file-image", tabelle: "fa-file-excel", text: "fa-file-lines", ton: "fa-file-audio" };
  let reiter = $state<"kommentare" | "verlauf">("kommentare");
  let vollbild = $state(false);
  $effect(() => { vollbild = voll; });
  let neuerPunkt = $state("");
  let kommentar = $state("");
  let zuweisen = $state("");

  /** Mitglieder des Boards als Kandidaten fürs Zuweisen */
  const mitglieder = $derived(board.mitglieder.map((m) => ({ kennung: konto(m.konto).kellerwolke, name: konto(m.konto).name, konto: m.konto })));

  function setzen(aenderung: Partial<Karte>, text: string): void {
    bearbeiten(k.id, aenderung, text);
  }

  function punktUmschalten(i: number): void {
    const liste = k.checkliste.map((p, j) => (j === i ? { ...p, erledigt: !p.erledigt } : p));
    setzen({ checkliste: liste }, liste[i].erledigt ? `Punkt "${liste[i].text}" erledigt` : `Punkt "${liste[i].text}" wieder offen`);
  }

  function punktHinzu(): void {
    const t = neuerPunkt.trim();
    if (!t) return;
    setzen({ checkliste: [...k.checkliste, { text: t, erledigt: false }] }, `Punkt "${t}" hinzugefügt`);
    neuerPunkt = "";
  }

  function erwaehnungen(text: string): string {
    const sicher = text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    return sicher.replace(/@(\w+)/g, '<span class="erwaehnt">@$1</span>');
  }

  function wegwerfen(): void {
    inPapierkorb([k.id]);
    schliessen();
  }
</script>

<aside class="pw-detail" class:voll={vollbild} aria-label="Karte {k.schluessel}">
  <div class="pw-detail-kopf">
    <span class="pw-schluessel pw-detail-schluessel">{k.schluessel}</span>
    <span class="zustand" data-farbe={spalte.farbe}><span class="pw-farbpunkt"></span>{spalte.name}</span>
    {#if board.module.zeiterfassung}
      <span class="pw-umschalter" title="Arbeit hat Zeiterfassung, eine Idee nicht; Umschalten hält laufende Timer an und bucht">
        <button class:an={k.art === "arbeit"} onclick={() => artSetzen(k.id, "arbeit")}><i class="fa-solid fa-briefcase"></i>Arbeit</button>
        <button class="idee" class:an={k.art === "idee"} onclick={() => artSetzen(k.id, "idee")}><i class="fa-solid fa-lightbulb"></i>Idee</button>
      </span>
    {/if}
    <span class="rechts">
      {#if board.module.vorlesen}<button class="knopf ohne symbol klein" title="Karte vorlesen"><i class="fa-solid fa-volume-high"></i></button>{/if}
      <button class="knopf ohne symbol klein" title="Verweis kopieren ({k.schluessel})"><i class="fa-solid fa-link"></i></button>
      <button class="knopf ohne symbol klein" title={vollbild ? "Als Leiste" : "Vollbild"} onclick={() => (vollbild = !vollbild)}><i class="fa-solid {vollbild ? 'fa-compress' : 'fa-expand'}"></i></button>
      <button class="knopf ohne symbol klein" title="Schließen (Escape)" onclick={schliessen}><i class="fa-solid fa-xmark"></i></button>
    </span>
  </div>

  <div class="pw-detail-inhalt">
    {#if konflikt}
      <div class="hinweis warnung"><i class="fa-solid fa-code-merge"></i>
        <div><b>Anna Berger hat die Karte gerade geändert.</b> Deine Änderung an der Fälligkeit ist nicht gespeichert, damit nichts
          still überschrieben wird. Ihre Fassung: fällig Mi 28.10., deine: Do 29.10.</div>
        <span class="rechts"><button class="knopf klein">Ihre behalten</button><button class="knopf haupt klein">Meine übernehmen</button></span>
      </div>
    {/if}
    <input class="pw-detail-titel" value={k.titel} disabled={!schreiben} aria-label="Titel"
           onchange={(e) => { const t = e.currentTarget.value.trim(); if (t && t !== k.titel) setzen({ titel: t }, "Titel geändert"); }} />

    <Textfeld name="Beschreibung" html={k.beschreibung} vorlesen={board.module.vorlesen} bearbeiten={bearbeitenEntwurf === "beschreibung"}
              markdown={"Kunde möchte **120 Gehäuse** in RAL 7035, Lieferung bis KW 50.\n\n- Blechstärke 1,5 mm\n- Montageplatte verzinkt\n- Türanschlag rechts\n\nPreise der Lieferanten liegen im Anhang."} />
    <Textfeld name="Notizen" html={k.notizen} nurVollbild />

    <section class="pw-abschnitt">
      <div class="etikett">Angaben</div>
      <div class="pw-felder">
        <span class="name"><i class="fa-solid fa-table-columns"></i>Status</span>
        <span class="wert"><select class="eingabe" value={k.spalte} disabled={!darf(board, "karten.verschieben")}
                                   onchange={(e) => verschieben(k.id, e.currentTarget.value)}>
          {#each board.spalten as s (s.id)}<option value={s.id}>{s.name}</option>{/each}</select></span>
        <span class="name"><i class="fa-solid fa-flag"></i>Priorität</span>
        <span class="wert"><select class="eingabe" value={k.prioritaet} disabled={!schreiben}
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
        <span class="wert"><input class="eingabe" value={k.blockiert ?? ""} placeholder="Grund, wenn die Karte wartet" disabled={!schreiben}
                                  onchange={(e) => { const t = e.currentTarget.value.trim(); setzen({ blockiert: t || undefined }, t ? "blockiert" : "nicht mehr blockiert"); }} /></span>
        <span class="name"><i class="fa-solid fa-palette"></i>Cover</span>
        <span class="wert"><Farbwahl wert={k.cover} keine kompakt wofuer="Cover" waehlen={(f) => setzen({ cover: f }, f ? "Cover gesetzt" : "Cover entfernt")} /></span>
        {#each board.felder as f (f.id)}
          <span class="name"><i class="fa-solid {f.art === 'zahl' ? 'fa-hashtag' : f.art === 'auswahl' ? 'fa-list' : f.art === 'datum' ? 'fa-calendar-day' : 'fa-font'}"></i>{f.name}</span>
          <span class="wert">
            {#if f.art === "auswahl"}
              <select class="eingabe" value={k.felder[f.id] ?? ""} disabled={!schreiben}
                      onchange={(e) => setzen({ felder: { ...k.felder, [f.id]: e.currentTarget.value } }, `${f.name} gesetzt`)}>
                <option value=""></option>{#each f.optionen ?? [] as o (o)}<option value={o}>{o}</option>{/each}</select>
            {:else if f.art === "datum"}
              <DatumFeld tag={k.felder[f.id] ?? ""} leerErlaubt ontag={(t) => setzen({ felder: { ...k.felder, [f.id]: t } }, `${f.name} gesetzt`)} />
            {:else}
              <input class="eingabe" value={k.felder[f.id] ?? ""} inputmode={f.art === "zahl" ? "numeric" : undefined} disabled={!schreiben}
                     onchange={(e) => setzen({ felder: { ...k.felder, [f.id]: e.currentTarget.value.trim() } }, `${f.name} gesetzt`)} />
            {/if}
          </span>
        {/each}
      </div>
      <div class="pw-alterung">
        <span class="pw-angabe {alterung(imStatus, board.einstellungen)}" title="Sanduhr nach den Schwellen des Boards"><i class="fa-solid fa-hourglass-half"></i>Im Status {imStatus} {imStatus === 1 ? "Tag" : "Tage"}</span>
        <span class="pw-angabe flaeche"><i class="fa-solid fa-route"></i>Durchlaufzeit {tageZwischen(k.erstelltAm.slice(0, 10), k.abgeschlossen ?? HEUTE)} Tage</span>
        <span class="pw-angabe flaeche"><i class="fa-solid fa-seedling"></i>Erstellt {datumJahr(k.erstelltAm, true)}{#if erstellt} von {konto(erstellt).kuerzel}{/if}</span>
      </div>
    </section>

    {#if board.module.zeiterfassung && k.art === "arbeit"}
      <Zeiterfassung karte={k} {board} gruppenSek={teilen ? zeitDerGruppe(k) - zeitDerKarte(k.id) : 0} />
    {/if}

    {#if k.art === "arbeit"}
      <section class="pw-abschnitt">
        <div class="etikett">Verknüpfte Aufgaben
          {#if gruppe.length && k.gruppe}{@const g = k.gruppe}<span class="rechts"><button class="knopf ohne klein" title="Die Gruppe zeigt die gemeinsame Zeit; gebucht wird je Karte"
            onclick={() => zeitTeilen(g, !teilen)}><span class="schalter" class:an={teilen}></span>Zeit teilen</button></span>{/if}
        </div>
        {#each gruppe as m (m.id)}
          <div class="pw-anhang"><i class="fa-solid fa-link pw-akzent"></i><span class="name"><span class="pw-schluessel">{m.schluessel}</span> {m.titel}</span>
            <button class="knopf ohne klein" onclick={() => gruppeLoesen(m.id)}>Lösen</button></div>
        {/each}
        <label class="suche pw-detail-suche"><i class="fa-solid fa-link"></i><input placeholder="Karte suchen und verknüpfen (zieht mit, Zeit geteilt)" /></label>
      </section>
    {/if}

    <section class="pw-abschnitt">
      <div class="etikett">Checkliste {#if k.checkliste.length}<span class="zaehler">{k.checkliste.filter((p) => p.erledigt).length}/{k.checkliste.length}</span>{/if}
        {#if board.module.ki}<span class="rechts"><button class="knopf ohne klein" title="Vorschlag über die Leitstelle"><i class="fa-solid fa-wand-magic-sparkles"></i>Vorschlagen</button></span>{/if}
      </div>
      {#each k.checkliste as p, i (i)}
        <label class="pw-punkt" class:erledigt={p.erledigt}><input type="checkbox" checked={p.erledigt} disabled={!schreiben} onchange={() => punktUmschalten(i)} /><span>{p.text}</span>
          {#if schreiben}<button class="knopf ohne symbol klein weg" title="Punkt entfernen"
            onclick={(e) => { e.preventDefault(); setzen({ checkliste: k.checkliste.filter((_, j) => j !== i) }, `Punkt "${p.text}" entfernt`); }}><i class="fa-solid fa-xmark"></i></button>{/if}</label>
      {/each}
      {#if schreiben}
        <input class="eingabe" placeholder="Punkt hinzufügen, Enter" bind:value={neuerPunkt} onkeydown={(e) => { if (e.key === "Enter") punktHinzu(); }} />
      {/if}
    </section>

    {#if board.module.ki && k.id === "c-131"}
      <div class="pw-vorschlag">
        <div class="kopf-zeile"><i class="fa-solid fa-wand-magic-sparkles"></i>Vorschlag: Zusammenfassung aus Beschreibung, Notizen und Kommentaren</div>
        <div class="pw-vorschlag-text">120 Gehäuse RAL 7035 für Elektro Brandt, Lieferung KW 50, erste 40 Stück bis KW 48. Offen: Preis der Pulverbeschichtung (Antwort am 28.10.), dann Angebot schreiben.</div>
        <div class="pw-vorschlag-knoepfe"><button class="knopf klein">In die Notizen übernehmen</button><button class="knopf ohne klein">Verwerfen</button></div>
      </div>
    {/if}

    <section class="pw-abschnitt">
      <div class="etikett">Anhänge {#if k.anhaenge.length}<span class="zaehler">{k.anhaenge.length}</span>{/if}
        <span class="rechts"><button class="knopf ohne klein"><i class="fa-solid fa-upload"></i>Hochladen</button><button class="knopf ohne klein"><i class="fa-solid fa-cloud"></i>Aus der Kellerwolke</button></span></div>
      {#each k.anhaenge as a (a.name)}
        <div class="pw-anhang"><i class="fa-solid {SYMBOL[a.art]}"></i><span class="name">{a.name}</span>
          <span class="meta">{a.verknuepft ? "verknüpft aus deiner Kellerwolke" : `${a.groesse} · Kellerwolke, Pinnwand/${board.name}`}</span>
          <button class="knopf ohne symbol klein" title="Öffnen"><i class="fa-solid fa-arrow-up-right-from-square"></i></button></div>
      {:else}
        <div class="schwach pw-detail-leer">Dateien hierher ziehen oder hochladen; sie liegen in der Kellerwolke im Ordner dieses Boards.</div>
      {/each}
    </section>

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

    <section class="pw-abschnitt">
      <div class="reiter pw-detail-reiter">
        <button class:aktiv={reiter === "kommentare"} onclick={() => (reiter = "kommentare")}><i class="fa-regular fa-comment"></i>Kommentare<span class="zaehler">{k.kommentare.length}</span></button>
        <button class:aktiv={reiter === "verlauf"} onclick={() => (reiter = "verlauf")}><i class="fa-solid fa-clock-rotate-left"></i>Verlauf</button>
      </div>
      {#if reiter === "kommentare"}
        {#each k.kommentare as c, i (i)}
          <div class="pw-kommentar"><Person id={c.von} />
            <div class="blase"><div class="kopf-zeile"><b>{konto(c.von).name}</b><span>{wann(c.zeit)}</span></div>
              <div>{@html erwaehnungen(c.text)}</div></div></div>
        {/each}
        {#if darf(board, "kommentieren")}
          <div class="pw-kommentar"><Person id={ICH} />
            <div class="pw-kommentar-neu">
              <textarea class="eingabe" rows="2" placeholder="Kommentar schreiben; mit @ eine Person erwähnen" bind:value={kommentar}></textarea>
              <div><button class="knopf klein" disabled={!kommentar.trim()} onclick={() => { kommentieren(k.id, kommentar); kommentar = ""; }}>Senden</button></div></div></div>
        {/if}
      {:else}
        <div class="pw-verlauf">
          {#each [...k.verlauf].reverse() as e, i (i)}<div class="pw-verlauf-zeile"><span class="zeit">{wann(e.zeit)}</span><span><b>{konto(e.von).kuerzel}</b> {e.text}</span></div>{/each}
        </div>
      {/if}
    </section>
  </div>

  <div class="pw-detail-fuss">
    {#if darf(board, "karten.loeschen")}
      <button class="knopf ohne gefahr klein" onclick={wegwerfen}><i class="fa-solid fa-trash-can"></i>In den Papierkorb</button>
    {/if}
    <span class="schwach pw-detail-hinweis">Alles wird sofort gespeichert; jede Änderung lässt sich in der Meldung rückgängig machen.</span>
  </div>
</aside>
