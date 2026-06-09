from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone
from sqlalchemy.orm import Session
from backend.app.core.database import DestSessionLocal
import urllib.request
import json
from datetime import datetime
from pydantic import BaseModel

scheduler = BackgroundScheduler(timezone=timezone('America/Lima'))

def execute_scheduled_task(task_id: int):
    from backend.app.models.models import ScheduledTask, TaskLog
    from backend.app.api.endpoints.etl import run_incremental_etl
    
    db: Session = DestSessionLocal()
    try:
        task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
        if not task:
            return

        # Registrar inicio
        log = TaskLog(task_id=task.id, status="RUNNING")
        db.add(log)
        db.commit()
        db.refresh(log)

        if task.task_type == "TC_SUNAT":
            # Descarga de TC
            try:
                import httpx
                today = datetime.now().strftime("%Y-%m-%d")
                TC_API_TOKEN = "ebf3feafb06f11f09f1d005056563c20"
                TC_API_BASE = "https://api.org.pe/v1"
                url = f"{TC_API_BASE}/tc/{today}"
                headers = {"Authorization": f"Bearer {TC_API_TOKEN}"}
                
                with httpx.Client(timeout=15) as client:
                    resp = client.get(url, headers=headers)
                    resp.raise_for_status()
                    data = resp.json()
                
                if data.get("success") and data.get("data"):
                    item = data.get("data")
                    from backend.app.models.models import TipoCambio
                    fecha = datetime.strptime(item["fecha"], "%Y-%m-%d").date()
                    existing = db.query(TipoCambio).filter(TipoCambio.fecha == fecha).first()
                    
                    if existing:
                        existing.compra = item["compra"]
                        existing.venta = item["venta"]
                        existing.source = "api.org.pe (Auto)"
                    else:
                        tc = TipoCambio(fecha=fecha, compra=item["compra"], venta=item["venta"], source="api.org.pe (Auto)")
                        db.add(tc)
                        
                    log.status = "SUCCESS"
                    log.message = f"TC sincronizado: Compra {item['compra']}, Venta {item['venta']}"
                else:
                    log.status = "ERROR"
                    log.message = data.get("message", "Error desconocido o sin datos")
            except Exception as e:
                log.status = "ERROR"
                log.message = str(e)[:250]
                
                
        elif task.task_type == "ETL_FULL":
            from backend.app.api.endpoints.etl import run_full_etl
                
            try:
                subcategories_filter = task.params.get("subcategorias", []) if task.params else []
                # Execute ETL process mimicking the frontend request body
                result = run_full_etl(
                    company_id=task.company_id,
                    body={"full_refresh": False, "clear_previous": False, "subcategorias": subcategories_filter},
                    db=db
                )
                
                # Check results for errors
                errors = []
                for step, res in result.get("resultados", {}).items():
                    if isinstance(res, dict) and res.get("status") == "ERROR":
                        errors.append(f"{step}: {res.get('message')}")
                        
                if errors:
                    log.status = "ERROR"
                    log.message = "Fallo ETL: " + " | ".join(errors)
                else:
                    res_dict = result.get("resultados", {})
                    gen_lines = res_dict.get("paso2_generar", {}).get("generated", 0)
                    mig_lines = res_dict.get("paso3_migrar", {}).get("migrated", 0)
                    log.status = "SUCCESS"
                    log.message = f"Completado. Asientos Locales: {gen_lines} generados | Migrados Final: {mig_lines}."
            except Exception as e:
                log.status = "ERROR"
                log.message = f"Error general en ETL: {str(e)}"
            
        elif task.task_type == "ETL_REALTIME":
            from backend.app.api.endpoints.etl import run_realtime_etl
            try:
                subcategories_filter = task.params.get("subcategorias", []) if task.params else []
                results = run_realtime_etl(company_id=task.company_id, db=db, subcategorias=subcategories_filter)
                errors = []
                warnings = []
                success_count = 0
                for r in results:
                    if r["status"] == "ERROR":
                        errors.append(f"{r['company_name']}: {r['message']}")
                    elif r["status"] == "WARNING":
                        warnings.append(f"{r['company_name']}: {r['message']}")
                    else:
                        success_count += 1
                
                if errors:
                    log.status = "ERROR"
                    log.message = "Fallo ETL Realtime: " + " | ".join(errors)
                elif warnings:
                    log.status = "WARNING"
                    log.message = "Advertencias en ETL Realtime: " + " | ".join(warnings)
                else:
                    log.status = "SUCCESS"
                    log.message = f"Completado para {len(results)} empresa(s). Exitosas: {success_count}."
            except Exception as e:
                log.status = "ERROR"
                log.message = f"Error general en ETL Realtime: {str(e)}"
            
        elif task.task_type == "MES_ROTATION":
            try:
                from backend.app.models.models import MapeoSubcategoria, MapeoCategoria
                # Reset asiento_inicial
                query = db.query(MapeoSubcategoria)
                if task.company_id:
                    query = query.join(MapeoCategoria).filter(MapeoCategoria.company_id == task.company_id)
                subcats = query.all()
                count = 0
                for sub in subcats:
                    sub.asiento_inicial = 1
                    sub.last_generated_control_value = None
                    count += 1
                db.commit()
                log.status = "SUCCESS"
                log.message = f"Mes rotado: {count} subcategorías reiniciadas (asiento inicial = 1)."
            except Exception as e:
                log.status = "ERROR"
                log.message = f"Error en rotación: {str(e)}"

        log.finished_at = datetime.now()
        task.last_run = datetime.now()
        db.commit()

    except Exception as e:
        print(f"Error executing task {task_id}: {e}")
    finally:
        db.close()

def start_scheduler():
    from backend.app.models.models import ScheduledTask
    db = DestSessionLocal()
    try:
        if not scheduler.running:
            scheduler.start()
            
        # Cargar tareas de la BD
        tasks = db.query(ScheduledTask).filter(ScheduledTask.is_active == True).all()
        for t in tasks:
            job_id = f"task_{t.id}"
            if scheduler.get_job(job_id):
                scheduler.remove_job(job_id)
                
            if t.schedule_type == "DAILY":
                hour, minute = map(int, t.time_str.split(':'))
                scheduler.add_job(
                    execute_scheduled_task, 'cron', 
                    hour=hour, minute=minute, 
                    id=job_id, args=[t.id]
                )
            elif t.schedule_type == "WEEKLY":
                hour, minute = map(int, t.time_str.split(':'))
                scheduler.add_job(
                    execute_scheduled_task, 'cron', 
                    day_of_week=(t.day_of_week or "mon"), 
                    hour=hour, minute=minute, 
                    id=job_id, args=[t.id]
                )
            elif t.schedule_type == "MONTHLY":
                hour, minute = map(int, t.time_str.split(':'))
                scheduler.add_job(
                    execute_scheduled_task, 'cron', 
                    day=(t.day_of_month or 1), 
                    hour=hour, minute=minute, 
                    id=job_id, args=[t.id]
                )
            elif t.schedule_type == "MINUTES":
                try:
                    minutes = int(t.time_str)
                except ValueError:
                    minutes = 5
                scheduler.add_job(
                    execute_scheduled_task, 'interval',
                    minutes=minutes,
                    id=job_id, args=[t.id]
                )
    except Exception as e:
        print("Scheduler startup error:", e)
    finally:
        db.close()
