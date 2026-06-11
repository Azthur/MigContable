import os
import sys
# Add parent dir to PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.core.database import DestSessionLocal
from backend.app.models.models import ComputedColumnRule, TableSelection

db = DestSessionLocal()
try:
    rules = db.query(ComputedColumnRule).join(
        TableSelection, TableSelection.id == ComputedColumnRule.table_selection_id
    ).filter(
        TableSelection.table_name.ilike('ccbrrdoc')
    ).order_by(ComputedColumnRule.priority).all()

    print(f"Found {len(rules)} rules for ccbrrdoc:")
    for r in rules:
        print(f"ID: {r.id}, Col: {r.new_column_name}, Priority: {r.priority}, Active: {r.is_active}, SrcCol: {r.source_column}, CondVal: {r.condition_value}, ResVal: {r.result_value}")
finally:
    db.close()
