import argparse
import logging
import time
import zipfile
from string import ascii_lowercase

import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "https://gesetze.co"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) jura_bsbe-data-collector/1.0 "
    "(+https://github.com/stefanieradnik/bsbe-comparison)"
)


def fetch_paragraph(session, land, law, nummer):
    """Lädt eine Paragraph-Seite. Gibt den HTML-Text zurück oder None, wenn die
    Nummer nicht existiert (gesetze.co leitet dann auf ?error=invalid_norm um)."""
    url = f"{BASE_URL}/{land}/{law}/{nummer}"
    resp = session.get(url, allow_redirects=False, timeout=15)
    if resp.status_code == 200:
        # Der Server sendet keinen Charset im Content-Type-Header, wodurch
        # requests faelschlich auf ISO-8859-1 statt UTF-8 zurueckfaellt.
        return resp.content.decode("utf-8")
    return None


def discover_paragraphs(session, land, law, start=1, hard_cap=450, delay=0.25):
    """Findet alle vorhandenen Paragraphen eines Gesetzes durch vollstaendiges
    Durchprobieren der Nummerierung start..hard_cap (inkl. Buchstaben-Suffixe
    wie '11a'). Es wird bewusst NICHT nach einer Serie von Fehltreffern
    abgebrochen: manche Gesetze haben grosse Luecken durch aufgehobene
    Paragraphen (z.B. SPolG Saarland: 27-39 fehlen, 40+ existieren wieder)."""
    pages = {}

    for n in range(start, hard_cap + 1):
        base = str(n)
        html = fetch_paragraph(session, land, law, base)
        time.sleep(delay)

        if html is not None:
            pages[base] = html
            logger.info(f"{land}/{law}/{base} gefunden")

            for letter in ascii_lowercase:
                suffix = base + letter
                html_suffix = fetch_paragraph(session, land, law, suffix)
                time.sleep(delay)
                if html_suffix is None:
                    break
                pages[suffix] = html_suffix
                logger.info(f"{land}/{law}/{suffix} gefunden")

    return pages


def save_zip(pages, out_path):
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for nummer, html in sorted(pages.items()):
            zf.writestr(f"{nummer}.html", html)


def main():
    parser = argparse.ArgumentParser(
        description="Scrapt ein Gesetz von gesetze.co in ein lokales Zip."
    )
    parser.add_argument("--land", required=True, help="Länderkürzel, z.B. TH, BW, BB")
    parser.add_argument("--law", required=True, help="Gesetzeskürzel, z.B. PAG, PolG, BbgPolG")
    parser.add_argument("--out", required=True, help="Zielpfad für die Zip-Datei")
    parser.add_argument(
        "--start", type=int, default=1, help="Erste zu pruefende Paragraphennummer (Default: 1)"
    )
    parser.add_argument(
        "--end", type=int, default=450, help="Letzte zu pruefende Paragraphennummer (Default: 450)"
    )
    args = parser.parse_args()

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    logger.info(f"Scraping {args.land}/{args.law} von {BASE_URL} ({args.start}-{args.end})")
    pages = discover_paragraphs(session, args.land, args.law, start=args.start, hard_cap=args.end)
    logger.info(f"{len(pages)} Paragraphen gefunden, schreibe nach {args.out}")
    save_zip(pages, args.out)


if __name__ == "__main__":
    main()
