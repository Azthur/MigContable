import logging
from sqlalchemy import create_engine, MetaData

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_single():
    source_url = "postgresql://postgres:postgres@host.docker.internal:5433/migconta_db"
    dest_url = "postgresql://postgres:postgres@db:5432/migconta_db"

    source_engine = create_engine(source_url)
    dest_engine = create_engine(dest_url)

    metadata = MetaData()
    metadata.reflect(bind=source_engine)
    
    table_name = "mapeo_lineas_asiento"
    table = metadata.tables.get(table_name)
    
    if table is None:
        logger.error(f"Table {table_name} not found in source!")
        return

    logger.info(f"Copiando tabla {table.name}...")
    with source_engine.connect() as src_conn:
        records = src_conn.execute(table.select()).fetchall()
        if not records:
            logger.info("  -> 0 filas")
            return
            
    dest_metadata = MetaData()
    dest_metadata.reflect(bind=dest_engine)
    dest_table = dest_metadata.tables.get(table_name)
    valid_columns = set(dest_table.columns.keys())

    with dest_engine.connect() as dest_conn:
        try:
            with dest_conn.begin():
                filtered_records = []
                for row in records:
                    row_dict = dict(row._mapping)
                    filtered_dict = {k: v for k, v in row_dict.items() if k in valid_columns}
                    filtered_records.append(filtered_dict)
                dest_conn.execute(dest_table.insert(), filtered_records)
            logger.info(f"  -> {len(records)} filas copiadas en {table.name}")
        except Exception as e:
            logger.error(f"  -> Error copiando {table.name}: {e}")

if __name__ == "__main__":
    migrate_single()
