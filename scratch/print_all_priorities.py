from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from backend.app.core.config import get_settings
from backend.app.models.models import TableSelection, ComputedColumnRule

settings = get_settings()
engine = create_engine(settings.POSTGRES_CONNECTION_STRING)
db = Session(bind=engine)

sel = db.query(TableSelection).filter(
    TableSelection.company_id == 1,
    TableSelection.table_name.ilike('ccbrrdoc')
).first()

if sel:
    rules = db.query(ComputedColumnRule).filter(
        ComputedColumnRule.table_selection_id == sel.id
    ).order_by(ComputedColumnRule.priority).all()
    for r in rules[:10]:
        print(f"Priority: {r.priority:03d} | Col: {r.new_column_name} | Cond: {r.condition_value}")
else:
    print("Not found")
