<script lang="ts">
  // Ganze Zahl in Grenzen (Tage, Karten, Grenze einer Spalte): Textfeld in der Zahlenschrift ohne Drehknöpfe; eine
  // Eingabe außerhalb der Grenzen wird nicht übernommen und sagt, warum. Leer heißt "keine", wo das erlaubt ist.
  let { wert, setzen, min, max, leer, name, einheit = "" }: {
    wert: number | undefined;
    setzen: (n: number | undefined) => void;
    min: number;
    max: number;
    /** Text für ein leeres Feld (etwa "keine"); ohne ist leer nicht erlaubt */
    leer?: string;
    name: string;
    einheit?: string;
  } = $props();

  let fehler = $state("");

  function uebernehmen(e: Event): void {
    const feld = e.currentTarget as HTMLInputElement;
    const t = feld.value.trim();
    if (!t && leer !== undefined) { fehler = ""; setzen(undefined); return; }
    const n = Number(t);
    if (!/^\d+$/.test(t) || n < min || n > max) {
      fehler = `Ganze Zahl von ${min} bis ${max.toLocaleString("de-DE")}${leer !== undefined ? `, leer: ${leer}` : ""}`;
      feld.value = wert === undefined ? "" : String(wert);
      return;
    }
    fehler = "";
    setzen(n);
  }
</script>

<span class="pw-verwaltung-zahl">
  <input class="eingabe" inputmode="numeric" value={wert ?? ""} placeholder={leer ?? ""} aria-label={name} aria-invalid={!!fehler}
         onchange={uebernehmen} />
  {#if einheit}<span class="einheit">{einheit}</span>{/if}
  {#if fehler}<span class="fehler" role="alert">{fehler}</span>{/if}
</span>
