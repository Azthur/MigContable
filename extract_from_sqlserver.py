import pyodbc
from backend.app.core.database import DestSessionLocal
from sqlalchemy import text

# Configuración SQL Server (de subdiario209_config.json)
SQL_SERVER_CONFIG = {
    'server': '192.168.1.17,1433',
    'database': 'YELAVE22',
    'uid': 'sa',
    'pwd': 'Pa$$word'
}

def connect_sql_server():
    """Conecta a SQL Server."""
    try:
        conn_str = (
            f"DRIVER=ODBC Driver 18 for SQL Server;"
            f"SERVER={SQL_SERVER_CONFIG['server']};"
            f"DATABASE={SQL_SERVER_CONFIG['database']};"
            f"UID={SQL_SERVER_CONFIG['uid']};"
            f"PWD={SQL_SERVER_CONFIG['pwd']};"
            f"TrustServerCertificate=yes;"
            f"Timeout=30"
        )
        conn = pyodbc.connect(conn_str)
        return conn
    except Exception as e:
        print(f"Error conectando a SQL Server: {e}")
        return None

def fix_encoding(value):
    """Corrige el encoding de un valor."""
    if value is None or not isinstance(value, str):
        return value
    try:
        # Re-encode as UTF-8 to ensure proper encoding
        return value.encode('utf-8', errors='replace').decode('utf-8')
    except Exception:
        return str(value)

def get_sql_server_tables():
    """Obtiene las tablas disponibles en SQL Server."""
    conn = connect_sql_server()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_NAME")
        tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return tables
    except Exception as e:
        print(f"Error obteniendo tablas: {e}")
        conn.close()
        return []

def find_auxiliary_tables():
    """Busca tablas de auxiliares en SQL Server."""
    tables = get_sql_server_tables()
    aux_tables = [t for t in tables if 'aux' in t.lower() or 'ent' in t.lower()]
    print("=== TABLAS EN SQL SERVER ===")
    print(f"Total tablas: {len(tables)}")
    print(f"\nTablas que podrían ser auxiliares:")
    for table in aux_tables:
        print(f"  - {table}")
    return aux_tables

def get_table_structure(table_name):
    """Obtiene la estructura de una tabla."""
    conn = connect_sql_server()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table_name}' ORDER BY ORDINAL_POSITION")
        columns = [(row[0], row[1]) for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return columns
    except Exception as e:
        print(f"Error obteniendo estructura de {table_name}: {e}")
        conn.close()
        return None

if __name__ == "__main__":
    print("=== BUSCANDO TABLA DE AUXILIARES EN SQL SERVER ===\n")
    
    aux_tables = find_auxiliary_tables()
    
    if aux_tables:
        print(f"\n=== ESTRUCTURA DE TABLAS DE AUXILIARES ===")
        for table in aux_tables[:5]:  # Primeras 5 tablas
            print(f"\nTabla: {table}")
            columns = get_table_structure(table)
            if columns:
                for col_name, col_type in columns:
                    print(f"  {col_name}: {col_type}")
