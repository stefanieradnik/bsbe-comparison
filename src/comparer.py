import sqlite3

from thefuzz import fuzz


class FuzzyComparer:

    def __init__(self, config):
        self.config = config

    def compare(self, ref_id, target_bl):
        conn = sqlite3.connect(self.config["db_path"])
        cursor = conn.cursor()

        cursor.execute(
            """SELECT text
                        FROM gesetze
                        WHERE id = ? """,
            (ref_id,),
        )

        ref_text = cursor.fetchone()[0]

        cursor.execute("SELECT * FROM gesetze WHERE bundesland = ?", (target_bl,))

        sim = []
        for target_row in cursor.fetchall():
            target_text = target_row[-1]
            sim.append({"tagret_id": target_row[0], "ratio": fuzz.ratio(ref_text, target_text)})

        best_ratio = max(sim, key=lambda x: x["ratio"])
        best_target_id = best_ratio["tagret_id"]

        cursor.execute(
            """SELECT *
                        FROM gesetze
                        WHERE id = ? """,
            (best_target_id,),
        )

        best_text = cursor.fetchone()[-1]

        cursor.close()

        return best_text, best_target_id
