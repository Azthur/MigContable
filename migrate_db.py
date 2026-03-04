import logging
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_data():
    source_url = "postgresql://postgres:postgres@host.docker.internal:5433/migconta_db"
    dest_url = "postgresql://postgres:postgres@db:5432/migconta_db"

    source_engine = create_engine(source_url)
    dest_engine = create_engine(dest_url)

    metadata = MetaData()
    metadata.reflect(bind=source_engine)

    
    from sqlalchemy import text
    
    with dest_engine.connect() as dest_conn:
        logger.info("Truncando tablas de destino con CASCADE...")
        for table in reversed(metadata.sorted_tables):
            try:
                with dest_conn.begin():
                    dest_conn.execute(text(f"TRUNCATE TABLE {table.name} CASCADE"))
            except Exception as e:
                logger.warning(f"Error truncando tabla {table.name}: {e}")
                
        logger.info("Empezando migracion de datos...")
        with source_engine.connect() as src_conn:
            for table in metadata.sorted_tables:
                logger.info(f"Copiando tabla {table.name}...")
                records = src_conn.execute(table.select()).fetchall()
                if records:
                    try:
                        with dest_conn.begin():
                            dest_conn.execute(table.insert(), [dict(row._mapping) for row in records])
                        logger.info(f"  -> {len(records)} filas copiadas en {table.name}")
                    except Exception as e:
                        logger.error(f"  -> Error copiando {table.name}: {e}")
                else:
                    logger.info(f"  -> 0 filas")
    
    logger.info("Migración completada!")

if __name__ == "__main__":
    migrate_data()
