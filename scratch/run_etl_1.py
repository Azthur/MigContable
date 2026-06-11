import sys
sys.path.append('c:/SistemaMigConta')
from backend.app.core.database import DestSessionLocal
from backend.app.api.endpoints.etl import run_incremental_etl

db = DestSessionLocal()

# sel_id for ccbrrdoc in company 1
from backend.app.models.models import TableSelection
sel = db.query(TableSelection).filter(TableSelection.company_id == 1, TableSelection.table_name == 'CcbRRdoc').first()

if sel:
    print(f"Running ETL for selection {sel.id}...")
    run_incremental_etl(company_id=1, table_selection_id=sel.id, db=db, full_refresh=True)
    print("ETL finished.")
else:
    print("Selection not found.")
