/// <reference types="svelte" />
/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

// Fassung der Oberfläche (vite.config.ts, aus version.json)
declare const __FASSUNG__: string
