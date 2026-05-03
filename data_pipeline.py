import logging
from pathlib import Path

import yaml

from data_extractor import BerlinExtractor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Starting data extraction pipeline...")
    with open("config.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    data_catalog_folder = Path(config["data_catalog_path"])
    data_catalog_folder.mkdir(parents=True, exist_ok=True)

    extractors = [
        BerlinExtractor(Path(config["raw_data_path"]) / config["bundeslaender_path"]["berlin"])
    ]

    for extractor in extractors:
        logger.info(f"Extracting data for {extractor.BUNDESLAND}")
        df = extractor.extract()
        file_path = data_catalog_folder / f"{extractor.BUNDESLAND}.csv"
        df.to_csv(file_path, index=False)
