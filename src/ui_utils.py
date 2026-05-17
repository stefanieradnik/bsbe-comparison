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
