import sys
sys.path.append('c:/SistemaMigConta')
from backend.app.core.database import DestSessionLocal
from backend.app.models.models import ScheduledTask
import json

db = DestSessionLocal()
try:
    tasks = db.query(ScheduledTask).all()
    print("=== Scheduled Tasks in DB ===")
    for t in tasks:
        print(f"ID: {t.id}, Company ID: {t.company_id}, Type: {t.task_type}, Schedule: {t.schedule_type}, Time: {t.time_str}, Active: {t.is_active}")
finally:
    db.close()
