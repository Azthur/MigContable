import sys
import os
import pandas as pd
from pprint import pprint

sys.path.append('c:/SistemaMigConta')
from backend.app.core.database import DestSessionLocal
from backend.app.models.models import TableSelection, ComputedColumnRule
from backend.app.api.endpoints.etl import run_incremental_etl

db = DestSessionLocal()

sel = db.query(TableSelection).filter(TableSelection.table_name.ilike('ccbrrdoc')).first()
if sel:
    print(f"Running ETL for table_selection {sel.id} - {sel.table_name}")
    # Force full_refresh=True to make sure we extract something and re-run all rules
    res = run_incremental_etl(company_id=sel.company_id, table_selection_id=sel.id, db=db, full_refresh=True)
    if res.get("extracted_rows"):
        df = pd.DataFrame(res["extracted_rows"])
        # print fchdoc and C_fechaEmision for the first 5 rows
        cols_to_print = [c for c in ['fchdoc', 'C_fechaEmision', 'C_coddoc', 'coddoc', 'C_estado1', 'c_estado', 'C_CAR'] if c in df.columns]
        if cols_to_print:
            print(df[cols_to_print].head(10))
        else:
            print("Columns not found. Available columns:")
            print(df.columns.tolist())
    else:
        print("No rows extracted or error:")
        print(res)
else:
    print("Table selection ccbrrdoc not found.")
