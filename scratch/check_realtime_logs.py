import sys
sys.path.append('c:/SistemaMigConta')
from backend.app.core.database import DestSessionLocal
from backend.app.models.models import EtlRealtimeLog

db = DestSessionLocal()
try:
    logs = db.query(EtlRealtimeLog).filter(EtlRealtimeLog.company_id == 1).order_by(EtlRealtimeLog.run_date.desc()).limit(20).all()
    print("Latest 20 Realtime Logs for Company 1:")
    for l in logs:
        print(f"Date: {l.run_date}, Status: {l.status}, Message: {l.message}")
        if l.errors:
            print("Errors:")
            for err in l.errors[:5]:
                print(f"  - Step: {err.get('step')}, Table: {err.get('table')}, Reference: {err.get('reference')}, Error: {err.get('error')}")
        print("-" * 50)
finally:
    db.close()
