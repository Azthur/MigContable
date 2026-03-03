import sys
sys.path.insert(0, r"c:\SistemaMigConta")
from backend.app.core.database import dest_engine
from backend.app.models.models import TableSelection, ComputedColumnRule
from sqlalchemy.orm import sessionmaker

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=dest_engine)
db = SessionLocal()
rule = db.query(ComputedColumnRule).filter(ComputedColumnRule.new_column_name == 'c_Seriedoc').first()
if rule:
    sel = db.query(TableSelection).filter(TableSelection.id == rule.table_selection_id).first()
    print(f"Table dest: {sel.table_name}")
else:
    print("Rule not found")
