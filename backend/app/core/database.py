from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.app.core.config import get_settings

settings = get_settings()

# Source Database (SQL Server 2022)
# Connection pooling optimizado para reducir I/O
source_engine = create_engine(
    settings.SQL_SERVER_CONNECTION_STRING,
    echo=settings.DEBUG,
    fast_executemany=True,  # Important for SQL Server performance
    pool_size=5,            # Conexiones permanentes en el pool
    max_overflow=10,        # Conexiones adicionales cuando el pool está lleno
    pool_pre_ping=True,     # Verificar conexiones antes de usarlas
    pool_recycle=3600,      # Reciclar conexiones cada hora (evitar stale connections)
)
SourceSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=source_engine)
SourceBase = declarative_base()

# Destination Database (PostgreSQL 9.4)
# Connection pooling optimizado para reducir I/O
dest_engine = create_engine(
    settings.POSTGRES_CONNECTION_STRING,
    echo=settings.DEBUG,
    pool_size=10,           # Más conexiones para PostgreSQL (más usado)
    max_overflow=20,        # Mayor overflow para picos de demanda
    pool_pre_ping=True,     # Verificar conexiones antes de usarlas
    pool_recycle=3600,      # Reciclar conexiones cada hora
)
DestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=dest_engine)
DestBase = declarative_base()

def get_source_db():
    db = SourceSessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def get_dest_db():
    db = DestSessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

