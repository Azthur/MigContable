from celery import Celery
from backend.app.core.config import get_settings

settings = get_settings()

celery = Celery(
    "sistemamigconta",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery.conf.update(
    # Serialización
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # Timezone
    timezone="America/Lima",
    enable_utc=True,
    
    # Worker
    worker_prefetch_multiplier=1,      # No prefetch (tareas pesadas)
    worker_max_tasks_per_child=50,     # Reciclar workers para evitar memory leaks
    worker_concurrency=4,              # 4 workers por proceso
    
    # Retry global
    task_acks_late=True,               # ACK después de completar (no al recibir)
    task_reject_on_worker_lost=True,   # Re-encolar si worker muere
    
    # Resultados
    result_expires=86400,              # Limpiar resultados después de 24h
    
    # Rutas de tareas
    task_routes={
        "backend.app.celery_tasks.etl_worker.run_etl_pipeline": {"queue": "etl"},
    },
    
    # Beat schedule (vacío — se llena dinámicamente desde DB)
    beat_schedule={},
)

# Import tasks explicitly to register them
import backend.app.celery_tasks.etl_worker

