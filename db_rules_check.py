import sys
sys.path.insert(0, r"c:\SistemaMigConta")
from backend.app.core.database import dest_engine
from backend.app.models.models import ComputedColumnRule
from sqlalchemy.orm import sessionmaker

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=dest_engine)
db = SessionLocal()
rules = db.query(ComputedColumnRule).order_by(ComputedColumnRule.id.desc()).limit(10).all()

for r in rules:
    print(f"ID={r.id}")
    print(f"ColName={repr(r.new_column_name)}")
    print(f"Cond={repr(r.condition_value)}")
    print(f"Res={repr(r.result_value)}")
    print(f"Added={r.created_at}")
    print("-----")
