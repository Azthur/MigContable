import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from backend.app.core.config import get_settings
from backend.app.api.endpoints.etl import __apply_computed_rules, build_where_clause
from backend.app.models.models import TableSelection, ComputedColumnRule, SourceConnection
from backend.app.services.connection_manager import ConnectionManager

settings = get_settings()
engine = create_engine(settings.POSTGRES_CONNECTION_STRING)
db = Session(bind=engine)

company_id = 1
table_name = "CcbRRdoc"

# Get source connection details
conn = db.query(SourceConnection).filter(SourceConnection.company_id == company_id).first()
conn_data = {
    "host": conn.host, "port": conn.port, "database_name": conn.database_name,
    "username": conn.username, "password": conn.password,
    "driver": conn.driver, "db_type": conn.db_type
}

# Fetch the specific row from SQL Server source
# Let's query using NroDoc = 'B050000015' and CodDoc = 'N/A'
src_engine = ConnectionManager.get_source_engine(conn_data)
query = "SELECT * FROM CcbRRdoc WHERE CodDoc = 'N/A' AND NroDoc = 'B050000015'"
with src_engine.connect() as s_conn:
    df = pd.read_sql(query, s_conn)

print("Fetched df shape from SQL Server:", df.shape)
print("Source columns:", list(df.columns))

# Load computed rules
sel = db.query(TableSelection).filter(
    TableSelection.company_id == company_id,
    TableSelection.table_name.ilike(table_name)
).first()

rules = db.query(ComputedColumnRule).filter(
    ComputedColumnRule.table_selection_id == sel.id
).order_by(ComputedColumnRule.priority).all()

print(f"\nApplying {len(rules)} rules...")

# Let's run __apply_computed_rules step-by-step
df_cols_lower = {str(c).lower(): str(c) for c in df.columns}
col_defaults = {}
for rule in rules:
    r_lower = rule.new_column_name.lower()
    actual_col = df_cols_lower.get(r_lower, rule.new_column_name)
    if actual_col not in col_defaults:
        col_defaults[actual_col] = rule.default_value if rule.default_value else ""
        
for col, default in col_defaults.items():
    df[col] = default

for rule in rules:
    r_lower = rule.new_column_name.lower()
    new_col = df_cols_lower.get(r_lower, rule.new_column_name)
    default = col_defaults.get(new_col, "")
    
    # Run single rule
    from backend.app.core.formula_parser import evaluate_formula_on_df
    try:
        if rule.condition_value.strip().upper() in ("BUSCARX_TC_VENTA", "BUSCARX_TC_COMPRA"):
            # Skip for dates
            pass
        else:
            df[new_col] = evaluate_formula_on_df(
                df=df, formula_str=rule.condition_value,
                db=db, company_id=company_id, default=default if default else "",
                db_engine=engine
            )
            # Log specific columns
            if new_col in ("C_car", "fchdoc", "C_fechaNC", "C_fechaEmision", "C_fechaNC_Contasis", "C_moneda", "codref1"):
                print(f"Rule: {rule.priority:02d} | Col: {new_col:18s} | Val: {df[new_col].iloc[0]} | Formula: {rule.condition_value}")
    except Exception as e:
        print(f"Error in rule {rule.new_column_name}: {e}")
