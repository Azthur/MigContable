import os
import sys

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import DestSessionLocal
from backend.app.models.models import ScheduledTask, EtlPipelineConfig, Company, MapeoSubcategoria

db = DestSessionLocal()
try:
    tasks = db.query(ScheduledTask).filter(ScheduledTask.task_type.in_(["ETL_REALTIME", "ETL_FULL"])).all()
    print(f"Encontradas {len(tasks)} tareas legadas para migrar.")
    
    migrated_count = 0
    for t in tasks:
        # Extract subcategory
        subcat_id = None
        if t.params and "subcategorias" in t.params:
            subs = t.params["subcategorias"]
            if subs:
                subcat_id = subs[0]
                
        if not subcat_id:
            print(f"Omitiendo tarea {t.id}: No tiene subcategoría en params.")
            continue
            
        # Check if already exists in etl_pipeline_config
        existing = db.query(EtlPipelineConfig).filter(
            EtlPipelineConfig.empresa_id == t.company_id,
            EtlPipelineConfig.subcategoria_id == subcat_id
        ).first()
        
        if existing:
            print(f"Omitiendo tarea {t.id}: Ya existe pipeline para empresa {t.company_id} subcategoría {subcat_id}.")
            continue
            
        comp = db.query(Company).filter(Company.id == t.company_id).first()
        sub = db.query(MapeoSubcategoria).filter(MapeoSubcategoria.id == subcat_id).first()
        nombre = f"{(sub.nombre if sub else '?')} - {(comp.name if comp else '?')}"
        
        pipeline = EtlPipelineConfig(
            empresa_id=t.company_id,
            subcategoria_id=subcat_id,
            nombre=nombre,
            is_active=t.is_active,
            schedule_type=t.schedule_type,
            schedule_value=t.time_str,
            day_of_week=t.day_of_week,
            day_of_month=t.day_of_month,
            run_extraction=True,
            run_generation=True,
            run_migration=True,
            params=t.params or {},
            priority=5,
            max_retries=3,
            retry_backoff=30
        )
        db.add(pipeline)
        migrated_count += 1
        
    db.commit()
    print(f"Migradas exitosamente {migrated_count} tareas a etl_pipeline_config.")
except Exception as e:
    db.rollback()
    print("Error al migrar tareas:", e)
finally:
    db.close()
