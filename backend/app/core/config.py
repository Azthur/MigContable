from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    API_PORT: int = 8000
    DEBUG: bool = True
    
    # Source Database (SQL Server)
    SQL_SERVER_CONNECTION_STRING: str
    
    # Destination Database (PostgreSQL)
    POSTGRES_CONNECTION_STRING: str
    
    # Celery + Redis
    REDIS_URL: str = "redis://redis:6379/0"
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/1"
    
    # Concurrencia
    MAX_WORKERS_PER_COMPANY: int = 4
    BEAT_SCAN_INTERVAL: int = 60  # segundos entre escaneos de DB
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

@lru_cache()
def get_settings():
    return Settings()
