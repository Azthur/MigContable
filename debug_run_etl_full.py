import sys, os
sys.path.append(os.getcwd())
from backend.app.core.database import dest_engine, DestSessionLocal
from backend.app.api.endpoints.etl import run_incremental_etl
from backend.app.models.models import TableSelection

db = DestSessionLocal()
sel = db.query(TableSelection).filter(TableSelection.table_name == 'VtaRItem', TableSelection.company_id == 4).first()
if sel:
    print("Running...")
    res = run_incremental_etl(company_id=4, table_selection_id=sel.id, db=db, full_refresh=False)
    print(f"Result returned: {res}")
