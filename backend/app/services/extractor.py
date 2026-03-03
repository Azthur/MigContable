import pandas as pd
from sqlalchemy import text
from backend.app.core.database import source_engine
import logging

logger = logging.getLogger(__name__)

class DataExtractor:
    def __init__(self):
        self.engine = source_engine

    def extract_sales(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Extracts sales data from the source SQL Server database.
        Adjust the SQL query based on the actual schema of the source DB.
        """
        query = text("""
            SELECT 
                doc_date, 
                doc_number, 
                customer_id, 
                net_amount, 
                tax_amount, 
                total_amount,
                currency_code
            FROM SalesTable
            WHERE doc_date BETWEEN :start_date AND :end_date
        """)
        
        try:
            with self.engine.connect() as connection:
                df = pd.read_sql(query, connection, params={"start_date": start_date, "end_date": end_date})
                logger.info(f"Extracted {len(df)} sales records.")
                return df
        except Exception as e:
            logger.error(f"Error extracting sales: {e}")
            raise e
