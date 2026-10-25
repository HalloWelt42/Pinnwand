<script lang="ts">
  // Boards am Telefon: deine Boards nach deinen Ordnern (Ordner ordnen nur, sie tragen keine Rechte), Boards ohne Ordner
  // zuletzt; je Board die offenen Karten und wie viele davon deine sind. Ein Tippen öffnet das Board spaltenweise.
  import { boardGruppen } from "../../daten/abfragen";
  import { ICH } from "../../daten/ich";
  import { kartenDerSpalte } from "../../daten/stand.svelte";
  import type { Board } from "../../modell";
  import { boardPfad } from "../../weg.svelte";
  import TelefonSchale from "./TelefonSchale.svelte";
  import { telPfad } from "./weg";

  function zahlen(b: Board): { offen: number; deine: number } {
    const auf = b.spalten.filter((s) => !s.erledigt).flatMap((s) => kartenDerSpalte(s.id));
    return { offen: auf.length, deine: auf.filter((k) => k.zustaendig.includes(ICH)).length };
  }
  const gruppen = $derived(boardGruppen().filter((g) => g.boards.length));
  const anzahl = $derived(gruppen.reduce((n, g) => n + g.boards.length, 0));
  const ordnerZahl = $derived(gruppen.filter((g) => g.ordner).length);
  const unter = $derived(`${anzahl} ${anzahl === 1 ? "Board" : "Boards"}` + (ordnerZahl ? ` in ${ordnerZahl} ${ordnerZahl === 1 ? "Ordner" : "Ordnern"}` : ""));
</script>

<TelefonSchale titel="Boards" {unter} reiter="boards">
  {#each gruppen as g (g.ordner?.id ?? "")}
    <section class="pw-tel-abschnitt" aria-label={g.ordner ? `Ordner ${g.ordner.name}` : "Ohne Ordner"}>
      <div class="etikett"><i class="fa-solid {g.ordner ? 'fa-folder' : 'fa-folder-minus'}"></i> {g.ordner?.name ?? "Ohne Ordner"}</div>
      {#each g.boards as b (b.id)}
        {@const z = zahlen(b)}
        <a class="pw-tel-boardzeile" href={telPfad(boardPfad(b.kuerzel))} data-farbe={b.farbe}>
          <span class="kuerzel">{b.kuerzel}</span>
          <span class="text"><b>{b.name}</b>
            <span class="angaben"><span class="zahl">{z.offen}</span> offen · <span class="zahl">{z.deine}</span> deine · <span class="zahl">{b.spalten.length}</span> Spalten</span></span>
          <i class="fa-solid fa-chevron-right"></i>
        </a>
      {/each}
    </section>
  {:else}
    <div class="leer"><i class="fa-solid fa-table-columns"></i><h2>Noch kein Board</h2>
      <p>Boards legst du am Rechner an; wer dich einlädt, dessen Board erscheint hier sofort.</p></div>
  {/each}
</TelefonSchale>
