import '@fontsource/ibm-plex-sans/400.css'
import '@fontsource/ibm-plex-sans/500.css'
import '@fontsource/ibm-plex-sans/600.css'
import '@fontsource/inter/400.css'
import '@fontsource/inter/500.css'
import '@fontsource/jetbrains-mono/400.css'
import '@fontsource/jetbrains-mono/500.css'
import '@fortawesome/fontawesome-free/css/all.min.css'
import './lib/theme/tokens.css'
import './app.css'

import { mount } from 'svelte'
import App from './App.svelte'
import { initTheme } from './lib/theme/theme.svelte'
import { startUhr } from './lib/timer.svelte'

initTheme()
startUhr()

// Module automatisch entdecken: jedes module/<name>/index.ts exportiert registriere().
const moduleDateien = import.meta.glob('./lib/module/*/index.ts', { eager: true })
for (const modul of Object.values(moduleDateien)) {
  ;(modul as { registriere?: () => void }).registriere?.()
}

const app = mount(App, { target: document.getElementById('app')! })

export default app
