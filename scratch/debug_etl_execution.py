import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from backend.app.core.config import get_settings
from backend.app.api.endpoints.etl import run_incremental_etl, __apply_computed_rules
from backend.app.models.models import TableSelection, ComputedColumnRule

settings = get_settings()
engine = create_engine(settings.POSTGRES_CONNECTION_STRING)
db = Session(bind=engine)

company_id = 1
table_name = "CcbRRdoc"

# Find table selection id
sel = db.query(TableSelection).filter(
    TableSelection.company_id == company_id,
    TableSelection.table_name.ilike(table_name)
).first()

print(f"Running run_incremental_etl for TableSelection ID={sel.id}...")

# Run incremental ETL (full_refresh=True to force fresh extraction and insertion)
res = run_incremental_etl(company_id, sel.id, db, full_refresh=True)
print("ETL Result:", res)

# Query the row back from DB to see if it was saved
query = 'SELECT "company_id", "CodDoc", "NroDoc", "fchdoc", "C_fechaNC", "C_fechaEmision", "C_fechaNC_Contasis" FROM "ccbrrdoc" WHERE "company_id" = 1 AND "NroDoc" = \'B050000015\''
df_res = pd.read_sql(query, engine)
print("\nccbrrdoc row from DB after ETL:")
print(df_res)
