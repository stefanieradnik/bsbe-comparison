import logging
import sqlite3
import os
from pathlib import Path

import yaml

from data_extractor import BerlinExtractor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataPipeline:
    def __init__(self, config):
        self.config = config
        
    def _create_db(self):
        db_path = self.config["db_path"]
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS gesetze (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bundesland TEXT NOT NULL,
            paragraph TEXT NOT NULL,
            absatz TEXT,
            titel TEXT,
            text TEXT
        )
        """)
        conn.commit()
        conn.close()
    
    def _delete_db(self):
        os.remove(self.config["db_path"])

    def run(self):
        if os.path.exists(self.config["db_path"]):
            logger.info("Delete existing db")
            self._delete_db()
            
        logger.info("Create db")
        self._create_db()
        
        logger.info("Starting data extraction pipeline...")

        extractors = [
            BerlinExtractor(Path(self.config["raw_data_path"]) / self.config["bundeslaender_path"]["berlin"])
        ]

        for extractor in extractors:
            logger.info(f"Extracting data for {extractor.BUNDESLAND}")
            data = extractor.extract()
            
            # save data in db
            with sqlite3.connect(self.config["db_path"]) as conn:
                cursor = conn.cursor()
                cursor.executemany(
                    """
                    INSERT INTO gesetze (bundesland, paragraph, absatz, titel, text)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    data
                )
