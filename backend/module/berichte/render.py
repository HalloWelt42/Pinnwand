"""Rendert einen normalisierten Bericht als PDF (WeasyPrint), CSV oder Markdown."""
from __future__ import annotations

import csv
import html as _html
import io
from datetime import datetime

_CSS = """
@page {
  size: A4; margin: 18mm 16mm 20mm;
  @bottom-center { content: "Seite " counter(page) " / " counter(pages); font-size: 9pt; color: #666; }
}
body { font-family: "Helvetica Neue", "Segoe UI", Arial, sans-serif; color: #1a1a1a; font-size: 10.5pt; }
h1 { font-size: 18pt; margin: 0 0 2pt; }
.zeitraum { color: #666; font-size: 10pt; margin: 0 0 14pt; }
h2 { font-size: 12.5pt; margin: 16pt 0 6pt; border-bottom: 1px solid #ccc; padding-bottom: 2pt; }
table { border-collapse: collapse; width: 100%; margin: 0 0 6pt; }
th, td { border: 1px solid #ddd; padding: 4pt 7pt; text-align: left; font-size: 9.5pt; vertical-align: top; }
th { background: #f1f1f4; }
tr.summe td { font-weight: bold; background: #fafafa; }
"""


def _esc(s: object) -> str:
    return _html.escape(str(s))


def _html_doc(bericht: dict) -> str:
    teile = [
        f"<h1>{_esc(bericht['titel'])}</h1>",
        f"<div class='zeitraum'>{_esc(bericht['zeitraum'])} &middot; erzeugt {datetime.now().strftime('%d.%m.%Y %H:%M')}</div>",
    ]
    for ab in bericht["abschnitte"]:
        teile.append(f"<h2>{_esc(ab['titel'])}</h2>")
        teile.append("<table><thead><tr>" + "".join(f"<th>{_esc(s)}</th>" for s in ab["spalten"]) + "</tr></thead><tbody>")
        if not ab["zeilen"]:
            teile.append(f"<tr><td colspan='{len(ab['spalten'])}'>keine Daten</td></tr>")
        for z in ab["zeilen"]:
            teile.append("<tr>" + "".join(f"<td>{_esc(c)}</td>" for c in z) + "</tr>")
        if ab.get("summe"):
            teile.append("<tr class='summe'>" + "".join(f"<td>{_esc(c)}</td>" for c in ab["summe"]) + "</tr>")
        teile.append("</tbody></table>")
    return f"<!doctype html><html><head><meta charset='utf-8'><style>{_CSS}</style></head><body>{''.join(teile)}</body></html>"


def pdf(bericht: dict) -> bytes:
    from weasyprint import HTML  # später Import: Start auch ohne WeasyPrint möglich

    return HTML(string=_html_doc(bericht)).write_pdf()


def csv_text(bericht: dict) -> str:
    out = io.StringIO()
    w = csv.writer(out, delimiter=";")
    w.writerow([bericht["titel"], bericht["zeitraum"]])
    w.writerow([])
    for ab in bericht["abschnitte"]:
        w.writerow([ab["titel"]])
        w.writerow(ab["spalten"])
        for z in ab["zeilen"]:
            w.writerow(z)
        if ab.get("summe"):
            w.writerow(ab["summe"])
        w.writerow([])
    return out.getvalue()


def markdown_text(bericht: dict) -> str:
    zeilen = [f"# {bericht['titel']}", f"_{bericht['zeitraum']}_", ""]
    for ab in bericht["abschnitte"]:
        zeilen.append(f"## {ab['titel']}")
        zeilen.append("| " + " | ".join(ab["spalten"]) + " |")
        zeilen.append("|" + "|".join("---" for _ in ab["spalten"]) + "|")
        for z in ab["zeilen"]:
            zeilen.append("| " + " | ".join(str(c).replace("|", "\\|") for c in z) + " |")
        if ab.get("summe"):
            zeilen.append("| " + " | ".join(str(c) for c in ab["summe"]) + " |")
        zeilen.append("")
    return "\n".join(zeilen)


def rendere(bericht: dict, fmt: str) -> tuple[bytes, str]:
    """Gibt (Inhalt, MIME) zurück."""
    if fmt == "pdf":
        return pdf(bericht), "application/pdf"
    if fmt == "csv":
        return csv_text(bericht).encode("utf-8-sig"), "text/csv; charset=utf-8"
    if fmt in ("markdown", "md"):
        return markdown_text(bericht).encode("utf-8"), "text/markdown; charset=utf-8"
    raise ValueError(f"Unbekanntes Format: {fmt}")
