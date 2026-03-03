import pandas as pd
from typing import List, Dict
from sqlalchemy.orm import Session
from backend.app.models.models import AccountMapping, TransformationRule

class DataTransformer:
    def __init__(self, db: Session):
        self.db = db
        self.account_mappings = self._load_account_mappings()

    def _load_account_mappings(self) -> Dict[str, str]:
        mappings = self.db.query(AccountMapping).filter(AccountMapping.is_active == True).all()
        return {m.source_account_code: m.dest_account_code for m in mappings}

    def transform_sales_to_entries(self, sales_df: pd.DataFrame) -> List[Dict]:
        """
        Transforms sales DataFrame into a list of accounting entry dictionaries.
        This is a simplified example. Real logic will depend on specific accounting rules.
        """
        entries = []
        for _, row in sales_df.iterrows():
            # Example logic: Credit Sales Account, Debit AR Account
            
            # Debit Entry (Accounts Receivable)
            entries.append({
                "date": row['doc_date'],
                "account": "110505", # Example AR account, should come from config
                "debit": row['total_amount'],
                "credit": 0,
                "description": f"Sale {row['doc_number']}",
                "doc_ref": row['doc_number']
            })
            
            # Credit Entry (Sales Income)
            entries.append({
                "date": row['doc_date'],
                "account": "413505", # Example Income account
                "debit": 0,
                "credit": row['net_amount'],
                "description": f"Sale {row['doc_number']}",
                "doc_ref": row['doc_number']
            })
            
            # Credit Entry (Tax)
            if row['tax_amount'] > 0:
                 entries.append({
                    "date": row['doc_date'],
                    "account": "240801", # Example VAT account
                    "debit": 0,
                    "credit": row['tax_amount'],
                    "description": f"VAT {row['doc_number']}",
                    "doc_ref": row['doc_number']
                })
                
        return entries
