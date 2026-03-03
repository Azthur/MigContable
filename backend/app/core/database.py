from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.app.core.config import get_settings

settings = get_settings()

# Source Database (SQL Server 2022)
source_engine = create_engine(
    settings.SQL_SERVER_CONNECTION_STRING,
    echo=settings.DEBUG,
    fast_executemany=True  # Important for SQL Server performance
)
SourceSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=source_engine)
SourceBase = declarative_base()

# Destination Database (PostgreSQL 9.4)
dest_engine = create_engine(
    settings.POSTGRES_CONNECTION_STRING,
    echo=settings.DEBUG
)
DestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=dest_engine)
DestBase = declarative_base()

def get_source_db():
    db = SourceSessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_dest_db():
    db = DestSessionLocal()
    try:
        yield db
    finally:
        db.close()
