"""
Worker genérico ETL.
Recibe (pipeline_id) → carga config de DB → ejecuta 3 etapas.
No conoce detalles de subcategorías — todo viene de la config.
"""
from celery import Task
from backend.app.celery_app import celery
from backend.app.celery_tasks import company_semaphore
from backend.app.core.database import DestSessionLocal
from datetime import datetime, timezone
import traceback


class ETLTask(Task):
    """Clase base con hooks de lifecycle."""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Se ejecuta cuando la tarea falla definitivamente (sin más retries)."""
        pipeline_id = args[0] if args else kwargs.get("pipeline_id")
        db = DestSessionLocal()
        try:
            from backend.app.models.models import EtlEjecucion, EtlPipelineConfig
            ejecucion = db.query(EtlEjecucion).filter(
                EtlEjecucion.celery_task_id == task_id
            ).first()
            if ejecucion:
                ejecucion.status = "ERROR"
                ejecucion.error_message = str(exc)[:2000]
                ejecucion.error_traceback = str(einfo)[:5000]
                ejecucion.finished_at = datetime.now(timezone.utc)
                if ejecucion.started_at:
                    ejecucion.duration_s = (
                        datetime.now(timezone.utc) - ejecucion.started_at
                    ).total_seconds()
            
            config = db.query(EtlPipelineConfig).filter(
                EtlPipelineConfig.id == pipeline_id
            ).first()
            if config:
                config.last_status = "ERROR"
                config.last_error = str(exc)[:2000]
                config.error_count = (config.error_count or 0) + 1
                
            db.commit()
        except Exception:
            db.rollback()
        finally:
            # Liberar semáforo
            if pipeline_id:
                try:
                    cfg = db.query(EtlPipelineConfig).get(pipeline_id)
                    if cfg:
                        company_semaphore.release(cfg.empresa_id, task_id)
                except Exception:
                    pass
            db.close()


@celery.task(
    bind=True,
    base=ETLTask,
    name="backend.app.celery_tasks.etl_worker.run_etl_pipeline",
    max_retries=3,
    default_retry_delay=30,
    acks_late=True,
    reject_on_worker_lost=True,
    time_limit=1800,       # 30 min hard limit
    soft_time_limit=1500,  # 25 min soft limit (raises SoftTimeLimitExceeded)
)
def run_etl_pipeline(self, pipeline_id: int):
    """
    Worker genérico: recibe pipeline_id, carga todo de DB, ejecuta.
    
    Flujo:
    1. Cargar config de etl_pipeline_config
    2. Adquirir semáforo de empresa (máx 4 concurrentes)
    3. Crear registro en etl_ejecuciones
    4. Ejecutar etapas (extracción → generación → migración)
    5. Actualizar log + liberar semáforo
    """
    db = DestSessionLocal()
    ejecucion = None
    config = None
    empresa_id = None
    
    try:
        from backend.app.models.models import EtlPipelineConfig, EtlEjecucion
        
        # ─── 1. Cargar configuración ───
        config = db.query(EtlPipelineConfig).filter(
            EtlPipelineConfig.id == pipeline_id
        ).first()
        
        if not config:
            raise ValueError(f"Pipeline {pipeline_id} no encontrado en DB")
        
        if not config.is_active:
            return {"status": "SKIPPED", "reason": "Pipeline inactivo"}
        
        empresa_id = config.empresa_id
        subcategoria_id = config.subcategoria_id
        
        # ─── 2. Adquirir semáforo (máx 4 por empresa) ───
        if not company_semaphore.acquire(empresa_id, self.request.id):
            # Empresa saturada → retry con delay
            raise self.retry(
                exc=Exception(
                    f"Empresa {empresa_id} tiene {company_semaphore.active_count(empresa_id)} "
                    f"workers activos (máx {company_semaphore.DEFAULT_MAX}). Reintentando..."
                ),
                countdown=15,
                max_retries=10,  # Más retries para saturación (no es error real)
            )
        
        # ─── 3. Crear o recuperar registro de ejecución ───
        # Si es un reintento, reutilizamos el registro existente para evitar UniqueViolation
        ejecucion = db.query(EtlEjecucion).filter(
            EtlEjecucion.celery_task_id == self.request.id
        ).first()
        
        if ejecucion:
            ejecucion.status = "RUNNING"
            ejecucion.started_at = datetime.now(timezone.utc)
            ejecucion.finished_at = None
            ejecucion.duration_s = None
            ejecucion.error_message = None
            ejecucion.error_traceback = None
            ejecucion.retry_count = self.request.retries
        else:
            ejecucion = EtlEjecucion(
                pipeline_id=pipeline_id,
                empresa_id=empresa_id,
                subcategoria_id=subcategoria_id,
                celery_task_id=self.request.id,
                status="RUNNING",
                started_at=datetime.now(timezone.utc),
                retry_count=self.request.retries,
            )
            db.add(ejecucion)
            
        config.last_run_at = datetime.now(timezone.utc)
        config.last_status = "RUNNING"
        db.commit()
        db.refresh(ejecucion)
        
        # ─── 4. Ejecutar pipeline (3 etapas) ───
        results = _execute_pipeline(config, ejecucion, db)
        
        # ─── 5. Marcar éxito o advertencia ───
        has_validation_errors = False
        for d in results.get("details", []):
            if isinstance(d, dict):
                if d.get("step") == "GENERATION" and d.get("errors"):
                    has_validation_errors = True
                if d.get("step") == "MIGRATION" and d.get("status") == "WARNING":
                    has_validation_errors = True

        status_flag = "WARNING" if has_validation_errors else "SUCCESS"

        ejecucion.status = status_flag
        ejecucion.finished_at = datetime.now(timezone.utc)
        ejecucion.duration_s = (
            ejecucion.finished_at - ejecucion.started_at
        ).total_seconds()
        ejecucion.records_extracted = results.get("extracted", 0)
        ejecucion.records_generated = results.get("generated", 0)
        ejecucion.records_migrated = results.get("migrated", 0)
        ejecucion.details = results.get("details", [])
        
        config.last_status = status_flag
        config.last_duration_s = ejecucion.duration_s
        config.last_error = None
        config.run_count = (config.run_count or 0) + 1
        
        db.commit()
        
        return {
            "status": status_flag,
            "pipeline_id": pipeline_id,
            "empresa_id": empresa_id,
            "subcategoria_id": subcategoria_id,
            "extracted": results.get("extracted", 0),
            "generated": results.get("generated", 0),
            "migrated": results.get("migrated", 0),
            "duration_s": float(ejecucion.duration_s or 0),
        }
        
    except self.MaxRetriesExceededError:
        raise  # Deja que on_failure maneje esto
        
    except Exception as exc:
        # Extract retry configuration before closing the session to prevent DetachedInstanceError
        retry_backoff = 30
        max_retries = 3
        if config:
            try:
                retry_backoff = config.retry_backoff or 30
                max_retries = config.max_retries or 3
            except Exception:
                pass

        # Close the broken session
        try:
            db.close()
        except Exception:
            pass
            
        # Create a fresh new session to log the error
        db_log = DestSessionLocal()
        try:
            from backend.app.models.models import EtlPipelineConfig, EtlEjecucion
            # Reload config and execution using the new session
            config_log = db_log.query(EtlPipelineConfig).get(pipeline_id)
            ejecucion_log = db_log.query(EtlEjecucion).filter(
                EtlEjecucion.celery_task_id == self.request.id
            ).first()
            
            if ejecucion_log:
                ejecucion_log.status = "ERROR"
                ejecucion_log.error_message = str(exc)[:2000]
                ejecucion_log.error_traceback = traceback.format_exc()[:5000]
                ejecucion_log.finished_at = datetime.now(timezone.utc)
                if ejecucion_log.started_at:
                    ejecucion_log.duration_s = (
                        datetime.now(timezone.utc) - ejecucion_log.started_at
                    ).total_seconds()
            
            if config_log:
                config_log.last_status = "ERROR"
                config_log.last_error = str(exc)[:2000]
                config_log.error_count = (config_log.error_count or 0) + 1
                
            db_log.commit()
        except Exception as e_inner:
            print("Error writing error log:", e_inner)
            db_log.rollback()
        finally:
            db_log.close()
        
        # Retry con backoff exponencial: 30s, 120s, 300s
        raise self.retry(
            exc=Exception(str(exc)),
            countdown=retry_backoff * (2 ** self.request.retries),
            max_retries=max_retries,
        )
    finally:
        # Liberar semáforo SIEMPRE
        if empresa_id is not None:
            company_semaphore.release(empresa_id, self.request.id)
        try:
            db.close()
        except Exception:
            pass


def _execute_pipeline(config, ejecucion, db):
    """
    Ejecuta las 3 etapas del ETL usando la lógica existente.
    No reimplementa nada — reutiliza run_incremental_etl, generate_to_cf_diariol, migrate_to_final.
    """
    from backend.app.models.models import (
        MapeoSubcategoria, TableSelection, FinalDestConnection
    )
    from backend.app.api.endpoints.etl import run_incremental_etl
    from backend.app.api.endpoints.mapeo import generate_to_cf_diariol, migrate_to_final
    
    empresa_id = config.empresa_id
    subcategoria_id = config.subcategoria_id
    params = config.params or {}
    results = {"extracted": 0, "generated": 0, "migrated": 0, "details": []}
    
    sub = db.query(MapeoSubcategoria).filter(
        MapeoSubcategoria.id == subcategoria_id
    ).first()
    if not sub:
        raise ValueError(f"Subcategoría {subcategoria_id} no encontrada")
    
    # ─── Etapa 1: Extracción ───
    if config.run_extraction:
        ejecucion.step_current = "EXTRACTION"
        db.commit()
        
        selections = db.query(TableSelection).filter(
            TableSelection.company_id == empresa_id,
            TableSelection.is_selected == True
        ).order_by(TableSelection.extraction_order).all()
        
        # Solo extraer tablas que alimentan esta subcategoría
        for sel in selections:
            sel_table_dest = sel.table_name.lower().replace(" ", "_")
            if sub.tabla_origen and (
                sel.table_name.lower() in sub.tabla_origen.lower() or
                sel_table_dest in sub.tabla_origen.lower()
            ):
                etl_res = run_incremental_etl(
                    empresa_id, sel.id, db, full_refresh=params.get("full_refresh", False)
                )
                recs = etl_res.get("records", 0)
                results["extracted"] += recs
                results["details"].append({
                    "step": "EXTRACTION",
                    "table": sel.table_name,
                    "status": etl_res.get("status", "OK"),
                    "records": recs,
                })
    
    # ─── Etapa 2: Generación ───
    if config.run_generation:
        ejecucion.step_current = "GENERATION"
        ejecucion.records_extracted = results["extracted"]
        db.commit()
        
        gen_res = generate_to_cf_diariol({
            "company_id": empresa_id,
            "subcategoria_id": subcategoria_id,
            "clear_previous": True,
            "is_realtime": True,
        }, db)
        
        results["generated"] = gen_res.get("generated", 0)
        results["details"].append({
            "step": "GENERATION",
            "status": "SUCCESS",
            "generated": results["generated"],
            "lote_id": gen_res.get("lote_id"),
            "errors": gen_res.get("errors", []),
        })
    
    # ─── Etapa 3: Migración ───
    if config.run_migration:
        ejecucion.step_current = "MIGRATION"
        ejecucion.records_generated = results["generated"]
        db.commit()
        
        final_conn = db.query(FinalDestConnection).filter(
            FinalDestConnection.company_id == empresa_id,
            FinalDestConnection.is_active == True
        ).first()
        
        if final_conn:
            mig_res = migrate_to_final(
                company_id=empresa_id,
                subcategoria_id=subcategoria_id,
                allow_overwrite=False,
                db=db,
            )
            results["migrated"] = mig_res.get("migrated_lineas", 0)
            results["details"].append({
                "step": "MIGRATION",
                "status": "SUCCESS",
                "migrated": results["migrated"],
            })
        else:
            results["details"].append({
                "step": "MIGRATION",
                "status": "SKIP",
                "reason": "No hay conexión destino final configurada",
            })
    
    return results


@celery.task(name="backend.app.celery_tasks.etl_worker.run_legacy_task")
def run_legacy_task(task_id: int):
    """Ejecuta una tarea del scheduler heredado (ej: TC_SUNAT, MES_ROTATION)."""
    from backend.app.core.scheduler import execute_scheduled_task
    execute_scheduled_task(task_id)
