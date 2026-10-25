// Markdown der Karten (Beschreibung, Notizen, Kommentare): ein Weg vom geschriebenen Text zur Darstellung, überall gleich.
// Gespeichert wird der Text, wie er geschrieben ist; die Darstellung entsteht hier und ist sicher: Text wird maskiert,
// HTML im Text (in Markdown erlaubt) läuft wie alles andere durch eine Erlaubnisliste, die nur bekannte Elemente und
// Angaben übernimmt. Verstanden werden Überschriften, Absätze (ein Zeilenumbruch bleibt einer, wie in der alten App),
// Listen auch verschachtelt und als Aufgaben, Zitate, Codeblöcke, Tabellen und Trennlinien, im Text fett, kursiv,
// durchgestrichen, Code, Verweise, Adressen und Erwähnungen mit @.

export interface MarkdownOptionen {
  /** voller Name zu einer Erwähnung (@anna) für den Hinweis beim Überfahren; ohne Treffer bleibt sie nur hervorgehoben */
  erwaehnung?: (wort: string) => string | undefined;
}

/** Markdown als sicheres HTML für {@html} */
export function markdownHtml(text: string, optionen: MarkdownOptionen = {}): string {
  return bereinigen(bloecke(text.replace(/\r\n?/g, "\n").split("\n"), optionen));
}

export function maskieren(text: string): string {
  return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

// ═══ Blöcke ══════════════════════════════════════════════════════════════════════════════════════════════

const ZAUN = /^ {0,3}(`{3,}|~{3,})\s*[\w-]*\s*$/;
const UEBERSCHRIFT = /^ {0,3}(#{1,6})\s+(.*?)(?:\s+#+)?\s*$/;
const LINIE = /^ {0,3}([-*_])(?:\s*\1){2,}\s*$/;
const ZITAT = /^ {0,3}>\s?(.*)$/;
const LISTE = /^( *)([-*+]|\d{1,9}[.)])( +)(.*)$/;
const AUFGABE = /^\[([ xX])\]\s+(.*)$/;
const HTML_BLOCK = /^ {0,3}<\/?(?:p|div|ul|ol|li|h[1-6]|blockquote|pre|table|thead|tbody|tr|td|th|hr|br)(?:\s|\/?>|$)/i;
const TRENNER = /^\s*\|?\s*:?-+:?\s*(?:\|\s*:?-+:?\s*)*\|?\s*$/;

function einzug(zeile: string): number {
  return zeile.length - zeile.trimStart().length;
}

/** beginnt hier ein eigener Block (beendet einen Absatz)? */
function beginntBlock(zeile: string): boolean {
  return [ZAUN, UEBERSCHRIFT, LINIE, ZITAT, LISTE, HTML_BLOCK].some((r) => r.test(zeile));
}

function bloecke(zeilen: string[], o: MarkdownOptionen): string {
  const aus: string[] = [];
  let i = 0;
  while (i < zeilen.length) {
    const z = zeilen[i];
    if (!z.trim()) { i++; continue; }
    let m: RegExpMatchArray | null;
    if ((m = z.match(ZAUN))) {
      const zaun = m[1];
      const code: string[] = [];
      i++;
      while (i < zeilen.length && !zeilen[i].trim().startsWith(zaun)) code.push(zeilen[i++]);
      i++;
      aus.push(`<pre><code>${maskieren(code.join("\n"))}</code></pre>`);
    } else if ((m = z.match(UEBERSCHRIFT))) {
      // unter dem Titel der Karte: # wird zur dritten Stufe
      const stufe = Math.min(6, m[1].length + 2);
      aus.push(`<h${stufe}>${zeile(m[2], o)}</h${stufe}>`);
      i++;
    } else if (LINIE.test(z)) {
      aus.push("<hr>");
      i++;
    } else if (HTML_BLOCK.test(z)) {
      // HTML-Block wie in CommonMark: bis zur nächsten Leerzeile, danach durch die Erlaubnisliste
      const start = i;
      while (i < zeilen.length && zeilen[i].trim()) i++;
      aus.push(zeilen.slice(start, i).join("\n"));
    } else if (ZITAT.test(z)) {
      const innen: string[] = [];
      while (i < zeilen.length && (m = zeilen[i].match(ZITAT))) { innen.push(m[1]); i++; }
      aus.push(`<blockquote>${bloecke(innen, o)}</blockquote>`);
    } else if (z.includes("|") && TRENNER.test(zeilen[i + 1] ?? "") && (zeilen[i + 1] ?? "").includes("-")) {
      i = tabelle(zeilen, i, o, aus);
    } else if (LISTE.test(z)) {
      i = liste(zeilen, i, o, aus);
    } else {
      const absatz: string[] = [];
      while (i < zeilen.length && zeilen[i].trim() && (!absatz.length || !beginntBlock(zeilen[i]))) absatz.push(zeilen[i++].trim());
      aus.push(`<p>${zeile(absatz.join("\n"), o).replace(/\n/g, "<br>")}</p>`);
    }
  }
  return aus.join("");
}

function zellen(zeile: string): string[] {
  return zeile.trim().replace(/^\|/, "").replace(/(?<!\\)\|$/, "").split(/(?<!\\)\|/).map((c) => c.trim().replace(/\\\|/g, "|"));
}

/** Tabelle: Kopfzeile, Trennzeile mit Ausrichtung, Zeilen bis zur ersten ohne senkrechten Strich; rollt in sich */
function tabelle(zeilen: string[], i: number, o: MarkdownOptionen, aus: string[]): number {
  const kopf = zellen(zeilen[i]);
  const richtung = zellen(zeilen[i + 1]).map((c) => (c.startsWith(":") && c.endsWith(":") ? "mitte" : c.endsWith(":") ? "rechts" : ""));
  const zelle = (tag: "th" | "td", text: string, n: number): string =>
    `<${tag}${richtung[n] ? ` class="${richtung[n]}"` : ""}>${zeile(text, o)}</${tag}>`;
  let j = i + 2;
  const reihen: string[] = [];
  while (j < zeilen.length && zeilen[j].trim() && zeilen[j].includes("|")) {
    const z = zellen(zeilen[j++]);
    reihen.push(`<tr>${kopf.map((_, n) => zelle("td", z[n] ?? "", n)).join("")}</tr>`);
  }
  aus.push(`<div class="pw-md-tabelle"><table><thead><tr>${kopf.map((c, n) => zelle("th", c, n)).join("")}</tr></thead>` +
    `<tbody>${reihen.join("")}</tbody></table></div>`);
  return j;
}

/** Liste: Punkte gleicher Art auf einer Ebene; was eingerückt folgt, gehört zum Punkt (auch eine Liste darin) */
function liste(zeilen: string[], i: number, o: MarkdownOptionen, aus: string[]): number {
  const erste = zeilen[i].match(LISTE)!;
  const basis = erste[1].length;
  const geordnet = /\d/.test(erste[2]);
  const punkte: string[][] = [];
  let inhalt = 0;
  let locker = false;
  while (i < zeilen.length) {
    const z = zeilen[i];
    const m = z.match(LISTE);
    if (m && m[1].length <= basis + 1 && /\d/.test(m[2]) === geordnet) {
      punkte.push([m[4]]);
      inhalt = m[1].length + m[2].length + m[3].length;
      i++;
      continue;
    }
    const tiefe = Math.min(inhalt, basis + 2);
    if (!z.trim()) {
      const weiter = zeilen.slice(i + 1).find((x) => x.trim());
      const gleich = weiter?.match(LISTE);
      if (weiter !== undefined && (einzug(weiter) >= tiefe || (gleich && gleich[1].length <= basis + 1))) {
        punkte[punkte.length - 1].push("");
        locker = true;
        i++;
        continue;
      }
      break;
    }
    if (einzug(z) >= tiefe) { punkte[punkte.length - 1].push(z.slice(Math.min(inhalt, einzug(z)))); i++; continue; }
    if (!beginntBlock(z)) { punkte[punkte.length - 1].push(z.trim()); i++; continue; }
    break;
  }
  const start = geordnet ? parseInt(erste[2], 10) : 1;
  const tag = geordnet ? "ol" : "ul";
  const html = punkte.map((p) => {
    const a = p[0].match(AUFGABE);
    const teile = a ? [a[2], ...p.slice(1)] : p;
    let innen = bloecke(teile, o);
    if (!locker) innen = innen.replace(/^<p>([\s\S]*?)<\/p>/, "$1");
    if (!a) return `<li>${innen}</li>`;
    const zeichen = a[1] === " " ? "fa-regular fa-square" : "fa-solid fa-square-check";
    return `<li class="aufgabe"><i class="${zeichen}"></i>${innen}</li>`;
  }).join("");
  aus.push(`<${tag}${geordnet && start !== 1 ? ` start="${start}"` : ""}>${html}</${tag}>`);
  return i;
}

// ═══ Im Text ═════════════════════════════════════════════════════════════════════════════════════════════

const IM_TEXT = new RegExp([
  /(?<code>`+)(?<codeText>.+?)\k<code>/u.source,
  /(?<tag><\/?(?:strong|em|b|i|s|del|u|code|kbd|sub|sup|mark|br|a)(?:\s+href="[^"<>]*")?\s*\/?>)/u.source,
  /(?<zeichen>&(?:#\d{1,7}|#x[0-9a-fA-F]{1,6}|[a-zA-Z][a-zA-Z0-9]{1,31});)/u.source,
  /\[(?<verweisText>[^\]\n]+)\]\((?<verweisZiel>[^)\s]+)\)/u.source,
  /(?<adresse>https?:\/\/[^\s<>"]*[^\s<>".,;:!?)\]'])/u.source,
  /\*\*(?<fett>[^\s*](?:.*?[^\s*])?)\*\*/u.source,
  /(?<![\p{L}\p{N}_])__(?<fettStrich>[^\s_](?:.*?[^\s_])?)__(?![\p{L}\p{N}_])/u.source,
  /~~(?<durch>[^\s~](?:.*?[^\s~])?)~~/u.source,
  /\*(?<kursiv>[^\s*](?:.*?[^\s*])?)\*/u.source,
  /(?<![\p{L}\p{N}_])_(?<kursivStrich>[^\s_](?:.*?[^\s_])?)_(?![\p{L}\p{N}_])/u.source,
  /(?<![\p{L}\p{N}_.@])@(?<wer>[\p{L}\p{N}_](?:[\p{L}\p{N}_.-]*[\p{L}\p{N}_])?)/u.source,
].join("|"), "gu");

/** sicheres Ziel eines Verweises: Adressen im Netz, E-Mail, Pfade der App */
function sicheresZiel(ziel: string): boolean {
  return /^(?:https?:\/\/|mailto:)/i.test(ziel) || /^\/(?!\/)/.test(ziel) || ziel.startsWith("#");
}

function verweis(ziel: string, innen: string): string {
  if (!sicheresZiel(ziel)) return innen;
  const fern = /^(?:https?:|mailto:)/i.test(ziel);
  return `<a href="${maskieren(ziel)}"${fern ? ' target="_blank" rel="noopener noreferrer"' : ""}>${innen}</a>`;
}

function zeile(text: string, o: MarkdownOptionen): string {
  let aus = "";
  let bis = 0;
  for (const m of text.matchAll(IM_TEXT)) {
    aus += maskieren(text.slice(bis, m.index));
    bis = (m.index ?? 0) + m[0].length;
    const g = m.groups ?? {};
    if (g.code) aus += `<code>${maskieren(g.codeText)}</code>`;
    else if (g.tag) aus += g.tag;
    else if (g.zeichen) aus += g.zeichen;
    else if (g.verweisText !== undefined) aus += verweis(g.verweisZiel, zeile(g.verweisText, o));
    else if (g.adresse) aus += verweis(g.adresse, maskieren(g.adresse));
    else if ((g.fett ?? g.fettStrich) !== undefined) aus += `<strong>${zeile(g.fett ?? g.fettStrich, o)}</strong>`;
    else if (g.durch !== undefined) aus += `<del>${zeile(g.durch, o)}</del>`;
    else if ((g.kursiv ?? g.kursivStrich) !== undefined) aus += `<em>${zeile(g.kursiv ?? g.kursivStrich, o)}</em>`;
    else if (g.wer) {
      const name = o.erwaehnung?.(g.wer);
      aus += `<span class="pw-erwaehnt"${name ? ` title="${maskieren(name)}"` : ""}>@${maskieren(g.wer)}</span>`;
    }
  }
  return aus + maskieren(text.slice(bis));
}

// ═══ Erlaubnisliste ══════════════════════════════════════════════════════════════════════════════════════

type Angaben = (el: Element) => string;
const OHNE: Angaben = () => "";

function klasse(erlaubt: string[]): Angaben {
  return (el) => {
    const k = el.getAttribute("class") ?? "";
    return erlaubt.includes(k) ? ` class="${k}"` : "";
  };
}

const ERLAUBT: Record<string, Angaben> = {
  p: OHNE, br: OHNE, hr: OHNE, strong: OHNE, b: OHNE, em: OHNE, s: OHNE, del: OHNE, u: OHNE, code: OHNE, pre: OHNE, kbd: OHNE,
  sub: OHNE, sup: OHNE, mark: OHNE, blockquote: OHNE, ul: OHNE, h1: OHNE, h2: OHNE, h3: OHNE, h4: OHNE, h5: OHNE, h6: OHNE,
  table: OHNE, thead: OHNE, tbody: OHNE, tr: OHNE,
  i: klasse(["fa-regular fa-square", "fa-solid fa-square-check"]),
  li: klasse(["aufgabe"]),
  th: klasse(["mitte", "rechts"]),
  td: klasse(["mitte", "rechts"]),
  div: klasse(["pw-md-tabelle"]),
  ol: (el) => (/^\d{1,9}$/.test(el.getAttribute("start") ?? "") ? ` start="${el.getAttribute("start")}"` : ""),
  span: (el) => el.getAttribute("class") === "pw-erwaehnt"
    ? ` class="pw-erwaehnt"${el.getAttribute("title") ? ` title="${maskieren(el.getAttribute("title") ?? "")}"` : ""}` : "",
  a: (el) => {
    const ziel = el.getAttribute("href") ?? "";
    if (!sicheresZiel(ziel)) return "";
    return ` href="${maskieren(ziel)}"${/^(?:https?:|mailto:)/i.test(ziel) ? ' target="_blank" rel="noopener noreferrer"' : ""}`;
  },
};
/** fällt samt Inhalt weg; alles andere Unbekannte verliert nur seine Hülle */
const WEG = new Set(["script", "style", "iframe", "object", "embed", "template", "noscript", "svg", "math", "textarea", "select",
  "button", "input", "form", "link", "meta", "base", "title", "head", "img", "video", "audio", "canvas"]);
const LEERE = new Set(["br", "hr"]);

function knoten(n: Node): string {
  if (n.nodeType === Node.TEXT_NODE) return maskieren(n.textContent ?? "");
  if (n.nodeType !== Node.ELEMENT_NODE) return "";
  const el = n as Element;
  const tag = el.tagName.toLowerCase();
  if (WEG.has(tag)) return "";
  const innen = Array.from(el.childNodes, knoten).join("");
  const angaben = ERLAUBT[tag];
  if (!angaben) return innen;
  // ein Verweis ohne sicheres Ziel bleibt Text
  if (tag === "a" && !angaben(el)) return innen;
  return LEERE.has(tag) ? `<${tag}>` : `<${tag}${angaben(el)}>${innen}</${tag}>`;
}

/** baut das HTML aus dem Baum neu auf, nur mit erlaubten Elementen und Angaben */
function bereinigen(html: string): string {
  const koerper = new DOMParser().parseFromString(html, "text/html").body;
  return Array.from(koerper.childNodes, knoten).join("");
}
