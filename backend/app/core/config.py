from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    API_PORT: int = 8000
    DEBUG: bool = True
    
    # Source Database (SQL Server)
    SQL_SERVER_CONNECTION_STRING: str
    
    # Destination Database (PostgreSQL)
    POSTGRES_CONNECTION_STRING: str
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

@lru_cache()
def get_settings():
    return Settings()
