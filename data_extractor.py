import re
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup

from utils import extract_xml_from_zip


class BerlinExtractor:
    BUNDESLAND = "Berlin"

    def __init__(self, path):
        self.path = path

    def extract(self):
        doknr_p_re = re.compile(r"P\d+[a-z]?$")

        xml_bytes = extract_xml_from_zip(self.path)
        root = ET.fromstring(xml_bytes)

        rows = []

        for child in root:
            doknr = child.attrib.get("doknr", "")
            if doknr_p_re.search(doknr):
                # extract textdata
                textdaten = child.find(".//textdaten")
                textdaten_xml = ET.tostring(textdaten, encoding="unicode")
                soup = BeautifulSoup(textdaten_xml, "html.parser")

                # extract paragraph number and title
                h = soup.find("h4") or soup.find("h5")  # je nach XML-Struktur
                h_text_parts = [t.strip() for t in h.stripped_strings]
                paragraph = h_text_parts[0] if len(h_text_parts) > 0 else ""
                paragraph = paragraph.split(" ")[-1] if paragraph else ""
                titel = h_text_parts[1] if len(h_text_parts) > 1 else ""

                for p in soup.find_all("p"):

                    # sup entfernen (Fußnotenziffern etc.)
                    for sup in p.find_all("sup"):
                        sup.decompose()

                    # Anchor-Tags entfernen, damit sie nicht als Text auftauchen
                    for atag in p.find_all("a"):
                        atag.decompose()

                    text = " ".join(p.stripped_strings)
                    text = re.sub(r"\s+", " ", text).strip()

                    # Optional: Absatznummer (1), (2) ... herausziehen
                    m = re.match(r"^\((\d+)\)\s*(.*)$", text)
                    absatz_nr = int(m.group(1)) if m else ""
                    absatz_text = m.group(2) if m else text

                    rows.append(
                        (
                            self.BUNDESLAND.lower(),
                            paragraph,
                            absatz_nr,
                            titel,
                            absatz_text,
                        )
                    )

        return rows
