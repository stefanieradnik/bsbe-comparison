import sqlite3


def get_unique_bundeslaender(db_path):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT bundesland FROM gesetze")
        bundeslaender = cursor.fetchall()
    unique_bundeslaender = [bl[0] for bl in bundeslaender]

    return unique_bundeslaender


def get_unique_paragraphs(db_path, bundesland):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT paragraph FROM gesetze WHERE bundesland = ?", (bundesland,))
        paragraphs = cursor.fetchall()
    unique_paragraphs = [pa[0] for pa in paragraphs]

    return unique_paragraphs


def get_unique_absaetze(db_path, bundesland, paragraph):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT DISTINCT absatz FROM gesetze WHERE bundesland = ? AND paragraph = ?",
            (bundesland, paragraph),
        )
        absaetze = cursor.fetchall()
    unique_absaetze = [ab[0] for ab in absaetze]

    return unique_absaetze


def get_text_from_id(db_path, id):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT text FROM gesetze WHERE id = ?", (id,))
        text = cursor.fetchone()

    return text[0]


def get_absatz_candidates(db_path, bundesland):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, text FROM gesetze WHERE bundesland = ?", (bundesland,))
        candidates = cursor.fetchall()

    return candidates


def get_full_paragraph_text(db_path, bundesland, paragraph):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT text FROM gesetze WHERE bundesland = ? AND paragraph = ? ORDER BY absatz",
            (bundesland, paragraph),
        )
        texts = [row[0] for row in cursor.fetchall()]

    return "\n".join(texts)


def get_paragraph_candidates(db_path, bundesland):
    paragraphs = get_unique_paragraphs(db_path, bundesland)

    return [
        (paragraph, get_full_paragraph_text(db_path, bundesland, paragraph))
        for paragraph in paragraphs
    ]
