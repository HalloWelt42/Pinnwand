<script lang="ts">
  import Markdown, { type Plugin } from 'svelte-exmarkdown'
  import { gfmPlugin } from 'svelte-exmarkdown/gfm'
  import remarkBreaks from 'remark-breaks'
  import remarkMath from 'remark-math'
  import remarkEmoji from 'remark-emoji'
  import rehypeKatex from 'rehype-katex'
  import rehypeHighlight from 'rehype-highlight'
  import DOMPurify from 'dompurify'
  import mermaid from 'mermaid'
  import 'katex/dist/katex.min.css'
  import 'highlight.js/styles/github-dark.css'

  let { md = '' }: { md?: string } = $props()

  // Reihenfolge wie im bewaehrten Vorbild: Umbrueche vor Mathe.
  const plugins: Plugin[] = [
    gfmPlugin(),
    { remarkPlugin: remarkBreaks },
    { remarkPlugin: remarkMath },
    { remarkPlugin: [remarkEmoji] },
    { rehypePlugin: [rehypeKatex, { throwOnError: false, strict: false }] },
    { rehypePlugin: [rehypeHighlight, { detect: true, ignoreMissing: true }] },
  ]

  let mermaidBereit = false
  function initMermaid(): void {
    if (mermaidBereit) return
    mermaid.initialize({
      startOnLoad: false,
      securityLevel: 'strict',
      theme: 'base',
      fontFamily: '"IBM Plex Sans", system-ui, sans-serif',
      themeVariables: {
        background: 'transparent',
        primaryColor: '#26303a',
        primaryTextColor: '#eceef1',
        primaryBorderColor: '#4f9be8',
        lineColor: '#7cb6ee',
        secondaryColor: '#2c3742',
        tertiaryColor: '#1a1d23',
      },
    })
    mermaidBereit = true
  }

  let wurzel = $state<HTMLElement | null>(null)
  let zaehler = 0

  async function nachbearbeiten(el: HTMLElement): Promise<void> {
    // 1) Mermaid-Codebloecke rendern.
    const mermaidBloecke = el.querySelectorAll<HTMLElement>('code.language-mermaid')
    if (mermaidBloecke.length) {
      initMermaid()
      for (const code of Array.from(mermaidBloecke)) {
        const pre = code.closest('pre')
        if (!pre) continue
        const quelle = code.textContent ?? ''
        try {
          const { svg } = await mermaid.render(`mmd-${zaehler++}`, quelle)
          const huelle = document.createElement('div')
          huelle.className = 'diagram'
          huelle.innerHTML = DOMPurify.sanitize(svg, { USE_PROFILES: { svg: true, svgFilters: true } })
          pre.replaceWith(huelle)
        } catch {
          /* ungueltiges Diagramm bleibt als Codeblock stehen */
        }
      }
    }
    // 2) Kopierknopf an Codebloecke.
    el.querySelectorAll<HTMLElement>('pre > code').forEach((code) => {
      const pre = code.parentElement as HTMLElement
      if (!pre || pre.dataset.kopf === '1') return
      pre.dataset.kopf = '1'
      const knopf = document.createElement('button')
      knopf.className = 'md-kopf'
      knopf.type = 'button'
      knopf.textContent = 'Kopieren'
      knopf.onclick = async () => {
        await navigator.clipboard.writeText(code.textContent ?? '')
        knopf.textContent = 'Kopiert'
        setTimeout(() => (knopf.textContent = 'Kopieren'), 1200)
      }
      pre.appendChild(knopf)
    })
    // 3) Externe Links sicher oeffnen.
    el.querySelectorAll('a[href]').forEach((a) => {
      a.setAttribute('target', '_blank')
      a.setAttribute('rel', 'noopener noreferrer')
    })
  }

  $effect(() => {
    void md
    const el = wurzel
    if (!el) return
    // Nach dem Render von svelte-exmarkdown nachbearbeiten.
    queueMicrotask(() => nachbearbeiten(el))
  })
</script>

<div class="md-body" bind:this={wurzel}>
  <Markdown {md} {plugins} />
</div>

<style>
  .md-body {
    font-family: var(--font-text);
    font-size: 13.5px;
    line-height: 1.6;
    color: var(--text-1);
    word-break: break-word;
  }
  .md-body :global(h1),
  .md-body :global(h2),
  .md-body :global(h3) {
    font-family: var(--font-display);
    line-height: 1.3;
    margin: 0.8em 0 0.4em;
  }
  .md-body :global(h1) { font-size: 1.5em; }
  .md-body :global(h2) { font-size: 1.3em; }
  .md-body :global(h3) { font-size: 1.12em; }
  .md-body :global(p) { margin: 0.5em 0; }
  .md-body :global(ul),
  .md-body :global(ol) { margin: 0.5em 0; padding-left: 1.4em; }
  .md-body :global(li) { margin: 0.2em 0; }
  .md-body :global(a) { color: var(--hl-primary-text); text-decoration: underline; }
  .md-body :global(code) {
    font-family: var(--font-mono);
    font-size: 0.88em;
    background: var(--surface-2);
    padding: 1px 5px;
    border-radius: var(--r-s);
  }
  .md-body :global(pre) {
    position: relative;
    background: #0d1117;
    border: 1px solid var(--border);
    border-radius: var(--r-m);
    padding: 11px 12px;
    overflow-x: auto;
    margin: 0.7em 0;
  }
  .md-body :global(pre code) {
    background: none;
    padding: 0;
    font-size: 12px;
  }
  .md-body :global(.md-kopf) {
    position: absolute;
    top: 6px;
    right: 6px;
    font-size: 10.5px;
    padding: 3px 8px;
    border-radius: var(--r-s);
    border: 1px solid var(--border-2);
    background: var(--surface-3);
    color: var(--text-2);
    opacity: 0;
    transition: opacity 0.12s;
  }
  .md-body :global(pre:hover .md-kopf) { opacity: 1; }
  .md-body :global(blockquote) {
    margin: 0.7em 0;
    padding: 4px 12px;
    background: var(--surface-2);
    border-radius: var(--r-s);
    color: var(--text-2);
  }
  .md-body :global(table) {
    border-collapse: collapse;
    margin: 0.7em 0;
    font-size: 12.5px;
  }
  .md-body :global(th),
  .md-body :global(td) {
    border: 1px solid var(--border);
    padding: 5px 9px;
    text-align: left;
  }
  .md-body :global(th) { background: var(--surface-2); }
  .md-body :global(img) { max-width: 100%; border-radius: var(--r-s); }
  .md-body :global(.diagram) {
    margin: 0.7em 0;
    padding: 10px;
    background: var(--surface-2);
    border: 1px solid var(--border);
    border-radius: var(--r-m);
    overflow-x: auto;
  }
  .md-body :global(.diagram svg) { max-width: 100%; height: auto; }
  .md-body :global(.task-list-item) { list-style: none; }
  .md-body :global(:first-child) { margin-top: 0; }
  .md-body :global(:last-child) { margin-bottom: 0; }
</style>
