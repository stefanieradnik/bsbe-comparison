import re
import xml.etree.ElementTree as ET

import pdfplumber
from bs4 import BeautifulSoup

from utils import extract_xml_from_zip


class BerlinExtractor:
    BUNDESLAND = "Berlin"

    def __init__(self, path):
        self.path = path

    def extract(self):
        para_pattern = re.compile(r"P\d+[a-z]?$")

        xml_bytes = extract_xml_from_zip(self.path)
        root = ET.fromstring(xml_bytes)

        rows = []

        def clean_tag(tag):
            """Entfernt sup/a und normalisiert Whitespace."""
            for sup in tag.find_all("sup"):
                sup.decompose()
            for atag in tag.find_all("a"):
                atag.decompose()

            text = " ".join(tag.stripped_strings)
            return re.sub(r"\s+", " ", text).strip()

        for child in root:
            doknr = child.attrib.get("doknr", "")
            if not para_pattern.search(doknr):
                continue

            textdaten = child.find(".//textdaten")
            if textdaten is None:
                continue

            textdaten_xml = ET.tostring(textdaten, encoding="unicode")
            soup = BeautifulSoup(textdaten_xml, "html.parser")

            # paragraph number and title
            h = soup.find("h4") or soup.find("h5")
            h_text_parts = [t.strip() for t in h.stripped_strings] if h else []
            paragraph = h_text_parts[0] if len(h_text_parts) > 0 else ""
            paragraph = paragraph.split(" ")[-1] if paragraph else ""
            titel = h_text_parts[1] if len(h_text_parts) > 1 else ""

            # Wir lesen NUR direkte Kinder von <textdaten>,
            # damit <dd>/<dt> nicht als eigene Absätze zählen
            textdaten_node = soup.find("textdaten")  # kann None sein, je nach Parser
            container = textdaten_node if textdaten_node else soup

            current_absatz_nr = None
            current_absatz_text_parts = []  # sammeln, später als String zusammenbauen

            def flush_current_absatz():
                """Schreibt den aktuellen Absatz als Row weg."""
                nonlocal current_absatz_nr, current_absatz_text_parts
                if current_absatz_nr is None and current_absatz_text_parts:
                    current_absatz_nr = 1

                if current_absatz_nr is not None:
                    absatz_text = "\n".join([p for p in current_absatz_text_parts if p]).strip()
                    rows.append(
                        (
                            f"{self.BUNDESLAND.lower()}_{paragraph}_{current_absatz_nr}",
                            self.BUNDESLAND.lower(),
                            paragraph,
                            current_absatz_nr,
                            titel,
                            absatz_text,
                        )
                    )

                current_absatz_nr = None
                current_absatz_text_parts = []

            # Nur <p> und <dl> auf oberster Ebene verarbeiten
            for node in container.find_all(["p", "dl"], recursive=False):
                if node.name == "p":
                    text = clean_tag(node)
                    if not text:
                        continue

                    # Absatznummer (1), (2), ...
                    m = re.match(r"^\((\d+)\)\s*(.*)$", text)
                    if m:
                        # neuer Absatz startet -> alten wegschreiben
                        flush_current_absatz()
                        current_absatz_nr = int(m.group(1))
                        rest = m.group(2).strip()
                        if rest:
                            current_absatz_text_parts.append(rest)
                    else:
                        # Fortsetzung des aktuellen Absatzes
                        if current_absatz_nr is None:
                            current_absatz_nr = 1
                        current_absatz_text_parts.append(text)

                elif node.name == "dl":
                    # Unterpunkte (dt/dd) an aktuellen Absatz anhängen, NICHT als eigene Rows
                    dts = node.find_all("dt", recursive=False)
                    dds = node.find_all("dd", recursive=False)

                    items = []
                    for i, dd in enumerate(dds):
                        nr = clean_tag(dts[i]) if i < len(dts) else ""
                        body = clean_tag(dd)
                        line = f"{nr} {body}".strip()
                        if line:
                            items.append(line)

                    if items:
                        if current_absatz_nr is None:
                            current_absatz_nr = 1
                        # als strukturierter Text (jede Nummer eigene Zeile)
                        current_absatz_text_parts.extend(items)

            # letzten Absatz nicht vergessen
            flush_current_absatz()

        return rows


class BayernExtractor:
    BUNDESLAND = "Bayern"

    def __init__(self, path):
        self.path = path

    def extract(self):
        para_pattern = re.compile(r"^P_\d+$")

        xml_bytes = extract_xml_from_zip(self.path)
        root = ET.fromstring(xml_bytes)

        rows = []

        for el in root.findall(".//einzelnorm"):
            norm_id = el.get("einzelnormid", "")
            if para_pattern.match(norm_id):
                para_nr = el.findtext(".//para.nr", "").strip().split(" ")[-1]
                para_titel = el.findtext(".//para.titel", "").strip()

                for ja in el.findall(".//jurAbsatz"):
                    abs_nr = ja.findtext("absatz.nr", "")

                    if abs_nr is None or not abs_nr.strip():
                        abs_nr = "1"
                    else:
                        abs_nr = abs_nr.strip("()")

                    abs_text_element = ja.find("absatz.text")

                    if abs_text_element is not None:
                        abs_text = " ".join(
                            t.strip() for t in abs_text_element.itertext() if t.strip()
                        )
                    else:
                        abs_text = ""

                    rows.append(
                        (
                            f"{self.BUNDESLAND.lower()}_{para_nr}_{abs_nr}",
                            self.BUNDESLAND.lower(),
                            para_nr,
                            abs_nr,
                            para_titel,
                            abs_text,
                        )
                    )

        return rows


class RlpExtractor:
    BUNDESLAND = "Rheinland-Pfalz"

    def __init__(self, path):
        self.path = path

    def read_pdf(self):
        text = ""
        with pdfplumber.open(self.path) as pdf:
            for page in pdf.pages[10:]:
                page_text = page.extract_text()

                if page_text:
                    page_text = re.sub(r"-\s*Seite\s*\d+\s*von\s*\d+\s*-", "", page_text)

                    text += page_text + "\n"
        return text

    def clean_text(self, text):
        # remove praeambel
        text = text[538:]
        # text to list
        text_list = list(text.split("\n"))
        return text_list

    def extract(self):
        rows = []

        TITEL_ZEILEN = {
            "16b": 2,
            "26": 2,
            "36": 2,
            "54": 2,
            "55": 2,
            "58": 2,
            "59": 2,
            "67": 2,
            "68": 2,
            "101": 3,
            "102": 2,
        }

        text = self.read_pdf()
        text = self.clean_text(text)

        current_para = None
        current_absatz = None
        current_text = []
        para_titel = ""

        seen_absatz = False

        titel_aktiv = False
        titel_zeilen_offen = 0

        for elem in text:
            elem = elem.strip()

            if not elem:
                continue

            # Titel erfassen
            if titel_aktiv:
                if para_titel:
                    para_titel += " " + elem
                else:
                    para_titel = elem

                titel_zeilen_offen -= 1

                if titel_zeilen_offen == 0:
                    titel_aktiv = False

                continue

            # Paragraph erkennen
            para_match = re.match(r"^§\s*(\d+[a-zA-Z]?)$", elem)

            if para_match:

                # Vorherigen Paragraphen speichern
                if current_para and current_text:
                    rows.append(
                        (
                            f"{self.BUNDESLAND.lower()}_{current_para}_"
                            f"{current_absatz if current_absatz else '1'}",
                            self.BUNDESLAND.lower(),
                            current_para,
                            current_absatz if current_absatz else "1",
                            para_titel,
                            " ".join(current_text),
                        )
                    )

                current_para = para_match.group(1)
                current_absatz = None
                current_text = []
                seen_absatz = False
                para_titel = ""

                # Anzahl der Titelzeilen festlegen
                titel_zeilen_offen = TITEL_ZEILEN.get(current_para, 1)
                titel_aktiv = True

                continue

            # Absatz erkennen
            abs_match = re.match(r"^\((\d+)\)", elem)

            if abs_match:

                if current_absatz is not None and current_text:
                    rows.append(
                        (
                            f"{self.BUNDESLAND.lower()}_{current_para}_{current_absatz}",
                            self.BUNDESLAND.lower(),
                            current_para,
                            current_absatz,
                            para_titel,
                            " ".join(current_text),
                        )
                    )

                current_absatz = abs_match.group(1)
                seen_absatz = True

                text_part = re.sub(r"^\(\d+\)\s*", "", elem)
                current_text = [text_part]

                continue

            # Normaler Text
            if not seen_absatz:
                current_absatz = "1"

            current_text.append(elem)

        # Letzten Eintrag speichern
        if current_para and current_text:
            rows.append(
                (
                    f"{self.BUNDESLAND.lower()}_{current_para}_"
                    f"{current_absatz if current_absatz else '1'}",
                    self.BUNDESLAND.lower(),
                    current_para,
                    current_absatz if current_absatz else "1",
                    para_titel,
                    " ".join(current_text),
                )
            )

        return rows


class NrwExtractor:
    BUNDESLAND = "Nordrhein-Westfalen"

    # Fließtext beginnt nach dem Inhaltsverzeichnis auf dieser Seite (0-indiziert)
    FIRST_CONTENT_PAGE = 8

    # Füllfarbe der Fußnoten-Boxen im PDF (RGB, 0-1)
    BOX_FILL_COLOR = (0.90196, 0.96471, 0.97255)

    # Größer als jede vorkommende Seitenhöhe, um (Seite, top) in einen global
    # sortierbaren Schlüssel umzurechnen - Fußnoten-Boxen können über eine
    # Seitengrenze hinweg reichen (Label auf Seite N, Box auf Seite N+1)
    PAGE_KEY = 10000

    def __init__(self, path):
        self.path = path

    def _global_key(self, page_index, top):
        return page_index * self.PAGE_KEY + top

    def _footnote_box_ranges(self, page, page_index):
        """Globale (top, bottom) Schlüssel der farbig hinterlegten Fußnoten-Boxen."""
        ranges = []
        for curve in page.curves:
            color = curve.get("non_stroking_color")
            if (
                curve.get("fill")
                and color
                and all(abs(a - b) < 0.01 for a, b in zip(color, self.BOX_FILL_COLOR))
            ):
                ranges.append(
                    (
                        self._global_key(page_index, curve["top"]),
                        self._global_key(page_index, curve["bottom"]),
                    )
                )
        return ranges

    def _page_lines(self, page, page_index, box_ranges):
        """Zeilen der Seite als (globaler_key, text, ist_fett), ohne Fußnoten-Boxen
        und Kopf-/Fußzeilen."""
        words = page.extract_words(extra_attrs=["fontname", "size"])

        lines_by_top = {}
        for word in words:
            key = self._global_key(page_index, word["top"])
            in_box = any(top - 1 <= key <= bottom + 1 for top, bottom in box_ranges)
            if in_box or word["size"] < 9:
                continue
            lines_by_top.setdefault(round(word["top"], 1), []).append(word)

        lines = []
        for top in sorted(lines_by_top):
            line_words = sorted(lines_by_top[top], key=lambda w: w["x0"])
            text = " ".join(w["text"] for w in line_words).strip()
            if text:
                bold = any("Bold" in w["fontname"] for w in line_words)
                lines.append((self._global_key(page_index, top), text, bold))
        return lines

    def _document_lines(self, pdf):
        """Alle Zeilen des Normtexts als (text, ist_fett), Fußnoten-Boxen (inkl.
        ihres teils mehrzeiligen Labels "Fußnoten zu ...") vollständig entfernt."""
        flat_lines = []
        flat_boxes = []
        for page_index in range(self.FIRST_CONTENT_PAGE, len(pdf.pages)):
            page = pdf.pages[page_index]
            box_ranges = self._footnote_box_ranges(page, page_index)
            flat_lines.extend(self._page_lines(page, page_index, box_ranges))
            flat_boxes.extend(box_ranges)
        flat_boxes.sort()

        lines = []
        skipping = False
        skip_until = None
        for key, text, bold in flat_lines:
            if skipping:
                if key < skip_until:
                    continue
                skipping = False
            if text.startswith("Fußnoten"):
                # Label kann über mehrere Zeilen und bis auf die Folgeseite
                # umbrechen - alles bis zur zugehörigen Box überspringen
                skipping = True
                skip_until = next((bottom for top, bottom in flat_boxes if top > key), key)
                continue
            lines.append((text, bold))
        return lines

    def extract(self):
        para_pattern = re.compile(r"^§\s*(\d+[a-zA-Z]?)$")
        absatz_pattern = re.compile(r"^\((\d+)\)\s*(.*)$")

        rows = []

        current_para = None
        current_titel = ""
        current_absatz = None
        current_text = []
        collecting_titel = False

        def flush_absatz():
            nonlocal current_absatz, current_text
            if current_para and current_text:
                rows.append(
                    (
                        f"{self.BUNDESLAND.lower()}_{current_para}_{current_absatz or '1'}",
                        self.BUNDESLAND.lower(),
                        current_para,
                        current_absatz or "1",
                        current_titel,
                        " ".join(current_text),
                    )
                )
            current_absatz = None
            current_text = []

        with pdfplumber.open(self.path) as pdf:
            for text, bold in self._document_lines(pdf):
                if text == "Zusatz:":
                    # Nachträge/Erläuterungen zu Grundrechtseinschränkungen am
                    # Ende des Dokuments, kein Normtext mehr
                    break

                para_match = para_pattern.match(text)
                if para_match:
                    flush_absatz()
                    current_para = para_match.group(1)
                    current_titel = ""
                    collecting_titel = True
                    continue

                if collecting_titel:
                    if bold:
                        current_titel = (current_titel + " " + text).strip()
                        continue
                    collecting_titel = False

                if bold:
                    # Abschnitts-/Titelüberschriften zwischen den Paragraphen
                    continue

                absatz_match = absatz_pattern.match(text)
                if absatz_match:
                    flush_absatz()
                    current_absatz = absatz_match.group(1)
                    rest = absatz_match.group(2).strip()
                    if rest:
                        current_text.append(rest)
                elif current_para is not None:
                    current_text.append(text)

        flush_absatz()
        return rows
