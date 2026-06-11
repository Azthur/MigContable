from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from backend.app.core.config import get_settings
from backend.app.models.models import TableSelection, ComputedColumnRule

settings = get_settings()
engine = create_engine(settings.POSTGRES_CONNECTION_STRING)
db = Session(bind=engine)

# Find the TableSelection for ccbrrdoc and company_id = 1
sel = db.query(TableSelection).filter(
    TableSelection.company_id == 1,
    TableSelection.table_name.ilike('ccbrrdoc')
).first()

if sel:
    print(f"Found TableSelection: ID={sel.id}, Table={sel.table_name}")
    rules = db.query(ComputedColumnRule).filter(
        ComputedColumnRule.table_selection_id == sel.id
    ).order_by(ComputedColumnRule.priority).all()
    print(f"Total rules: {len(rules)}")
    for r in rules:
        print(f"Priority: {r.priority:03d} | Col: {r.new_column_name} | Source: {r.source_column} | Cond: {r.condition_value} | Result: {r.result_value} | Default: {r.default_value}")
else:
    print("TableSelection not found for ccbrrdoc and company_id = 1")
