import os
import sys
# Add parent dir to PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.core.database import DestSessionLocal
from backend.app.api.endpoints.etl import run_incremental_etl, TableSelection

db = DestSessionLocal()
try:
    sel = db.query(TableSelection).filter(
        TableSelection.company_id == 1,
        TableSelection.table_name.ilike('ccbrrdoc')
    ).first()
    
    if not sel:
        print("TableSelection for ccbrrdoc not found")
        sys.exit(1)
        
    print(f"Triggering run_incremental_etl for company 1 table selection ID {sel.id} (ccbrrdoc)...")
    res = run_incremental_etl(company_id=1, table_selection_id=sel.id, db=db, full_refresh=False)
    print("Result of run_incremental_etl:", res)
finally:
    db.close()
