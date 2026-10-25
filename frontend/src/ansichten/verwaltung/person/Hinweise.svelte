<script lang="ts">
  // Hinweise: oben Push aufs Telefon einrichten (Schritte wie im Entwurf, Geräte mit Mitteilungen, Testmitteilung, dieses
  // Gerät), darunter je Art (zugewiesen, fällig, erwähnt, Termin, Kommentar, verschoben) und je Weg, den diese Pinnwand
  // anbietet, ein Schalter. Gilt am Konto, auf allen Geräten; jeder Schalter über den Anwendungsfall.
  import { pushGeraete, pushGeraetEntfernen, pushProbe, type PushGeraet as Geraet } from "appkern-oberflaeche";
  import { artenDa, hinweisWegSetzen, wegAn, wegeDa } from "../../../daten/anwendung/hinweise.svelte";
  import { melden } from "../../../daten/anwendung/meldung.svelte";
  import { wann } from "../../../daten/format";
  import DiesesGeraet from "../../../teile/PushGeraet.svelte";

  const arten = $derived(artenDa());
  const wege = $derived(wegeDa());
  const mitPush = $derived(wege.some((w) => w.id === "push"));
  let geraete = $state<Geraet[] | null>(null);
  let unterwegs = $state(false);

  async function laden(): Promise<void> {
    try {
      geraete = await pushGeraete();
    } catch {
      geraete = [];
    }
  }
  $effect(() => { if (mitPush) void laden(); });

  async function probe(): Promise<void> {
    unterwegs = true;
    try {
      const v = await pushProbe();
      melden(v.zugestellt ? `Testmitteilung an ${v.zugestellt} ${v.zugestellt === 1 ? "Gerät" : "Geräte"} gesendet`
        : "Kein Gerät hat die Testmitteilung angenommen");
      await laden();
    } catch {
      melden("Die Testmitteilung ging nicht");
    }
    unterwegs = false;
  }

  async function entfernen(g: Geraet): Promise<void> {
    await pushGeraetEntfernen(g.id);
    melden(`${g.name} bekommt keine Mitteilungen mehr`);
    await laden();
  }
</script>

<div class="rollfeld">
  <div class="pw-verwaltung-flaeche">
    {#if mitPush}
      <section class="bereich">
        <h2 class="etikett">Push aufs Telefon einrichten</h2>
        <div class="kette" aria-label="Schritte">
          <span class="schritt erledigt"><i class="fa-solid fa-circle-check"></i>Pinnwand als Web-App aufs Telefon</span>
          <span class="pfeil" class:erledigt={!!geraete?.length}></span>
          <span class="schritt" class:erledigt={!!geraete?.length} class:jetzt={!geraete?.length}>
            <i class="fa-solid {geraete?.length ? 'fa-circle-check' : 'fa-bell'}"></i>Dort Mitteilungen erlauben</span>
          <span class="pfeil"></span>
          <span class="schritt" class:jetzt={!!geraete?.length} class:offen={!geraete?.length}><i class="fa-solid fa-paper-plane"></i>Testmitteilung</span>
        </div>
        <div class="pw-verwaltung-formular">
          <p class="pw-verwaltung-satz">Öffne die Pinnwand auf dem Telefon vom Home-Bildschirm, dann Hinweise, "Mitteilungen erlauben".
            Danach steht das Telefon hier, und eine Testmitteilung zeigt, dass es ankommt.</p>
          <button class="knopf" disabled={!geraete?.length || unterwegs} onclick={probe}
                  title={geraete?.length ? "An alle deine Geräte mit Mitteilungen" : "Erst, wenn ein Gerät Mitteilungen erlaubt"}>
            <i class="fa-solid fa-paper-plane"></i>Testmitteilung senden</button>
        </div>
        {#if geraete?.length}
          {#each geraete as g (g.id)}
            <div class="pw-verwaltung-geraete"><i class="fa-solid fa-mobile-screen"></i><span>{g.name}, eingerichtet {wann(g.angelegt)}{g.zuletzt ? `, zuletzt erreicht ${wann(g.zuletzt)}` : ""}</span>
              <button class="knopf ohne symbol klein" title="{g.name} bekommt dann keine Mitteilungen mehr" aria-label="{g.name} entfernen"
                      onclick={() => entfernen(g)}><i class="fa-solid fa-xmark"></i></button></div>
          {/each}
        {:else if geraete}
          <div class="pw-verwaltung-geraete"><i class="fa-solid fa-mobile-screen"></i>Noch kein Telefon eingerichtet; bis dahin kommen Hinweise in der Pinnwand.</div>
        {/if}
        <DiesesGeraet nachher={laden} />
      </section>
    {/if}

    <section class="bereich">
      <h2 class="etikett">Welche Hinweise wohin</h2>
      <div class="tabellen-raum pw-verwaltung-tabelle">
        <table class="tabelle karten pw-verwaltung-hinweise">
          <thead><tr><th>Art</th>{#each wege as w (w.id)}<th class="haken" title={w.text}><i class="fa-solid {w.symbol}"></i> {w.name}</th>{/each}</tr></thead>
          <tbody>
            {#each arten as a (a.art)}
              <tr>
                <td><span class="pw-verwaltung-art"><i class="fa-solid {a.symbol}"></i><span><b>{a.name}</b><span class="pw-verwaltung-erklaerung">{a.text}</span></span></span></td>
                {#each wege as w (w.id)}
                  {@const an = wegAn(a.art, w.id)}
                  <td class="haken" data-titel={w.name}>
                    <button class="schalter" class:an aria-pressed={an} aria-label="{a.name}: {w.name}"
                            onclick={() => hinweisWegSetzen(a.art, w.id, !an)}></button>
                    <span class="pw-verwaltung-schalterwort">{an ? "an" : "aus"}</span>
                  </td>
                {/each}
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
      <p class="pw-verwaltung-satz">Gelesen gilt für dein Konto, auf allen Geräten.{mitPush ? " Push gilt erst, wenn ein Telefon eingerichtet ist." : ""}</p>
    </section>
  </div>
</div>
