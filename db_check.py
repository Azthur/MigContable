import sys
import os
sys.path.insert(0, r"c:\SistemaMigConta")
from backend.app.core.database import DestSessionLocal
from backend.app.models.models import ComputedColumnRule

db = DestSessionLocal()
rules = db.query(ComputedColumnRule).order_by(ComputedColumnRule.id.desc()).limit(1).all()
for r in rules:
    print(f"ID={r.id}")
    print(f"ColName={repr(r.new_column_name)}")
    print(f"Cond={repr(r.condition_value)}")
    print(f"Res={repr(r.result_value)}")
