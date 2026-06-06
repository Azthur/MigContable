import sys
sys.path.append("c:\\SistemaMigConta")
from backend.app.core.database import DestSessionLocal
from backend.app.models.models import ComputedColumnRule

db = DestSessionLocal()
try:
    rules = db.query(ComputedColumnRule).filter(ComputedColumnRule.table_selection_id == 17).order_by(ComputedColumnRule.id.desc()).limit(10).all()
    for r in rules:
        print(f"ID: {r.id}, Col: {r.new_column_name}, Source: {r.source_column}, Cond: {r.condition_value}, Result: {r.result_value}")
finally:
    db.close()
