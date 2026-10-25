<script lang="ts">
  // Eine Person als Kürzel im Kreis, in ihrer Farbe; der volle Name im Hinweis.
  import { konto } from "../daten/stand.svelte";

  let { id, gross = false }: { id: string; gross?: boolean } = $props();
  const k = $derived(konto(id));
</script>

<span class="pw-person" class:gross data-farbe={k.farbe} title={k.name}>{k.kuerzel}</span>
