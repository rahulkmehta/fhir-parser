import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.config import settings
from app.ingestion.pipeline import run_ingestion

if __name__ == "__main__":
    run_ingestion(settings.DATA_DIR, settings.DATABASE_URL)
