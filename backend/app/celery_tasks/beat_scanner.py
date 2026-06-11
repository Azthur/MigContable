"""
Custom Beat Scanner: Lee etl_pipeline_config cada N segundos
y sincroniza las tareas programadas con Celery Beat.

Se ejecuta como proceso independiente via 'celery -A backend.app.celery_app beat'.
"""
from celery import Celery
from celery.beat import Scheduler, ScheduleEntry
from celery.schedules import crontab, schedule as interval_schedule
from datetime import timedelta
from backend.app.core.database import DestSessionLocal
import logging

logger = logging.getLogger(__name__)


def parse_schedule(schedule_type: str, schedule_value: str, day_of_week: str = None, day_of_month: int = None):
    """Convierte configuración de DB a objeto schedule de Celery."""
    schedule_type = schedule_type.upper()
    
    if schedule_type == "MINUTES":
        try:
            minutes = int(schedule_value)
        except ValueError:
            minutes = 60
        return interval_schedule(run_every=timedelta(minutes=minutes))
    
    elif schedule_type == "DAILY":
        # schedule_value = "HH:MM"
        hour, minute = map(int, schedule_value.split(":"))
        return crontab(hour=hour, minute=minute)
    
    elif schedule_type == "WEEKLY":
        # schedule_value = "HH:MM"
        hour, minute = map(int, schedule_value.split(":"))
        return crontab(
            day_of_week=day_of_week or "mon",
            hour=hour,
            minute=minute,
        )
    
    elif schedule_type == "MONTHLY":
        # schedule_value = "HH:MM"
        hour, minute = map(int, schedule_value.split(":"))
        return crontab(
            day_of_month=day_of_month or 1,
            hour=hour,
            minute=minute,
        )
    
    elif schedule_type == "CRON":
        # schedule_value = cron expression "*/5 * * * *"
        parts = schedule_value.split()
        if len(parts) == 5:
            return crontab(
                minute=parts[0],
                hour=parts[1],
                day_of_month=parts[2],
                month_of_year=parts[3],
                day_of_week=parts[4],
            )
    
    # Fallback: cada 60 minutos
    return interval_schedule(run_every=timedelta(minutes=60))


class DatabaseScheduler(Scheduler):
    """
    Scheduler personalizado que lee la tabla etl_pipeline_config.
    El Beat solo sabe encolar — no conoce lógica ETL.
    """
    
    # Intervalo de sincronización con DB (segundos)
    UPDATE_INTERVAL = timedelta(seconds=60)
    
    def __init__(self, *args, **kwargs):
        self._last_sync = None
        super().__init__(*args, **kwargs)
    
    def setup_schedule(self):
        """Carga inicial desde DB."""
        self.update_schedule_from_db()
    
    def update_schedule_from_db(self):
        """Lee etl_pipeline_config y scheduled_tasks y sincroniza con Beat."""
        db = DestSessionLocal()
        try:
            from backend.app.models.models import EtlPipelineConfig, ScheduledTask
            
            # 1. Pipelines nuevos
            configs = db.query(EtlPipelineConfig).filter(
                EtlPipelineConfig.is_active == True
            ).all()
            
            new_entries = {}
            for cfg in configs:
                task_name = f"pipeline_{cfg.id}"
                celery_schedule = parse_schedule(
                    cfg.schedule_type, cfg.schedule_value
                )
                
                entry = ScheduleEntry(
                    name=task_name,
                    task="backend.app.celery_tasks.etl_worker.run_etl_pipeline",
                    schedule=celery_schedule,
                    args=(cfg.id,),
                    kwargs={},
                    options={"queue": "etl", "priority": cfg.priority or 5},
                    app=self.app,
                )
                new_entries[task_name] = entry

            # 2. Tareas legadas (TC_SUNAT, MES_ROTATION)
            legacy_tasks = db.query(ScheduledTask).filter(
                ScheduledTask.is_active == True,
                ScheduledTask.task_type.in_(["TC_SUNAT", "MES_ROTATION"])
            ).all()
            
            for lt in legacy_tasks:
                task_name = f"legacy_task_{lt.id}"
                celery_schedule = parse_schedule(
                    lt.schedule_type, lt.time_str,
                    day_of_week=lt.day_of_week,
                    day_of_month=lt.day_of_month
                )
                
                entry = ScheduleEntry(
                    name=task_name,
                    task="backend.app.celery_tasks.etl_worker.run_legacy_task",
                    schedule=celery_schedule,
                    args=(lt.id,),
                    kwargs={},
                    options={"queue": "etl"},
                    app=self.app,
                )
                new_entries[task_name] = entry
            
            # Reemplazar schedule completo
            self.merge_inplace(new_entries)
            logger.info(
                f"Beat sincronizado: {len(configs)} pipelines y {len(legacy_tasks)} tareas legadas activas"
            )
            
        except Exception as e:
            logger.error(f"Error sincronizando Beat con DB: {e}")
        finally:
            db.close()

    
    def tick(self):
        """Override: re-sincroniza con DB periódicamente."""
        from datetime import datetime
        now = datetime.now()
        
        if (self._last_sync is None or 
            now - self._last_sync > self.UPDATE_INTERVAL):
            self.update_schedule_from_db()
            self._last_sync = now
        
        return super().tick()
