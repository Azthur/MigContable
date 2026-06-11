"""
Cache global de SQLAlchemy engines con pool de conexiones.
Evita crear un engine nuevo por cada subcategoría/tarea.
"""
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from threading import Lock
from typing import Dict
import logging

logger = logging.getLogger(__name__)

_engine_cache: Dict[str, Engine] = {}
_cache_lock = Lock()


def get_cached_engine(
    url: str,
    pool_size: int = 5,
    max_overflow: int = 10,
    pool_timeout: int = 30,
    pool_recycle: int = 1800,
    **kwargs
) -> Engine:
    """
    Retorna un engine cacheado por URL.
    Thread-safe gracias al Lock.
    """
    with _cache_lock:
        if url not in _engine_cache:
            logger.info(f"Creando engine para: {url[:50]}...")
            _engine_cache[url] = create_engine(
                url,
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_timeout=pool_timeout,
                pool_recycle=pool_recycle,
                **kwargs,
            )
        return _engine_cache[url]


def dispose_all():
    """Libera todos los engines cacheados (para shutdown)."""
    with _cache_lock:
        for url, engine in _engine_cache.items():
            try:
                engine.dispose()
            except Exception:
                pass
        _engine_cache.clear()
