import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

import fassungDatei from '../version.json'

// Fassung der Oberfläche aus der einzigen Quelle (version.json); weicht die des Servers ab, lädt die Oberfläche neu
// (src/lib/fassung.svelte.ts). Als Import zählt version.json zu den Abhängigkeiten der Konfiguration: ändert sie
// sich, startet der Entwicklungsserver von selbst neu, und eingebaute und Server-Fassung bleiben gleich.
export default defineConfig({
  plugins: [svelte()],
  define: { __FASSUNG__: JSON.stringify(fassungDatei.version) },
  server: {
    port: 5198,
    strictPort: false,
  },
})
