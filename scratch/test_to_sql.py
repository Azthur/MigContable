import sys
sys.path.append('c:/SistemaMigConta')
from backend.app.core.database import DestSessionLocal
from backend.app.services.connection_manager import ConnectionManager
from backend.app.models.models import SourceConnection, TableSelection, ComputedColumnRule
from backend.app.api.endpoints.etl import __apply_computed_rules
import pandas as pd
from sqlalchemy import text

db = DestSessionLocal()
company_id = 1
sel = db.query(TableSelection).filter(TableSelection.company_id == company_id, TableSelection.table_name == 'CcbRRdoc').first()
source_conn = db.query(SourceConnection).filter(SourceConnection.company_id == company_id).first()

src_data = {
    "host": source_conn.host, "port": source_conn.port,
    "database_name": source_conn.database_name,
    "username": source_conn.username, "password": source_conn.password,
    "driver": source_conn.driver, "db_type": source_conn.db_type
}
src_engine = ConnectionManager.get_source_engine(src_data)

computed_rules = db.query(ComputedColumnRule).filter(
    ComputedColumnRule.table_selection_id == sel.id,
    ComputedColumnRule.is_active == True
).order_by(ComputedColumnRule.priority).all()

query = "SELECT TOP 1 * FROM [dbo].[CcbRRdoc] WHERE CodDoc = 'N/A' AND NroDoc LIKE '%B050000015%'"
with src_engine.connect() as conn:
    df = pd.read_sql(query, conn)

__apply_computed_rules(df, computed_rules, db, company_id, 'CcbRRdoc')

print("--- Data Types ---")
c_car_col = next((c for c in df.columns if c.lower() == 'c_car'), 'C_car')
fchdoc_col = next((c for c in df.columns if c.lower() == 'fchdoc'), 'fchdoc')
c_fechaemision_col = next((c for c in df.columns if c.lower() == 'c_fechaemision'), 'C_fechaEmision')

print(df[[c_car_col, fchdoc_col, c_fechaemision_col]].dtypes)

print("Saving to temp_test_table...")
df[[c_car_col, fchdoc_col, c_fechaemision_col]].to_sql('temp_test_table', db.bind, if_exists='replace', index=False)

print("Querying from temp_test_table...")
with db.bind.connect() as conn:
    res = conn.execute(text('SELECT * FROM temp_test_table'))
    print(res.fetchall())
