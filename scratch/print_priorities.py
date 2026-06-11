import sys
sys.path.append('c:/SistemaMigConta')
from backend.app.core.database import DestSessionLocal
from backend.app.models.models import TableSelection, ComputedColumnRule

db = DestSessionLocal()

sel = db.query(TableSelection).filter(TableSelection.table_name.ilike('ccbrrdoc')).first()
if sel:
    rules = db.query(ComputedColumnRule).filter(ComputedColumnRule.table_selection_id == sel.id, ComputedColumnRule.is_active == True).order_by(ComputedColumnRule.priority).all()
    for r in rules:
        print(f'{r.priority}: {r.new_column_name} = {r.condition_value}')
else:
    print("Table selection ccbrrdoc not found.")
