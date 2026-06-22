from backend.app.core.database import DestSessionLocal
from backend.app.models.models import EtlPipelineConfig

db = DestSessionLocal()
try:
    pipelines = db.query(EtlPipelineConfig).all()
    print(f"Total pipelines in database: {len(pipelines)}")
    for p in pipelines:
        print(f"ID: {p.id} | Name: {p.nombre}")
        print(f"  Active: {p.is_active} | Schedule: {p.schedule_type} ({p.schedule_value})")
        print(f"  Last Run: {p.last_run_at} | Created At: {p.created_at}")
        print(f"  Last Status: {p.last_status} | Run Count: {p.run_count}")
        print("-" * 50)
finally:
    db.close()
