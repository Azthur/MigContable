from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from typing import List, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def build_mssql_url(host: str, port: int, database: str, username: str, password: str, driver: str) -> str:
    """Construye la URL de conexión para SQL Server."""
    import urllib.parse
    # Manejar instancias nombradas como 192.168.1.17\SQL2022
    driver_encoded = urllib.parse.quote_plus(driver)
    # TrustServerCertificate is irrelevant/unsupported in legacy "SQL Server" driver
    # and "Native Client" drivers usually don't need it explicitly unless enforced.
    # It is critical for "ODBC Driver 18 for SQL Server" (and 17).
    conn_str = (
        f"mssql+pyodbc://{username}:{urllib.parse.quote_plus(password)}"
        f"@{host},{port}/{database}"
        f"?driver={driver_encoded}"
    )
    if "ODBC Driver" in driver:
        conn_str += "&TrustServerCertificate=yes"
    
    return conn_str


def build_postgres_url(host: str, port: int, database: str, username: str, password: str) -> str:
    """Construye la URL de conexión para PostgreSQL."""
    import urllib.parse
    return (
        f"postgresql://{username}:{urllib.parse.quote_plus(password)}"
        f"@{host}:{port}/{database}"
    )


class ConnectionManager:
    """Gestiona conexiones dinámicas a bases de datos por empresa."""

    @staticmethod
    def _resolve_host(host: str) -> str:
        """Resuelve localhost a host.docker.internal si está en Docker (Linux).
        Solo convierte localhost/127.0.0.1, deja IPs de red local sin cambios."""
        import os
        if os.name != 'nt' and host in ("localhost", "127.0.0.1"):
            return "host.docker.internal"
        # No convertir IPs de red local (192.168.x.x, 10.x.x.x, 172.16-31.x.x)
        return host

    @staticmethod
    def get_source_engine(conn_data: dict) -> Engine:
        """
        Crea un engine SQLAlchemy para la conexión fuente.
        conn_data: dict con host, port, database_name, username, password, driver, db_type
        """
        db_type = conn_data.get("db_type", "MSSQL").upper()
        host = ConnectionManager._resolve_host(conn_data["host"])
        if db_type == "MSSQL":
            driver = conn_data.get("driver", "ODBC Driver 17 for SQL Server")
            import os
            if os.name != 'nt' and driver in ("SQL Server", "SQL Server Native Client 11.0"):
                driver = "ODBC Driver 17 for SQL Server"

            url = build_mssql_url(
                host=host,
                port=conn_data.get("port", 1433),
                database=conn_data["database_name"],
                username=conn_data["username"],
                password=conn_data["password"],
                driver=driver
            )
            # fast_executemany requiere drivers ODBC modernos (13, 17, 18).
            # El driver legacy "SQL Server" falla con esta opción.
            use_fast = "ODBC Driver" in driver

            return create_engine(url, fast_executemany=use_fast, connect_args={"timeout": 10})
        elif db_type == "POSTGRESQL":
            url = build_postgres_url(
                host=host,
                port=conn_data.get("port", 5432),
                database=conn_data["database_name"],
                username=conn_data["username"],
                password=conn_data["password"]
            )
            return create_engine(url)
        else:
            raise ValueError(f"Tipo de base de datos no soportado: {db_type}")

    @staticmethod
    def get_dest_engine(conn_data: dict) -> Engine:
        """Crea un engine SQLAlchemy para la conexión destino (PostgreSQL)."""
        host = ConnectionManager._resolve_host(conn_data["host"])
        url = build_postgres_url(
            host=host,
            port=conn_data.get("port", 5433),
            database=conn_data["database_name"],
            username=conn_data["username"],
            password=conn_data["password"]
        )
        return create_engine(url)

    @staticmethod
    def test_source_connection(conn_data: dict) -> Dict:
        """Prueba la conexión fuente y retorna estado."""
        try:
            engine = ConnectionManager.get_source_engine(conn_data)
            with engine.connect() as connection:
                result = connection.execute(text("SELECT @@VERSION"))
                version = result.fetchone()[0]
            engine.dispose()
            return {
                "status": "OK",
                "message": f"Conexión exitosa",
                "server_version": version[:100] if version else "Desconocida",
                "tested_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error probando conexión fuente: {e}")
            return {
                "status": "ERROR",
                "message": str(e),
                "server_version": None,
                "tested_at": datetime.now().isoformat()
            }

    @staticmethod
    def test_dest_connection(conn_data: dict) -> Dict:
        """Prueba la conexión destino PostgreSQL."""
        try:
            engine = ConnectionManager.get_dest_engine(conn_data)
            with engine.connect() as connection:
                result = connection.execute(text("SELECT version()"))
                version = result.fetchone()[0]
            engine.dispose()
            return {
                "status": "OK",
                "message": "Conexión exitosa",
                "server_version": version[:100] if version else "Desconocida",
                "tested_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error probando conexión destino: {e}")
            return {
                "status": "ERROR",
                "message": str(e),
                "server_version": None,
                "tested_at": datetime.now().isoformat()
            }

    @staticmethod
    def list_tables(conn_data: dict) -> List[Dict]:
        """Lista todas las tablas disponibles en la base de datos fuente."""
        try:
            engine = ConnectionManager.get_source_engine(conn_data)
            db_type = conn_data.get("db_type", "MSSQL").upper()

            if db_type == "MSSQL":
                query = text("""
                    SELECT
                        TABLE_SCHEMA as table_schema,
                        TABLE_NAME as table_name,
                        TABLE_TYPE as table_type,
                        (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS c
                         WHERE c.TABLE_SCHEMA = t.TABLE_SCHEMA
                           AND c.TABLE_NAME = t.TABLE_NAME) as column_count
                    FROM INFORMATION_SCHEMA.TABLES t
                    WHERE TABLE_TYPE IN ('BASE TABLE', 'VIEW')
                    ORDER BY TABLE_SCHEMA, TABLE_NAME
                """)
            else:
                query = text("""
                    SELECT table_schema, table_name, table_type, 0 as column_count
                    FROM information_schema.tables
                    WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
                    ORDER BY table_schema, table_name
                """)

            with engine.connect() as connection:
                result = connection.execute(query)
                tables = [
                    {
                        "table_schema": row[0],
                        "table_name": row[1],
                        "table_type": row[2],
                        "column_count": row[3]
                    }
                    for row in result
                ]
            engine.dispose()
            return tables
        except Exception as e:
            logger.error(f"Error listando tablas: {e}")
            raise e

    @staticmethod
    def get_table_columns(conn_data: dict, table_schema: str, table_name: str) -> List[Dict]:
        """Obtiene las columnas de una tabla específica."""
        try:
            engine = ConnectionManager.get_source_engine(conn_data)
            db_type = conn_data.get("db_type", "MSSQL").upper()

            if db_type == "MSSQL":
                query = text("""
                    SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, CHARACTER_MAXIMUM_LENGTH
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_SCHEMA = :schema AND TABLE_NAME = :table
                    ORDER BY ORDINAL_POSITION
                """)
            else:
                query = text("""
                    SELECT column_name, data_type, is_nullable, character_maximum_length
                    FROM information_schema.columns
                    WHERE table_schema = :schema AND table_name = :table
                    ORDER BY ordinal_position
                """)

            with engine.connect() as connection:
                result = connection.execute(query, {"schema": table_schema, "table": table_name})
                columns = [
                    {
                        "column_name": row[0],
                        "data_type": row[1],
                        "is_nullable": row[2],
                        "max_length": row[3]
                    }
                    for row in result
                ]
            engine.dispose()
            return columns
        except Exception as e:
            logger.error(f"Error obteniendo columnas: {e}")
            raise e

    @staticmethod
    def list_postgres_tables(conn_data: dict) -> List[Dict]:
        """Lista todas las tablas disponibles en una base de datos PostgreSQL destino."""
        try:
            engine = ConnectionManager.get_dest_engine(conn_data)
            query = text("""
                SELECT
                    t.table_schema,
                    t.table_name,
                    t.table_type,
                    (SELECT COUNT(*) FROM information_schema.columns c
                     WHERE c.table_schema = t.table_schema
                       AND c.table_name = t.table_name) as column_count
                FROM information_schema.tables t
                WHERE t.table_schema NOT IN ('pg_catalog', 'information_schema')
                  AND t.table_type IN ('BASE TABLE', 'VIEW')
                ORDER BY t.table_schema, t.table_name
            """)

            with engine.connect() as connection:
                result = connection.execute(query)
                tables = [
                    {
                        "table_schema": row[0],
                        "table_name": row[1],
                        "table_type": row[2],
                        "column_count": row[3]
                    }
                    for row in result
                ]
            engine.dispose()
            return tables
        except Exception as e:
            logger.error(f"Error listando tablas PostgreSQL: {e}")
            raise e

    @staticmethod
    def get_postgres_table_columns(conn_data: dict, table_schema: str, table_name: str) -> List[Dict]:
        """Obtiene las columnas de una tabla específica en PostgreSQL con metadatos completos."""
        try:
            engine = ConnectionManager.get_dest_engine(conn_data)
            query = text("""
                SELECT column_name, data_type, is_nullable,
                       character_maximum_length,
                       numeric_precision, numeric_scale,
                       column_default, datetime_precision
                FROM information_schema.columns
                WHERE table_schema = :schema AND table_name = :table
                ORDER BY ordinal_position
            """)

            with engine.connect() as connection:
                result = connection.execute(query, {"schema": table_schema, "table": table_name})
                columns = [
                    {
                        "column_name": row[0],
                        "data_type": row[1],
                        "is_nullable": row[2],
                        "max_length": row[3],
                        "numeric_precision": row[4],
                        "numeric_scale": row[5],
                        "column_default": row[6],
                        "datetime_precision": row[7]
                    }
                    for row in result
                ]
            engine.dispose()
            return columns
        except Exception as e:
            logger.error(f"Error obteniendo columnas PostgreSQL: {e}")
            raise e
