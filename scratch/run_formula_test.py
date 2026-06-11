import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from backend.app.core.config import get_settings
from backend.app.api.endpoints.etl import __apply_computed_rules
from backend.app.models.models import TableSelection, ComputedColumnRule

settings = get_settings()
engine = create_engine(settings.POSTGRES_CONNECTION_STRING)
db = Session(bind=engine)

# Get TableSelection
sel = db.query(TableSelection).filter(
    TableSelection.company_id == 1,
    TableSelection.table_name.ilike('ccbrrdoc')
).first()

rules = db.query(ComputedColumnRule).filter(
    ComputedColumnRule.table_selection_id == sel.id
).order_by(ComputedColumnRule.priority).all()

# Let's load the raw extracted df from PostgreSQL (simulating df_pending)
# We select rows where C_car = 'N/AM010003564'
query = 'SELECT * FROM "ccbrrdoc" WHERE "company_id" = 1 AND "C_car" = \'N/AM010003564\' LIMIT 2'
df = pd.read_sql(query, engine)

print("Before running rules:")
print(df[["C_car", "fchdoc", "C_fechaEmision", "C_fechaNC", "C_fechaNC_Contasis"]])

# Let's run __apply_computed_rules
__apply_computed_rules(df, rules, db, 1, "ccbrrdoc", db_engine=engine)

print("\nAfter running rules:")
print(df[["C_car", "fchdoc", "C_fechaEmision", "C_fechaNC", "C_fechaNC_Contasis"]])
