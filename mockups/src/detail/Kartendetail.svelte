<script lang="ts">
  // Kartendetail als Leiste rechts über dem Board: jedes Feld an Ort und Stelle bearbeitbar (kein Lese- oder
  // Bearbeitungsmodus), Abschnitte der Module nur, wenn das Modul im Board an ist. Der Status ändert sich über denselben
  // Anwendungsfall wie das Ziehen (Gruppe zieht mit, Abschlussdatum, Timer), es gibt keinen Nebenweg.
  import { ICH } from "../beispiel/daten";
  import { alterTage, datum, tageZwischen, wann } from "../beispiel/format";
  import { gruppenmitglieder, karte as holeKarte, konto, stand } from "../beispiel/stand.svelte";
  import type { Board, Farbe } from "../modell";
  import Person from "../board/Person.svelte";
  import Textfeld from "./Textfeld.svelte";
  import Zeiterfassung from "./Zeiterfassung.svelte";

  let { kartenId, board, voll = false, bearbeiten, konflikt = false, schliessen }: {
    kartenId: string; board: Board; voll?: boolean; bearbeiten?: "beschreibung"; konflikt?: boolean; schliessen: () => void;
  } = $props();

  const k = $derived(holeKarte(kartenId)!);
  const spalte = $derived(board.spalten.find((s) => s.id === k.spalte)!);
  const gruppe = $derived(gruppenmitglieder(k));
  const gruppenSek = $derived(gruppe.reduce((s, x) => s + x.erfasstSek, 0));
  const zeitTeilen = $derived(stand.gruppen.find((g) => g.id === k.gruppe)?.zeitTeilen ?? false);
  const COVER: Farbe[] = ["koralle", "rose", "violett", "flieder", "himmel", "petrol", "tuerkis", "minze", "honig", "sand", "stahl"];
  const PRIO = [["keine", "Keine"], ["niedrig", "Niedrig"], ["mittel", "Mittel"], ["hoch", "Hoch"], ["dringend", "Dringend"]] as const;
  const SYMBOL = { pdf: "fa-file-pdf", bild: "fa-file-image", tabelle: "fa-file-excel", text: "fa-file-lines", ton: "fa-file-audio" };
  let reiter = $state<"kommentare" | "verlauf">("kommentare");

  function erwaehnungen(text: string): string {
    return text.replace(/@(\w+)/g, '<span class="erwaehnt">@$1</span>');
  }
</script>

<aside class="pw-detail" class:voll aria-label="Karte {k.schluessel}">
  <div class="pw-detail-kopf">
    <span class="pw-schluessel" style="font-size: var(--klein)">{k.schluessel}</span>
    <span class="zustand" data-farbe={spalte.farbe}><span class="pw-farbpunkt"></span>{spalte.name}</span>
    <span class="pw-umschalter" title="Arbeit hat Zeiterfassung, eine Idee nicht; Umschalten hält einen laufenden Timer an und bucht">
      <button class:an={k.art === "arbeit"} onclick={() => (k.art = "arbeit")}><i class="fa-solid fa-briefcase"></i>Arbeit</button>
      <button class="idee" class:an={k.art === "idee"} onclick={() => (k.art = "idee")}><i class="fa-solid fa-lightbulb"></i>Idee</button>
    </span>
    <span class="rechts">
      {#if board.module.vorlesen}<button class="knopf ohne symbol klein" title="Karte vorlesen"><i class="fa-solid fa-volume-high"></i></button>{/if}
      <button class="knopf ohne symbol klein" title="Verweis kopieren ({k.schluessel})"><i class="fa-solid fa-link"></i></button>
      <button class="knopf ohne symbol klein" title={voll ? "Als Leiste" : "Vollbild"}><i class="fa-solid {voll ? 'fa-compress' : 'fa-expand'}"></i></button>
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
    <div class="pw-detail-titel">{k.titel}</div>

    <Textfeld name="Beschreibung" html={k.beschreibung} vorlesen={board.module.vorlesen} bearbeiten={bearbeiten === "beschreibung"}
              markdown={"Kunde möchte **120 Gehäuse** in RAL 7035, Lieferung bis KW 50.\n\n- Blechstärke 1,5 mm\n- Montageplatte verzinkt\n- Türanschlag rechts\n\nPreise der Lieferanten liegen im Anhang."} />
    <Textfeld name="Notizen" html={k.notizen} nurVollbild />

    <section class="pw-abschnitt">
      <div class="etikett">Angaben</div>
      <div class="pw-felder">
        <span class="name"><i class="fa-solid fa-table-columns"></i>Status</span>
        <span class="wert"><select class="eingabe">{#each board.spalten as s (s.id)}<option selected={s.id === k.spalte}>{s.name}</option>{/each}</select></span>
        <span class="name"><i class="fa-solid fa-flag"></i>Priorität</span>
        <span class="wert"><select class="eingabe">{#each PRIO as [w, n] (w)}<option selected={w === k.prioritaet}>{n}</option>{/each}</select></span>
        <span class="name"><i class="fa-solid fa-play"></i>Start</span>
        <span class="wert"><input class="eingabe" value={k.start ? datum(k.start, true) + "2026" : ""} placeholder="Tag wählen" /></span>
        <span class="name"><i class="fa-regular fa-calendar"></i>Fällig</span>
        <span class="wert"><input class="eingabe" value={k.faellig ? datum(k.faellig, true) + "2026" : ""} placeholder="Tag wählen" /></span>
        <span class="name"><i class="fa-solid fa-user"></i>Zuständig</span>
        <span class="wert">
          {#each k.zustaendig as p (p)}<span class="chip"><Person id={p} />{konto(p).name}</span>{/each}
          <button class="knopf ohne symbol klein" title="Mitglied des Boards zuweisen"><i class="fa-solid fa-plus"></i></button>
        </span>
        <span class="name"><i class="fa-solid fa-tag"></i>Labels</span>
        <span class="wert">
          {#each k.labels as l (l)}{@const lab = board.labels.find((x) => x.id === l)}{#if lab}<span class="pw-label" data-farbe={lab.farbe}>{lab.name}</span>{/if}{/each}
          <button class="knopf ohne symbol klein" title="Label wählen oder anlegen"><i class="fa-solid fa-plus"></i></button>
        </span>
        <span class="name"><i class="fa-solid fa-ban"></i>Blockiert</span>
        <span class="wert"><input class="eingabe" value={k.blockiert ?? ""} placeholder="Grund, wenn die Karte wartet" /></span>
        <span class="name"><i class="fa-solid fa-palette"></i>Cover</span>
        <span class="wert pw-cover-wahl">
          <button class="kein" class:gewaehlt={!k.cover} title="Kein Cover" aria-label="Kein Cover"></button>
          {#each COVER as f (f)}<button data-farbe={f} class:gewaehlt={k.cover === f} title={f} aria-label="Cover {f}"></button>{/each}
        </span>
        {#each board.felder as f (f.id)}
          <span class="name"><i class="fa-solid {f.art === 'zahl' ? 'fa-hashtag' : f.art === 'auswahl' ? 'fa-list' : f.art === 'datum' ? 'fa-calendar-day' : 'fa-font'}"></i>{f.name}</span>
          <span class="wert">
            {#if f.art === "auswahl"}
              <select class="eingabe"><option></option>{#each f.optionen ?? [] as o (o)}<option selected={k.felder[f.id] === o}>{o}</option>{/each}</select>
            {:else}
              <input class="eingabe" value={k.felder[f.id] ?? ""} />
            {/if}
          </span>
        {/each}
      </div>
      <div class="pw-alterung">
        <span class="pw-angabe flaeche" class:warnung={alterTage(k.bewegtAm) >= 4}><i class="fa-solid fa-hourglass-half"></i>Im Status {alterTage(k.bewegtAm)} Tage</span>
        <span class="pw-angabe flaeche"><i class="fa-solid fa-route"></i>Durchlaufzeit {tageZwischen(k.erstelltAm, "2026-10-27")} Tage</span>
        <span class="pw-angabe flaeche"><i class="fa-solid fa-seedling"></i>Erstellt {datum(k.erstelltAm, true)} von {konto("k-max").kuerzel}</span>
      </div>
    </section>

    {#if board.module.zeiterfassung && k.art === "arbeit"}
      <Zeiterfassung karte={k} gruppenSek={zeitTeilen ? gruppenSek : 0} />
    {/if}

    {#if k.art === "arbeit"}
      <section class="pw-abschnitt">
        <div class="etikett">Verknüpfte Aufgaben
          {#if gruppe.length}<span class="rechts"><button class="knopf ohne klein" title="Gruppe zeigt die gemeinsame Zeit; gebucht wird je Karte">
            <span class="schalter" class:an={zeitTeilen}></span>Zeit teilen</button></span>{/if}
        </div>
        {#each gruppe as m (m.id)}
          <div class="pw-anhang"><i class="fa-solid fa-link" style="color: var(--akzent)"></i><span class="name"><span class="pw-schluessel">{m.schluessel}</span> {m.titel}</span>
            <button class="knopf ohne klein">Lösen</button></div>
        {/each}
        <label class="suche" style="max-width: none; height: 40px"><i class="fa-solid fa-link"></i><input placeholder="Karte suchen und verknüpfen (zieht mit, Zeit geteilt)" /></label>
      </section>
    {/if}

    <section class="pw-abschnitt">
      <div class="etikett">Checkliste {#if k.checkliste.length}<span class="zaehler">{k.checkliste.filter((p) => p.erledigt).length}/{k.checkliste.length}</span>{/if}
        {#if board.module.ki}<span class="rechts"><button class="knopf ohne klein" title="Vorschlag über die Leitstelle"><i class="fa-solid fa-wand-magic-sparkles"></i>Vorschlagen</button></span>{/if}
      </div>
      {#each k.checkliste as p, i (i)}
        <label class="pw-punkt" class:erledigt={p.erledigt}><input type="checkbox" bind:checked={p.erledigt} /><span>{p.text}</span>
          <button class="knopf ohne symbol klein weg" title="Punkt entfernen"><i class="fa-solid fa-xmark"></i></button></label>
      {/each}
      <input class="eingabe" placeholder="Punkt hinzufügen, Enter" />
    </section>

    {#if board.module.ki && k.id === "c-131"}
      <div class="pw-vorschlag">
        <div class="kopf-zeile"><i class="fa-solid fa-wand-magic-sparkles"></i>Vorschlag: Zusammenfassung aus Beschreibung, Notizen und Kommentaren</div>
        <div style="font-size: var(--klein)">120 Gehäuse RAL 7035 für Elektro Brandt, Lieferung KW 50, erste 40 Stück bis KW 48. Offen: Preis der Pulverbeschichtung (Antwort am 28.10.), dann Angebot schreiben.</div>
        <div style="display: flex; gap: var(--a2)"><button class="knopf klein">In die Notizen übernehmen</button><button class="knopf ohne klein">Verwerfen</button></div>
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
        <div class="schwach" style="font-size: var(--klein)">Dateien hierher ziehen oder hochladen; sie liegen in der Kellerwolke im Ordner dieses Boards.</div>
      {/each}
    </section>

    {#if board.module.transkripte}
      <section class="pw-abschnitt">
        <div class="etikett">Transkripte</div>
        {#each k.transkripte as t (t.stelle)}
          <div class="pw-anhang"><i class="fa-solid fa-wave-square"></i><span class="name">{t.aufnahme} <span class="schwach">bei {t.stelle}: "{t.text}"</span></span>
            <button class="knopf ohne symbol klein" title="Abspielen ab der Stelle"><i class="fa-solid fa-play"></i></button></div>
        {/each}
        <label class="suche" style="max-width: none; height: 40px"><i class="fa-solid fa-wave-square"></i><input placeholder="In Transkripten suchen und eine Stelle verknüpfen" /></label>
      </section>
    {/if}

    <section class="pw-abschnitt">
      <div class="reiter" style="margin: 0">
        <button class:aktiv={reiter === "kommentare"} onclick={() => (reiter = "kommentare")}><i class="fa-regular fa-comment"></i>Kommentare<span class="zaehler">{k.kommentare.length}</span></button>
        <button class:aktiv={reiter === "verlauf"} onclick={() => (reiter = "verlauf")}><i class="fa-solid fa-clock-rotate-left"></i>Verlauf</button>
      </div>
      {#if reiter === "kommentare"}
        {#each k.kommentare as c, i (i)}
          <div class="pw-kommentar"><Person id={c.von} />
            <div class="blase"><div class="kopf-zeile"><b>{konto(c.von).name}</b><span>{wann(c.zeit)}</span></div>
              <div>{@html erwaehnungen(c.text)}</div></div></div>
        {/each}
        <div class="pw-kommentar"><Person id={ICH} />
          <div style="flex: 1; display: flex; flex-direction: column; gap: var(--a2)">
            <textarea class="eingabe" rows="2" placeholder="Kommentar schreiben; mit @ eine Person erwähnen"></textarea>
            <div><button class="knopf klein">Senden</button></div></div></div>
      {:else}
        <div class="pw-verlauf">
          {#each k.verlauf as e, i (i)}<div style="display: flex; gap: var(--a3)"><span class="zeit">{wann(e.zeit)}</span><span><b>{konto(e.von).kuerzel}</b> {e.text}</span></div>{/each}
        </div>
      {/if}
    </section>
  </div>

  <div class="pw-detail-fuss">
    <button class="knopf ohne gefahr klein"><i class="fa-solid fa-trash-can"></i>In den Papierkorb</button>
    <span class="schwach" style="font-size: var(--marke)">Alles wird sofort gespeichert; Fehler erscheinen hier.</span>
  </div>
</aside>
