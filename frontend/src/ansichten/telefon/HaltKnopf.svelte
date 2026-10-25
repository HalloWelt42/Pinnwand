<script lang="ts">
  // Drücken und Halten mit füllendem Ring: Folgenreiches (erledigen) geschieht erst, wenn der Ring voll ist. Loslassen
  // vorher bricht ab; ein kurzes Tippen löst nichts aus und meldet nur, dass gehalten werden muss. Geht mit Finger, Maus
  // und Tastatur (Leertaste oder Enter halten).
  let { beschriftung, symbol = "fa-check", dauerMs = 900, aktion, fortschritt = $bindable(0), hinweis = $bindable(false) }: {
    /** wofür gehalten wird, für Vorlesen und Hinweis */
    beschriftung: string;
    symbol?: string;
    /** so lange halten, bis es gilt */
    dauerMs?: number;
    aktion: () => void;
    fortschritt?: number;
    /** kurz getippt statt gehalten */
    hinweis?: boolean;
  } = $props();

  const UMFANG = 2 * Math.PI * 21;
  const TIPPEN_MS = 350;
  let start = 0;
  let rahmen = 0;
  let hinweisUhr: ReturnType<typeof setTimeout> | undefined;

  $effect(() => () => { cancelAnimationFrame(rahmen); clearTimeout(hinweisUhr); });

  function schritt(): void {
    fortschritt = Math.min(1, (performance.now() - start) / dauerMs);
    if (fortschritt < 1) { rahmen = requestAnimationFrame(schritt); return; }
    rahmen = 0;
    aktion();
  }

  function beginnen(): void {
    if (rahmen || fortschritt >= 1) return;
    clearTimeout(hinweisUhr);
    hinweis = false;
    fortschritt = 0;
    start = performance.now();
    rahmen = requestAnimationFrame(schritt);
  }

  function loslassen(): void {
    if (!rahmen) return;
    cancelAnimationFrame(rahmen);
    rahmen = 0;
    if (performance.now() - start < TIPPEN_MS) {
      hinweis = true;
      hinweisUhr = setTimeout(() => (hinweis = false), 2500);
    }
    fortschritt = 0;
  }

  const taste = (e: KeyboardEvent): boolean => e.key === " " || e.key === "Enter";
</script>

<button type="button" class="pw-tel-halten" class:haelt={fortschritt > 0 && fortschritt < 1} class:voll={fortschritt >= 1}
        aria-label="{beschriftung}: gedrückt halten" title="{beschriftung}: gedrückt halten, bis der Ring voll ist"
        onpointerdown={(e) => { e.currentTarget.setPointerCapture(e.pointerId); beginnen(); }}
        onpointerup={loslassen} onpointercancel={loslassen}
        onkeydown={(e) => { if (taste(e)) { e.preventDefault(); if (!e.repeat) beginnen(); } }}
        onkeyup={(e) => { if (taste(e)) loslassen(); }}
        oncontextmenu={(e) => e.preventDefault()}>
  <svg viewBox="0 0 48 48" aria-hidden="true">
    <circle class="spur" cx="24" cy="24" r="21" />
    <circle class="fuellung" cx="24" cy="24" r="21" stroke-dasharray={UMFANG} stroke-dashoffset={UMFANG * (1 - fortschritt)} />
  </svg>
  <i class="fa-solid {symbol}"></i>
</button>
