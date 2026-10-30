<script lang="ts">
  // Eine Person als Kürzel im Kreis, in ihrer Farbe; der volle Name im Hinweis, bei einem App-Zugang (HELF-43) mit dem
  // Hinweis, wem er gehört.
  import { konto } from "../daten/stand.svelte";

  let { id, gross = false }: { id: string; gross?: boolean } = $props();
  const k = $derived(konto(id));
  const titel = $derived(k.app ? `${k.name}: App-Zugang von ${k.inhaber ? konto(k.inhaber).name : "?"}` : k.name);
</script>

<span class="pw-person" class:gross data-farbe={k.farbe} class:app={!!k.app} title={titel}>{k.kuerzel}</span>
