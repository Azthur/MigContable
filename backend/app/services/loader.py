from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict
from backend.app.core.database import dest_engine
import logging

logger = logging.getLogger(__name__)

class DataLoader:
    def __init__(self):
        self.engine = dest_engine

    def load_entries(self, entries: List[Dict]):
        """
        Loads accounting entries into the destination PostgreSQL database.
        Assumes a table 'accounting_entries' exists.
        """
        if not entries:
            logger.info("No entries to load.")
            return

        insert_query = text("""
            INSERT INTO accounting_entries (date, account_code, debit, credit, description, document_ref)
            VALUES (:date, :account, :debit, :credit, :description, :doc_ref)
        """)

        try:
            with self.engine.begin() as connection:
                connection.execute(insert_query, entries)
                logger.info(f"Successfully loaded {len(entries)} entries into PostgreSQL.")
        except Exception as e:
            logger.error(f"Error loading entries: {e}")
            raise e
