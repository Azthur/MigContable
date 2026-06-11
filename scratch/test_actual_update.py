import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from backend.app.core.config import get_settings
from backend.app.api.endpoints.etl import __apply_computed_rules
from backend.app.models.models import TableSelection, ComputedColumnRule

settings = get_settings()
engine = create_engine(settings.POSTGRES_CONNECTION_STRING)
db = Session(bind=engine)

table_dest_name = "ccbrrdoc"
company_id = 1

# Load df_pending
where_clause = "company_id = :cid"
query_pend = text(f'SELECT * FROM "{table_dest_name}" WHERE {where_clause}')
with engine.connect() as conn:
    df_pending = pd.read_sql(query_pend, conn, params={"cid": company_id})

print(f"Loaded df_pending. Rows: {len(df_pending)}")

# Load rules
sel = db.query(TableSelection).filter(
    TableSelection.company_id == company_id,
    TableSelection.table_name.ilike('ccbrrdoc')
).first()
rules = db.query(ComputedColumnRule).filter(
    ComputedColumnRule.table_selection_id == sel.id
).order_by(ComputedColumnRule.priority).all()

# Apply rules
__apply_computed_rules(df_pending, rules, db, company_id, "ccbrrdoc", db_engine=engine)

# Get columns to update
update_cols = []
df_cols_lower_pending = {str(c).lower(): str(c) for c in df_pending.columns}
for r in rules:
    r_lower = r.new_column_name.lower()
    if r_lower in df_cols_lower_pending:
        actual_col_name = df_cols_lower_pending[r_lower]
        if actual_col_name not in update_cols:
            update_cols.append(actual_col_name)

print(f"Columns to update: {update_cols}")

# Coerce types (simulating etl.py)
insp = engine.dialect.inspector(engine)
col_info_list = insp.get_columns(table_dest_name)
dest_type_map = {c['name']: str(c['type']).upper() for c in col_info_list}

for col in update_cols:
    col_type = dest_type_map.get(col, 'TEXT')
    if 'INT' in col_type:
        df_pending[col] = pd.to_numeric(df_pending[col], errors='coerce')
        try: df_pending[col] = df_pending[col].astype('Int64')
        except: pass
    elif any(t in col_type for t in ['DOUBLE', 'FLOAT', 'NUMERIC', 'REAL', 'DECIMAL']):
        df_pending[col] = pd.to_numeric(df_pending[col], errors='coerce')
    elif 'TIMESTAMP' in col_type or 'DATE' in col_type:
        df_pending[col] = pd.to_datetime(df_pending[col], errors='coerce')
    else:
        if df_pending[col].dtype == 'object':
            df_pending[col] = df_pending[col].apply(
                lambda x: None if pd.isna(x) or str(x).strip() in ['', 'nan', 'None', '<NA>'] else x
            )

# Check a sample before updating
matching_rows = df_pending[df_pending["C_car"] == "N/AM010003564"]
print("\nSample row in df_pending before saving:")
print(matching_rows[["_migration_id", "C_car", "fchdoc", "C_fechaEmision"]])

# Save to temp table
temp_table = f"temp_update_test_{company_id}"
df_pending.to_sql(temp_table, engine, if_exists="replace", index=False)

# Let's perform UPDATE
match_col = "_migration_id"
set_parts = [f'"{c}" = temp."{c}"' for c in update_cols] # all TEXT anyway
set_clause = ", ".join(set_parts)

update_sql = f"""
    UPDATE "{table_dest_name}" t
    SET {set_clause}
    FROM "{temp_table}" temp
    WHERE t."{match_col}" = temp."{match_col}"
"""

with engine.begin() as conn:
    result = conn.execute(text(update_sql))
    print(f"\nPostgreSQL UPDATE command matched & updated {result.rowcount} rows!")
    conn.execute(text(f'DROP TABLE "{temp_table}"'))
