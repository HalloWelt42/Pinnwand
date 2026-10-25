import { svelte } from "@sveltejs/vite-plugin-svelte";
import { defineConfig } from "vite";

// Entwürfe der neuen Pinnwand: eigene kleine Oberfläche mit Beispieldaten, ohne Backend.
export default defineConfig({
  plugins: [svelte()],
  server: { port: 5398, strictPort: true },
});
