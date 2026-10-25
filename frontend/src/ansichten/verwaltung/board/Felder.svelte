<script lang="ts">
  // Eigene Felder des Boards: Name, Art (Text, Zahl, Datum, Auswahl, Verweis auf eine Karte), Optionen einer Auswahl,
  // "auf der Karte zeigen"; Reihenfolge per Ziehen am Griff (so stehen sie im Kartendetail und auf der Karte). Die Art
  // bleibt fest, sobald Karten Werte tragen. Darunter, was Module mitbringen, und die Grundfelder. Alles über die
  // Anwendungsfälle.
  import { untrack } from "svelte";
  import { dragHandle, dragHandleZone, type DndEvent } from "svelte-dnd-action";
  import { MODULE } from "../../../anzeige";
  import {
    feldAendern, feldAnlegen, feldLoeschen, feldOption, felderOrdnen, kartenMitWert,
  } from "../../../daten/anwendung/boards.svelte";
  import type { Board, Feld, FeldArt } from "../../../modell";
  import { GRUNDFELDER } from "../daten";

  let { board }: { board: Board; entwurf?: string } = $props();

  const ARTEN: { art: FeldArt; name: string; symbol: string; text: string }[] = [
    { art: "text", name: "Text", symbol: "fa-font", text: "Eine Zeile Text, etwa ein Kunde oder eine Auftragsnummer." },
    { art: "zahl", name: "Zahl", symbol: "fa-hashtag", text: "Eine Zahl, etwa eine Stückzahl; in Liste und Berichten summierbar." },
    { art: "datum", name: "Datum", symbol: "fa-calendar-day", text: "Ein Tag im deutschen Format, etwa ein Liefertermin." },
    { art: "auswahl", name: "Auswahl", symbol: "fa-list", text: "Eine aus festen Optionen, etwa eine Maschine; im Filter wählbar." },
    { art: "verweis", name: "Verweis", symbol: "fa-link", text: "Verweis auf eine andere Karte, als Textfeld mit Vorschlägen." },
  ];
  const ART = Object.fromEntries(ARTEN.map((a) => [a.art, a])) as Record<FeldArt, (typeof ARTEN)[number]>;

  // Ziehen ordnet erst die Anzeige, das Ablegen ruft den Anwendungsfall
  let items = $state<Feld[]>([]);
  $effect(() => { items = [...board.felder]; });
  function erwaegen(e: CustomEvent<DndEvent<Feld>>): void { items = e.detail.items; }
  function abgelegt(e: CustomEvent<DndEvent<Feld>>): void {
    items = e.detail.items;
    felderOrdnen(board.id, items.map((f) => f.id));
    items = [...board.felder];
  }

  const anzahl = (n: number) => `${n} ${n === 1 ? "Karte" : "Karten"}`;

  function umbenennen(f: Feld, e: Event): void {
    const feld = e.currentTarget as HTMLInputElement;
    if (feld.value.trim() === f.name || !feldAendern(board.id, f.id, { name: feld.value })) feld.value = f.name;
  }

  let option = $state<Record<string, string>>({});
  function optionDazu(f: Feld): void {
    if (feldOption(board.id, f.id, option[f.id] ?? "", true)) option[f.id] = "";
  }

  let loeschen = $state<string | null>(null);
  $effect(() => { board.id; untrack(() => (loeschen = null)); });

  let neuName = $state("");
  let neuArt = $state<FeldArt>("text");
  function anlegen(): void {
    if (feldAnlegen(board.id, neuName, neuArt)) neuName = "";
  }
  const vonModulen = $derived(MODULE.filter((m) => board.module[m.id] && m.felder.length));
</script>

<div class="rollfeld">
  <div class="pw-verwaltung-flaeche">
    <p class="pw-verwaltung-satz"><i class="fa-solid fa-circle-info"></i>Eigene Felder stehen im Kartendetail unter den Angaben, in dieser
      Reihenfolge; mit "auf der Karte" auch auf der Karte im Board.</p>

    <div class="pw-verwaltung-liste" use:dragHandleZone={{ items, flipDurationMs: 160, type: "feld", dropTargetStyle: {} }}
         onconsider={erwaegen} onfinalize={abgelegt}>
      {#each items as f (f.id)}
        {@const mit = kartenMitWert(board.id, f.id)}
        <article class="pw-verwaltung-eintrag" class:gefahr={loeschen === f.id} aria-label="Feld {f.name}">
          <div class="oben">
            <span class="pw-verwaltung-griff" use:dragHandle aria-label="Feld {f.name} ziehen zum Umsortieren" title="Ziehen zum Umsortieren">
              <i class="fa-solid fa-grip-vertical"></i></span>
            <i class="fa-solid {ART[f.art].symbol} pw-verwaltung-artsymbol" title={ART[f.art].name}></i>
            <input class="eingabe pw-verwaltung-name" value={f.name} aria-label="Name des Feldes" onchange={(e) => umbenennen(f, e)} />
            <span class="pw-angabe flaeche" title="Karten mit einem Wert in diesem Feld"><i class="fa-regular fa-note-sticky"></i>{anzahl(mit.length)}</span>
            <button class="knopf ohne symbol klein" title="Feld {f.name} löschen" aria-label="Feld {f.name} löschen" disabled={loeschen === f.id}
                    onclick={() => (loeschen = f.id)}><i class="fa-solid fa-trash-can"></i></button>
          </div>
          <div class="angaben">
            <span class="angabe" title={mit.length ? `Die Art bleibt fest, solange ${anzahl(mit.length)} einen Wert tragen` : ART[f.art].text}>
              <span class="etikett">Art</span>
              <select class="eingabe" value={f.art} disabled={mit.length > 0} aria-label="Art des Feldes {f.name}"
                      onchange={(e) => feldAendern(board.id, f.id, { art: (e.currentTarget as HTMLSelectElement).value as FeldArt })}>
                {#each ARTEN as a (a.art)}<option value={a.art}>{a.name}</option>{/each}
              </select>
              {#if mit.length}<i class="fa-solid fa-lock schwach"></i>{/if}</span>
            <span class="angabe" title="Auch auf der Karte im Board zeigen, nicht nur im Kartendetail">
              <span class="etikett">Auf der Karte</span>
              <button class="schalter" class:an={f.aufKarte} aria-pressed={f.aufKarte} aria-label="{f.name} auf der Karte zeigen"
                      onclick={() => feldAendern(board.id, f.id, { aufKarte: !f.aufKarte })}></button>{f.aufKarte ? "ja" : "nein"}</span>
          </div>
          {#if f.art === "auswahl"}
            <div class="angaben pw-verwaltung-optionen">
              <span class="etikett">Optionen</span>
              {#each f.optionen ?? [] as o (o)}
                <span class="chip">{o}<button class="knopf ohne symbol klein" title="Option {o} entfernen" aria-label="Option {o} entfernen"
                  onclick={() => feldOption(board.id, f.id, o, false)}><i class="fa-solid fa-xmark"></i></button></span>
              {/each}
              <input class="eingabe" bind:value={option[f.id]} placeholder="Option, Enter" aria-label="Option hinzufügen"
                     onkeydown={(e) => { if (e.key === "Enter") optionDazu(f); }} />
            </div>
          {/if}
          {#if loeschen === f.id}
            <div class="hinweis gefahr pw-verwaltung-rueckfrage" role="alert"><i class="fa-solid fa-trash-can"></i>
              <div><b>Feld {f.name} löschen?</b>
                {#if mit.length}{anzahl(mit.length)} tragen einen Wert ({mit.map((k) => k.schluessel).join(", ")}); die Werte fallen mit dem Feld weg.
                {:else}Keine Karte trägt einen Wert.{/if}</div>
              <span class="rechts"><button class="knopf klein" onclick={() => (loeschen = null)}>Abbrechen</button>
                <button class="knopf gefahr-voll klein" onclick={() => { if (feldLoeschen(board.id, f.id)) loeschen = null; }}>
                  <i class="fa-solid fa-trash-can"></i>Feld löschen</button></span>
            </div>
          {/if}
        </article>
      {:else}
        <div class="leer"><i class="fa-solid fa-rectangle-list"></i><p>Noch keine eigenen Felder. Lege unten das erste an.</p></div>
      {/each}
    </div>

    <section class="bereich">
      <h2 class="etikett">Neues Feld</h2>
      <div class="pw-verwaltung-formular">
        <input class="eingabe" bind:value={neuName} placeholder="Name des Feldes" aria-label="Name des neuen Feldes"
               onkeydown={(e) => { if (e.key === "Enter") anlegen(); }} />
        <button class="knopf haupt" disabled={!neuName.trim()} onclick={anlegen}><i class="fa-solid fa-plus"></i>Feld anlegen</button>
      </div>
      <div class="pw-verwaltung-formular">
        <span class="etikett">Art</span>
        <span class="stufen" role="radiogroup" aria-label="Art des neuen Feldes">
          {#each ARTEN as a (a.art)}
            <button role="radio" aria-checked={neuArt === a.art} class:an={neuArt === a.art} onclick={() => (neuArt = a.art)}>
              <i class="fa-solid {a.symbol}"></i> {a.name}</button>
          {/each}
        </span>
      </div>
      <p class="pw-verwaltung-satz">{ART[neuArt].text}</p>
    </section>

    <section class="bereich">
      <h2 class="etikett">Felder der Module</h2>
      <p class="pw-verwaltung-satz">Bringt ein Modul mit und nimmt es beim Abschalten wieder mit; hier nicht änderbar.</p>
      <div class="pw-verwaltung-chips">
        {#each vonModulen as m (m.id)}
          {#each m.felder as f (f)}<span class="chip pw-verwaltung-fest"><i class="fa-solid {m.symbol}"></i>{f}<span class="schwach">{m.name}</span></span>{/each}
        {:else}
          <span class="schwach klein">Kein eingeschaltetes Modul bringt Felder mit.</span>
        {/each}
      </div>
      <h2 class="etikett pw-verwaltung-abstand">Grundfelder jeder Karte</h2>
      <p class="pw-verwaltung-satz">{GRUNDFELDER.join(", ")}.</p>
    </section>
  </div>
</div>
