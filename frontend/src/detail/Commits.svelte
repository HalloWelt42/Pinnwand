<script lang="ts">
  // Commits an der Karte (HELF-35): je Commit der kurze Hash, die erste Zeile der Nachricht, Repo, Person und Zeit. Mit
  // Verweis öffnet der Knopf den Commit in seiner Git-Verwaltung; ein lokaler Commit (ohne Verweis) klappt hier auf und
  // zeigt die ganze Nachricht und die geänderten Dateien. Wer die Karte bearbeiten darf, sucht unter den bekannten
  // Commits (Anfang des Hashs oder Wörter der Nachricht) und verknüpft von Hand, oder löst einen (mit Rückgängig).
  import { Hilfepunkt, Suchfeld } from "appkern-oberflaeche";
  import { betreff, commitsDer, loesen, suchen, verknuepfen } from "../daten/anwendung/commits.svelte";
  import { wann } from "../daten/format";
  import type { Commit, Karte } from "../modell";
  import { verwerfen } from "../teile/verwerfen";

  let { karte, schreiben }: { karte: Karte; schreiben: boolean } = $props();

  const liste = $derived(commitsDer(karte.id));
  let offen = $state<string | null>(null);

  /** so lange nach der letzten Taste wird gesucht */
  const WARTEN_MS = 220;
  let text = $state("");
  let treffer = $state<Commit[] | null>(null);
  let sucht = $state(false);
  let fehler = $state("");
  let uhr: ReturnType<typeof setTimeout> | undefined;
  let steuerung: AbortController | null = null;
  $effect(() => () => { steuerung?.abort(); clearTimeout(uhr); });

  function eingabe(): void {
    clearTimeout(uhr);
    steuerung?.abort();
    const t = text.trim();
    if (!t) {
      treffer = null;
      fehler = "";
      sucht = false;
      return;
    }
    uhr = setTimeout(() => void holen(t), WARTEN_MS);
  }

  async function holen(t: string): Promise<void> {
    const s = new AbortController();
    steuerung = s;
    sucht = true;
    try {
      const ergebnis = await suchen(karte.id, t, s.signal);
      if (!s.signal.aborted) {
        treffer = ergebnis;
        fehler = "";
      }
    } catch (f) {
      if (!s.signal.aborted) {
        treffer = null;
        fehler = f instanceof Error ? f.message : "Die Suche ging nicht";
      }
    } finally {
      if (steuerung === s) sucht = false;
    }
  }

  async function anhaengen(c: Commit): Promise<void> {
    if (await verknuepfen(karte.id, c.id)) {
      text = "";
      treffer = null;
    }
  }
  const verknuepft = (c: Commit) => liste.some((x) => x.commit === c.id);
</script>

<section class="pw-abschnitt" aria-label="Commits">
  <div class="etikett">Commits<Hilfepunkt thema="kartendetail" abschnitt="commits" /> {#if liste.length}<span class="zaehler">{liste.length}</span>{/if}</div>
  {#each liste as c (c.id)}
    <div class="pw-commit" class:offen={offen === c.id}>
      <div class="pw-anhang">
        <i class="fa-solid fa-code-commit"></i>
        <span class="pw-commit-hash" title={c.hash}>{c.hash.slice(0, 7)}</span>
        <span class="pw-commit-text">
          <span class="name" title={c.nachricht}>{betreff(c)}</span>
          <span class="meta" title="{c.repo}, {c.quelle === 'lokal' ? 'nur lokal' : c.quelle}; {c.art === 'hand' ? 'von Hand verknüpft' : 'Schlüssel in der Nachricht'}">
            {c.reponame} · {c.autor} · {wann(c.zeit)}</span></span>
        {#if c.verweis}
          <a class="knopf ohne symbol klein" href={c.verweis} target="_blank" rel="noopener" title="In {c.quelle} öffnen"><i class="fa-solid fa-arrow-up-right-from-square"></i></a>
        {:else}
          <button class="knopf ohne symbol klein" aria-expanded={offen === c.id} title={offen === c.id ? "Zuklappen" : "Nachricht und Dateien zeigen (nur lokal)"}
                  onclick={() => (offen = offen === c.id ? null : c.id)}><i class="fa-solid {offen === c.id ? 'fa-chevron-up' : 'fa-chevron-down'}"></i></button>
        {/if}
        {#if schreiben}
          <button class="knopf ohne symbol klein" title="Lösen (Rückgängig möglich)" aria-label="Commit {c.hash.slice(0, 7)} lösen"
                  onclick={() => loesen(karte.id, c.id)}><i class="fa-solid fa-xmark"></i></button>
        {/if}
      </div>
      {#if offen === c.id}
        <div class="pw-commit-inhalt">
          <pre>{c.nachricht}</pre>
          {#if c.dateien.length}<ul>{#each c.dateien as d (d)}<li>{d}</li>{/each}</ul>{/if}
        </div>
      {/if}
    </div>
  {/each}

  {#if schreiben}
    <Suchfeld klasse="pw-detail-suche" symbol={sucht ? "fa-spinner fa-spin-pulse" : "fa-code-commit"} placeholder="Commit suchen: Hash oder Wörter der Nachricht"
              aria-label="Commit suchen" bind:wert={text} oninput={eingabe} {@attach verwerfen} />
    {#if fehler}
      <div class="hinweis warnung"><i class="fa-solid fa-triangle-exclamation"></i><div>{fehler}</div></div>
    {:else if treffer}
      <div class="pw-commit-treffer" aria-label="Treffer">
        {#each treffer as c (c.id)}
          <button class="fundstelle" disabled={verknuepft(c)} title={verknuepft(c) ? "Hängt schon an dieser Karte" : "Diesen Commit verknüpfen"}
                  onclick={() => anhaengen(c)}>
            <span class="zeit">{c.hash.slice(0, 7)}</span><span class="ausschnitt">{betreff(c)}</span><span class="meta">{c.reponame} · {wann(c.zeit)}</span></button>
        {:else}
          <div class="pw-vorschlag-text">Kein bekannter Commit passt zu "{text.trim()}".</div>
        {/each}
      </div>
    {/if}
  {/if}
</section>
