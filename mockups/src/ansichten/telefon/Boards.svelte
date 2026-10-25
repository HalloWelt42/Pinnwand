<script lang="ts">
  // Boards am Telefon: deine Boards nach deinen Ordnern (Ordner ordnen nur, sie tragen keine Rechte); je Board die
  // offenen Karten und wie viele davon deine sind. Ein Tippen öffnet das Board spaltenweise.
  import { ICH, ORDNER } from "../../beispiel/daten";
  import { board, stand } from "../../beispiel/stand.svelte";
  import { boardPfad } from "../../weg.svelte";
  import TelefonSchale from "./TelefonSchale.svelte";
  import { telPfad } from "./weg";

  function zahlen(id: string): { offen: number; deine: number } {
    const b = board(id);
    const auf = stand.karten.filter((k) => k.board === id && !b.spalten.find((s) => s.id === k.spalte)?.erledigt);
    return { offen: auf.length, deine: auf.filter((k) => k.zustaendig.includes(ICH)).length };
  }
  const anzahl = ORDNER.reduce((n, o) => n + o.boards.length, 0);
</script>

<TelefonSchale titel="Boards" unter="{anzahl} Boards in {ORDNER.length} Ordnern" reiter="boards">
  {#each ORDNER as o (o.id)}
    <section class="pw-tel-abschnitt" aria-label="Ordner {o.name}">
      <div class="etikett"><i class="fa-solid fa-folder"></i> {o.name}</div>
      {#each o.boards as id (id)}
        {@const b = board(id)}
        {@const z = zahlen(id)}
        <a class="pw-tel-boardzeile" href={telPfad(boardPfad(b.kuerzel))} data-farbe={b.farbe}>
          <span class="kuerzel">{b.kuerzel}</span>
          <span class="text"><b>{b.name}</b>
            <span class="angaben"><span class="zahl">{z.offen}</span> offen · <span class="zahl">{z.deine}</span> deine · <span class="zahl">{b.spalten.length}</span> Spalten</span></span>
          <i class="fa-solid fa-chevron-right"></i>
        </a>
      {/each}
    </section>
  {/each}
</TelefonSchale>
