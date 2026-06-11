from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from backend.app.core.database import get_dest_db
from backend.app.models.models import (
    EtlPipelineConfig, EtlEjecucion, Company, MapeoSubcategoria
)

router = APIRouter()


class PipelineCreate(BaseModel):
    company_id: int
    task_type: Optional[str] = "ETL_REALTIME"
    schedule_type: str
    time_str: str
    day_of_week: Optional[str] = None
    day_of_month: Optional[int] = None
    params: Optional[dict] = None
    priority: int = 5
    max_retries: int = 3
    retry_backoff: int = 30


class PipelineUpdate(BaseModel):
    company_id: Optional[int] = None
    task_type: Optional[str] = None
    schedule_type: Optional[str] = None
    time_str: Optional[str] = None
    day_of_week: Optional[str] = None
    day_of_month: Optional[int] = None
    is_active: Optional[bool] = None
    params: Optional[dict] = None
    priority: Optional[int] = None
    max_retries: Optional[int] = None
    retry_backoff: Optional[int] = None


@router.get("")
def list_pipelines(
    company_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_dest_db),
):
    """Lista todos los pipelines configurados con formato compatible con ScheduledTask."""
    query = db.query(EtlPipelineConfig)
    if company_id:
        query = query.filter(EtlPipelineConfig.empresa_id == company_id)
    if is_active is not None:
        query = query.filter(EtlPipelineConfig.is_active == is_active)
    
    configs = query.order_by(
        EtlPipelineConfig.empresa_id, EtlPipelineConfig.nombre
    ).all()
    
    result = []
    for c in configs:
        # Get next run from Celery or a simple logic if not available
        next_run = None
        
        # Subcategory list for compatibility
        subcat_ids = [c.subcategoria_id] if c.subcategoria_id else []
        
        result.append({
            "id": c.id,
            "company_id": c.empresa_id,
            "company_name": c.empresa.name if c.empresa else "?",
            "subcategoria_nombres": c.subcategoria.nombre if c.subcategoria else "?",
            "task_type": "ETL_REALTIME",
            "schedule_type": c.schedule_type,
            "time_str": c.schedule_value,
            "day_of_week": c.day_of_week,
            "day_of_month": c.day_of_month,
            "is_active": c.is_active,
            "params": {"subcategorias": subcat_ids},
            "last_run": str(c.last_run_at) if c.last_run_at else None,
            "next_run": str(next_run) if next_run else None,
            "last_status": c.last_status,
            "last_duration_s": float(c.last_duration_s) if c.last_duration_s else None,
            "last_error": c.last_error,
            "run_count": c.run_count,
            "error_count": c.error_count,
        })
    return result


@router.post("")
def create_pipeline(body: PipelineCreate, db: Session = Depends(get_dest_db)):
    """
    Agregar un pipeline ETL.
    """
    # Extract subcategoria_id from params
    subcat_id = None
    if body.params and "subcategorias" in body.params:
        subs = body.params["subcategorias"]
        if subs:
            subcat_id = subs[0]
            
    if not subcat_id:
        raise HTTPException(status_code=400, detail="Debe seleccionar una subcategoría específica.")
        
    # Check if pipeline already exists for company + subcat
    existing = db.query(EtlPipelineConfig).filter(
        EtlPipelineConfig.empresa_id == body.company_id,
        EtlPipelineConfig.subcategoria_id == subcat_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ya existe una programación para esta empresa y subcategoría.")

    sub = db.query(MapeoSubcategoria).filter(MapeoSubcategoria.id == subcat_id).first()
    comp = db.query(Company).filter(Company.id == body.company_id).first()
    nombre = f"{(sub.nombre if sub else '?')} - {(comp.name if comp else '?')}"
    
    config = EtlPipelineConfig(
        empresa_id=body.company_id,
        subcategoria_id=subcat_id,
        nombre=nombre,
        schedule_type=body.schedule_type,
        schedule_value=body.time_str,
        day_of_week=body.day_of_week,
        day_of_month=body.day_of_month,
        params=body.params or {},
        priority=body.priority,
        max_retries=body.max_retries,
        retry_backoff=body.retry_backoff,
        is_active=True
    )
    db.add(config)
    try:
        db.commit()
        db.refresh(config)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
        
    return {"id": config.id, "message": f"Pipeline '{nombre}' creado. Beat lo detectará en ≤60s."}


@router.put("/{pipeline_id}")
def update_pipeline(
    pipeline_id: int, body: PipelineUpdate, db: Session = Depends(get_dest_db)
):
    config = db.query(EtlPipelineConfig).filter(
        EtlPipelineConfig.id == pipeline_id
    ).first()
    if not config:
        raise HTTPException(status_code=404, detail="Pipeline no encontrado")
    
    try:
        if body.is_active is not None:
            config.is_active = body.is_active
            
        if body.schedule_type is not None:
            config.schedule_type = body.schedule_type
            
        if body.time_str is not None:
            config.schedule_value = body.time_str
            
        if body.day_of_week is not None:
            config.day_of_week = body.day_of_week
            
        if body.day_of_month is not None:
            config.day_of_month = body.day_of_month
            
        if body.params is not None:
            config.params = body.params
            # Update subcategoria_id if it changed in params
            if "subcategorias" in body.params:
                subs = body.params["subcategorias"]
                if subs:
                    config.subcategoria_id = subs[0]
                    
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
        
    return {"id": config.id, "message": "Pipeline actualizado. Beat sincronizará en ≤60s."}


@router.delete("/{pipeline_id}")
def delete_pipeline(pipeline_id: int, db: Session = Depends(get_dest_db)):
    config = db.query(EtlPipelineConfig).filter(
        EtlPipelineConfig.id == pipeline_id
    ).first()
    if not config:
        raise HTTPException(status_code=404, detail="Pipeline no encontrado")
    try:
        db.delete(config)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    return {"message": "Pipeline eliminado"}


@router.post("/{pipeline_id}/toggle")
def toggle_pipeline(pipeline_id: int, db: Session = Depends(get_dest_db)):
    """Activar/desactivar un pipeline."""
    config = db.query(EtlPipelineConfig).filter(
        EtlPipelineConfig.id == pipeline_id
    ).first()
    if not config:
        raise HTTPException(status_code=404, detail="Pipeline no encontrado")
    config.is_active = not config.is_active
    db.commit()
    return {"id": config.id, "is_active": config.is_active}


@router.post("/{pipeline_id}/run-now")
def run_pipeline_now(pipeline_id: int, db: Session = Depends(get_dest_db)):
    """Ejecutar un pipeline inmediatamente (fuera de schedule)."""
    config = db.query(EtlPipelineConfig).filter(
        EtlPipelineConfig.id == pipeline_id
    ).first()
    if not config:
        raise HTTPException(status_code=404, detail="Pipeline no encontrado")
    
    from backend.app.celery_tasks.etl_worker import run_etl_pipeline
    task = run_etl_pipeline.apply_async(
        args=[pipeline_id],
        queue="etl",
        priority=1,  # Máxima prioridad para ejecuciones manuales
    )
    
    return {
        "message": f"Pipeline '{config.nombre}' encolado",
        "celery_task_id": task.id,
    }


@router.get("/ejecuciones")
def list_ejecuciones(
    pipeline_id: Optional[int] = None,
    company_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_dest_db),
):
    """Historial de ejecuciones con filtros."""
    query = db.query(EtlEjecucion)
    if pipeline_id:
        query = query.filter(EtlEjecucion.pipeline_id == pipeline_id)
    if company_id:
        query = query.filter(EtlEjecucion.empresa_id == company_id)
    if status:
        query = query.filter(EtlEjecucion.status == status)
    
    ejecuciones = query.order_by(EtlEjecucion.queued_at.desc()).limit(limit).all()
    
    return [{
        "id": e.id,
        "pipeline_id": e.pipeline_id,
        "pipeline_nombre": e.pipeline.nombre if e.pipeline else "?",
        "company_id": e.empresa_id,
        "celery_task_id": e.celery_task_id,
        "status": e.status,
        "step_current": e.step_current,
        "records_extracted": e.records_extracted,
        "records_generated": e.records_generated,
        "records_migrated": e.records_migrated,
        "queued_at": str(e.queued_at) if e.queued_at else None,
        "started_at": str(e.started_at) if e.started_at else None,
        "finished_at": str(e.finished_at) if e.finished_at else None,
        "duration_s": float(e.duration_s) if e.duration_s else None,
        "error_message": e.error_message,
        "retry_count": e.retry_count,
    } for e in ejecuciones]


@router.get("/status/live")
def live_status(db: Session = Depends(get_dest_db)):
    """
    Status en tiempo real: qué está corriendo ahora, qué falló recientemente.
    """
    from backend.app.celery_tasks import company_semaphore
    from backend.app.models.models import Company
    
    # Tareas corriendo ahora
    running = db.query(EtlEjecucion).filter(
        EtlEjecucion.status == "RUNNING"
    ).all()
    
    # Últimos errores (últimas 2 horas)
    from datetime import datetime, timedelta
    two_hours_ago = datetime.now() - timedelta(hours=2)
    recent_errors = db.query(EtlEjecucion).filter(
        EtlEjecucion.status == "ERROR",
        EtlEjecucion.finished_at >= two_hours_ago,
    ).order_by(EtlEjecucion.finished_at.desc()).limit(10).all()
    
    # Semáforos por empresa
    companies = db.query(Company).filter(Company.is_active == True).all()
    semaphores = {}
    for c in companies:
        semaphores[c.name] = {
            "active": company_semaphore.active_count(c.id),
            "max": company_semaphore.DEFAULT_MAX,
            "tasks": company_semaphore.active_tasks(c.id),
        }
    
    return {
        "running": [{
            "pipeline_nombre": r.pipeline.nombre if r.pipeline else "?",
            "company_id": r.empresa_id,
            "step_current": r.step_current,
            "started_at": str(r.started_at),
            "celery_task_id": r.celery_task_id,
        } for r in running],
        "recent_errors": [{
            "pipeline_nombre": e.pipeline.nombre if e.pipeline else "?",
            "error_message": e.error_message[:200] if e.error_message else None,
            "finished_at": str(e.finished_at),
            "retry_count": e.retry_count,
        } for e in recent_errors],
        "semaphores": semaphores,
    }
