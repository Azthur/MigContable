import sys
sys.path.append('c:/SistemaMigConta')
from backend.app.core.database import DestSessionLocal, dest_engine
from backend.app.models.models import TableSelection, ComputedColumnRule
from backend.app.api.endpoints.etl import __apply_computed_rules
import pandas as pd
from sqlalchemy import text

db = DestSessionLocal()
company_id = 1

sel = db.query(TableSelection).filter(TableSelection.company_id == company_id, TableSelection.table_name == 'CcbRRdoc').first()

computed_rules = db.query(ComputedColumnRule).filter(
    ComputedColumnRule.table_selection_id == sel.id,
    ComputedColumnRule.is_active == True
).order_by(ComputedColumnRule.priority).all()

df = pd.DataFrame({'coddoc': ['N/A'], 'nrodoc': ['B050000015']})

print("--- Original DataFrame ---")
print(df[['coddoc', 'nrodoc']])

__apply_computed_rules(df, computed_rules, db, company_id, 'CcbRRdoc')

print("--- After Rules ---")
print(df[['C_car', 'fchdoc', 'C_fechaEmision']])
