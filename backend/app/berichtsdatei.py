"""Ein Bericht als Datei: derselbe Inhalt (Titel, Zeitraum, Abschnitte mit Spalten, Zeilen, Summe, Fuß) als PDF, als
Tabelle (CSV mit Semikolon, wie Tabellenprogramme sie hierzulande lesen) oder als Markdown. Reine Ausgabe ohne Wissen
über die Pinnwand; was im Bericht steht, rechnet anwendung/berichte.py."""

from __future__ import annotations

import csv
import io
from pathlib import Path

from fpdf import FPDF, FontFace

from .modell import Modell
from .regeln.tage import datum_text

SCHRIFTEN = Path(__file__).parent / "schriften"
ENDUNG = {"pdf": "pdf", "tabelle": "csv", "markdown": "md"}
INHALTSTYP = {"pdf": "application/pdf", "tabelle": "text/csv", "markdown": "text/markdown"}
#: Spalten mit Zeiten stehen rechtsbündig und schmal, kurze Angaben schmal, der Rest teilt sich die Breite
ZAHLEN = {"Soll", "Ist", "Differenz", "Zeit", "Schätzung"}
KURZ = {"Tag", "Schlüssel", "Erledigt", "Zuständig", "Personen"}


class Abschnitt(Modell):
    titel: str
    spalten: list[str]
    zeilen: list[list[str]]
    summe: list[str] | None = None
    fuss: str | None = None


class BerichtInhalt(Modell):
    titel: str
    zeitraum: str
    abschnitte: list[Abschnitt]


def als_markdown(b: BerichtInhalt) -> str:
    teile = [f"# {b.titel}", "", f"Zeitraum: {b.zeitraum}", ""]
    for s in b.abschnitte:
        teile += [f"## {s.titel}", "", f"| {' | '.join(s.spalten)} |", f"| {' | '.join('---' for _ in s.spalten)} |"]
        teile += [f"| {' | '.join(z)} |" for z in s.zeilen]
        if s.summe:
            teile.append(f"| {' | '.join(f'**{x}**' if x else '' for x in s.summe)} |")
        if s.fuss:
            teile += ["", s.fuss]
        teile.append("")
    return "\n".join(teile)


def als_tabelle(b: BerichtInhalt) -> str:
    puffer = io.StringIO()
    w = csv.writer(puffer, delimiter=";", lineterminator="\r\n")
    w.writerow([b.titel])
    w.writerow([f"Zeitraum: {b.zeitraum}"])
    for s in b.abschnitte:
        w.writerow([])
        w.writerow([s.titel])
        w.writerow(s.spalten)
        w.writerows(s.zeilen)
        if s.summe:
            w.writerow(s.summe)
    return puffer.getvalue()


class Blatt(FPDF):
    """A4 hochkant mit Barlow, im Fuß Quelle, Tag der Erstellung und Seitenzahl."""

    def __init__(self, fuss: str) -> None:
        super().__init__(orientation="P", unit="mm", format="A4")
        self.fusstext = fuss
        self.add_font("Barlow", "", SCHRIFTEN / "Barlow-Regular.ttf")
        self.add_font("Barlow", "B", SCHRIFTEN / "Barlow-SemiBold.ttf")
        self.set_auto_page_break(auto=True, margin=16)
        self.set_margins(16, 16, 16)

    def footer(self) -> None:
        self.set_y(-12)
        self.set_font("Barlow", "", 8)
        self.set_text_color(110)
        self.cell(0, 6, f"{self.fusstext}, Seite {self.page_no()} von {{nb}}", align="C")


def breiten(spalten: list[str], gesamt: float) -> tuple[float, ...]:
    gewicht = [1.0 if s in ZAHLEN else 1.3 if s in KURZ else 3.0 for s in spalten]
    return tuple(gesamt * g / sum(gewicht) for g in gewicht)


def als_pdf(b: BerichtInhalt, erstellt: str) -> bytes:
    pdf = Blatt(f"Pinnwand, erstellt am {datum_text(erstellt[:10])} um {erstellt[11:16]}")
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_font("Barlow", "B", 16)
    pdf.cell(0, 9, b.titel, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Barlow", "", 10)
    pdf.set_text_color(90)
    pdf.cell(0, 6, f"Zeitraum: {b.zeitraum}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0)
    kopf = FontFace(emphasis="BOLD", fill_color=(232, 236, 240))
    for s in b.abschnitte:
        pdf.ln(4)
        pdf.set_font("Barlow", "B", 12)
        pdf.cell(0, 7, s.titel, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Barlow", "", 9)
        ausrichtung = tuple("RIGHT" if sp in ZAHLEN else "LEFT" for sp in s.spalten)
        with pdf.table(col_widths=breiten(s.spalten, pdf.epw), text_align=ausrichtung, headings_style=kopf,
                       line_height=5.2, padding=(0.6, 1.6), borders_layout="HORIZONTAL_LINES", width=pdf.epw) as tabelle:
            tabelle.row(s.spalten)
            for z in s.zeilen:
                tabelle.row(z)
            if s.summe:
                tabelle.row(s.summe, style=FontFace(emphasis="BOLD"))
        if s.fuss:
            pdf.ln(1)
            pdf.set_font("Barlow", "", 8)
            pdf.set_text_color(90)
            pdf.multi_cell(0, 4.2, s.fuss, new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(0)
    return bytes(pdf.output())


def datei_aus(b: BerichtInhalt, format: str, erstellt: str) -> bytes:
    """Der Inhalt einer Berichtsdatei im gewählten Format."""
    if format == "pdf":
        return als_pdf(b, erstellt)
    if format == "tabelle":
        return als_tabelle(b).encode("utf-8-sig")
    return als_markdown(b).encode("utf-8")
