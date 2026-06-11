from backend.app.core.database import DestSessionLocal
from backend.app.models.models import ComputedColumnRule, TableSelection

db = DestSessionLocal()
try:
    sel = db.query(TableSelection).filter(TableSelection.table_name == 'CcbRRdoc', TableSelection.company_id == 1).first()
    if not sel:
         print("TableSelection CcbRRdoc not found")
         sys.exit(1)
         
    print(f"TableSelection: ID={sel.id}, TableName={sel.table_name}")
    rules = db.query(ComputedColumnRule).filter(
        ComputedColumnRule.table_selection_id == sel.id
    ).order_by(ComputedColumnRule.priority).all()
    
    print("\nRules order in DB:")
    for r in rules:
         print(f"Priority={r.priority:03d} | Active={r.is_active} | Col={r.new_column_name} | formula={r.condition_value} | Src={r.source_column}")
finally:
    db.close()
