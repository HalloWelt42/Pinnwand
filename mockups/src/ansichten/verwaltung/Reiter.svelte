<script lang="ts">
  // Reiter einer Einstellungsseite, jeder mit eigener Adresse (gewöhnliche Verweise, der Weg fängt sie ab). Gebaut wie
  // die Reiter des Leitstands, die nur Knöpfe kennen.
  let { reiter, aktiv, name, pfad }: {
    reiter: readonly { id: string; name: string; symbol: string }[];
    aktiv: string;
    /** wofür die Reiter stehen (Vorlesen) */
    name: string;
    /** Adresse eines Reiters */
    pfad: (id: string) => string;
  } = $props();
</script>

<nav class="pw-verwaltung-reiter" aria-label={name}>
  {#each reiter as r (r.id)}
    <a href={pfad(r.id)} class:aktiv={r.id === aktiv} aria-current={r.id === aktiv ? "page" : undefined}>
      <i class="fa-solid {r.symbol}"></i>{r.name}</a>
  {/each}
</nav>
