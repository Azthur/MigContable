from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from backend.app.core.database import get_dest_db
from backend.app.models.models import ScheduledTask

router = APIRouter()

class TaskCreate(BaseModel):
    company_id: Optional[int] = None
    task_type: str
    schedule_type: str
    time_str: str
    day_of_week: Optional[str] = None
    day_of_month: Optional[int] = None
    params: Optional[dict] = None

class TaskUpdate(BaseModel):
    company_id: Optional[int] = None
    task_type: Optional[str] = None
    schedule_type: Optional[str] = None
    time_str: Optional[str] = None
    day_of_week: Optional[str] = None
    day_of_month: Optional[int] = None
    is_active: Optional[bool] = None
    params: Optional[dict] = None

@router.get("")
def list_tasks(db: Session = Depends(get_dest_db)):
    tasks = db.query(ScheduledTask).order_by(ScheduledTask.id.desc()).all()
    from backend.app.core.scheduler import scheduler
    from backend.app.models.models import Company, MapeoSubcategoria
    
    result = []
    for t in tasks:
        # Check actual next run time from apscheduler
        job = scheduler.get_job(f"task_{t.id}")
        real_next_run = str(job.next_run_time) if job and job.next_run_time else (str(t.next_run) if t.next_run else None)
        
        # Get Company name
        company_name = "Todas"
        if t.company_id:
            comp = db.query(Company).filter(Company.id == t.company_id).first()
            if comp:
                company_name = comp.name
                
        # Get Subcategory names
        subcategoria_nombres = "Todas las Subcategorías"
        if t.params and "subcategorias" in t.params:
            subids = t.params["subcategorias"]
            if subids:
                subs = db.query(MapeoSubcategoria).filter(MapeoSubcategoria.id.in_(subids)).all()
                if subs:
                    subcategoria_nombres = ", ".join([s.nombre for s in subs])
        
        result.append({
            "id": t.id,
            "company_id": t.company_id,
            "company_name": company_name,
            "subcategoria_nombres": subcategoria_nombres,
            "task_type": t.task_type,
            "schedule_type": t.schedule_type,
            "time_str": t.time_str,
            "day_of_week": t.day_of_week,
            "day_of_month": t.day_of_month,
            "is_active": t.is_active,
            "params": t.params,
            "last_run": str(t.last_run) if t.last_run else None,
            "next_run": real_next_run
        })
    return result

@router.post("")
def create_task(task: TaskCreate, db: Session = Depends(get_dest_db)):
    try:
        new_task = ScheduledTask(
            company_id=task.company_id,
            task_type=task.task_type,
            schedule_type=task.schedule_type,
            time_str=task.time_str,
            day_of_week=task.day_of_week,
            day_of_month=task.day_of_month,
            params=task.params
        )
        db.add(new_task)
        db.commit()
        db.refresh(new_task)
        
        # Reload scheduler dynamically if needed later
        from backend.app.core.scheduler import start_scheduler
        start_scheduler()
        
        return {"id": new_task.id, "message": "Task created successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{task_id}")
def update_task(task_id: int, task_data: TaskUpdate, db: Session = Depends(get_dest_db)):
    task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    try:
        update_data = task_data.model_dump(exclude_unset=True)
        for key, val in update_data.items():
            setattr(task, key, val)
        
        db.commit()
        db.refresh(task)
        
        from backend.app.core.scheduler import start_scheduler
        start_scheduler()
        
        return {"id": task.id, "message": "Task updated successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_dest_db)):
    task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    try:
        db.delete(task)
        db.commit()
        
        from backend.app.core.scheduler import scheduler
        job_id = f"task_{task_id}"
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)
            
        return {"message": "Task deleted"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/all/logs')
def get_all_task_logs(limit: int = 100, status: Optional[str] = None, db: Session = Depends(get_dest_db)):
    from backend.app.models.models import TaskLog, ScheduledTask
    query = db.query(TaskLog, ScheduledTask).join(ScheduledTask, TaskLog.task_id == ScheduledTask.id)
    if status:
        query = query.filter(TaskLog.status == status)
    logs = query.order_by(TaskLog.id.desc()).limit(limit).all()
    return [{'id': l.TaskLog.id, 'task_id': l.ScheduledTask.id, 'company_id': l.ScheduledTask.company_id, 'task_type': l.ScheduledTask.task_type, 'status': l.TaskLog.status, 'message': l.TaskLog.message, 'started_at': str(l.TaskLog.started_at) if l.TaskLog.started_at else None, 'finished_at': str(l.TaskLog.finished_at) if l.TaskLog.finished_at else None} for l in logs]

@router.get('/{task_id}/logs')
def get_task_logs(task_id: int, limit: int = 50, db: Session = Depends(get_dest_db)):
    from backend.app.models.models import TaskLog
    logs = db.query(TaskLog).filter(TaskLog.task_id == task_id).order_by(TaskLog.id.desc()).limit(limit).all()
    return [{'id': l.id, 'status': l.status, 'message': l.message, 'details': l.details, 'started_at': str(l.started_at) if l.started_at else None, 'finished_at': str(l.finished_at) if l.finished_at else None} for l in logs]

@router.post("/{task_id}/run")
def run_task_immediately(task_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_dest_db)):
    task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    from backend.app.core.scheduler import execute_scheduled_task
    background_tasks.add_task(execute_scheduled_task, task_id)
    return {"message": "Tarea iniciada en segundo plano"}
