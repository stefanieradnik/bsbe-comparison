import re
import xml.etree.ElementTree as ET

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

            # Wir lesen NUR direkte Kinder von <textdaten>, damit <dd>/<dt> nicht als eigene Absätze zählen
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
                    absatz_text = "\n".join(
                        [p for p in current_absatz_text_parts if p]
                    ).strip()
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


class BayernExtractor:
    pass