"""
Semáforo Redis para limitar concurrencia por empresa.
Máximo N workers simultáneos por empresa_id.
"""
import redis
import time
from backend.app.core.config import get_settings

settings = get_settings()
_redis = redis.Redis.from_url(settings.REDIS_URL)

SEMAPHORE_PREFIX = "etl:semaphore:company:"
DEFAULT_MAX = settings.MAX_WORKERS_PER_COMPANY  # 4
LOCK_TTL = 3600  # 1 hora máximo (safety net si worker muere)


def acquire(empresa_id: int, task_id: str, max_concurrent: int = DEFAULT_MAX) -> bool:
    """
    Intenta adquirir un slot para la empresa.
    Retorna True si hay slot disponible, False si está lleno.
    """
    key = f"{SEMAPHORE_PREFIX}{empresa_id}"
    
    # Limpiar slots expirados
    now = time.time()
    _redis.zremrangebyscore(key, 0, now - LOCK_TTL)
    
    # Verificar slots disponibles
    current = _redis.zcard(key)
    if current >= max_concurrent:
        return False
    
    # Tomar slot (score = timestamp actual)
    _redis.zadd(key, {task_id: now})
    _redis.expire(key, LOCK_TTL)
    return True


def release(empresa_id: int, task_id: str):
    """Libera el slot de la empresa."""
    key = f"{SEMAPHORE_PREFIX}{empresa_id}"
    _redis.zrem(key, task_id)


def active_count(empresa_id: int) -> int:
    """Cuántos workers están activos para esta empresa."""
    key = f"{SEMAPHORE_PREFIX}{empresa_id}"
    now = time.time()
    _redis.zremrangebyscore(key, 0, now - LOCK_TTL)
    return _redis.zcard(key)


def active_tasks(empresa_id: int) -> list:
    """Lista de task_ids activos para esta empresa."""
    key = f"{SEMAPHORE_PREFIX}{empresa_id}"
    return [m.decode() for m in _redis.zrange(key, 0, -1)]
