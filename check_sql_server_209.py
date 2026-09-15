#!/usr/bin/env python3
"""Script para verificar datos del libro 209 en SQL Server (Majestic)."""
import sys
sys.path.insert(0, '/app')

from backend.app.core.database import get_dest_db
from backend.app.models.models import Company, SourceConnection
from backend.app.services.connection_manager import ConnectionManager
from sqlalchemy import text

def check_sql_server_209():
    db = next(get_dest_db())
    
    try:
        # Get company 5 (YELAVE NATURE S.A.C.)
        company = db.query(Company).filter(Company.id == 5).first()
        print(f"=== EMPRESA: {company.name if company else 'No encontrada'} ===")
        
        # Get source connection
        source_conn = db.query(SourceConnection).filter(
            SourceConnection.company_id == 5,
            SourceConnection.is_active == True
        ).first()
        
        if not source_conn:
            print("ERROR: No hay conexión origen configurada")
            return
            
        print(f"Host: {source_conn.host}:{source_conn.port}")
        print(f"Base de datos: {source_conn.database_name}")
        
        # Connect to SQL Server
        conn_data = {
            "host": source_conn.host,
            "port": source_conn.port,
            "database_name": source_conn.database_name,
            "username": source_conn.username,
            "password": source_conn.password,
            "driver": source_conn.driver,
            "db_type": source_conn.db_type
        }
        source_engine = ConnectionManager.get_source_engine(conn_data)
        conn = source_engine.connect()
        
        print("\n=== ESTRUCTURA DE TABLA finplanillamovilidaddet ===")
        result = conn.execute(text("""
            SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'finplanillamovilidaddet'
            ORDER BY ORDINAL_POSITION
        """))
        for row in result:
            print(f"  {row[0]} ({row[1]})" + (f"({row[2]})" if row[2] else ""))
        
        print("\n=== PRIMEROS 5 REGISTROS ===")
        result = conn.execute(text("SELECT TOP 5 * FROM finplanillamovilidaddet"))
        columns = [col[0] for col in result.cursor.description]
        print("Columnas:", columns)
        for row in result:
            print(f"  {dict(zip(columns, row))}")
        
        print("\n=== CONTEO TOTAL ===")
        result = conn.execute(text("SELECT COUNT(*) as total FROM finplanillamovilidaddet"))
        total = result.scalar()
        print(f"Total registros en finplanillamovilidaddet: {total}")
        
        # Try to find date/period columns to filter by
        print("\n=== BUSCAR COLUMNAS DE FECHA/PERIODO ===")
        result = conn.execute(text("""
            SELECT COLUMN_NAME, DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'finplanillamovilidaddet'
            AND (DATA_TYPE LIKE '%date%' OR DATA_TYPE LIKE '%time%' 
                 OR COLUMN_NAME LIKE '%fecha%' OR COLUMN_NAME LIKE '%periodo%'
                 OR COLUMN_NAME LIKE '%ano%' OR COLUMN_NAME LIKE '%mes%'
                 OR COLUMN_NAME LIKE '%per%')
        """))
        date_cols = list(result)
        if date_cols:
            for row in date_cols:
                print(f"  {row[0]} ({row[1]})")
            
            # Try to count by period if we find date columns
            first_date_col = date_cols[0][0]
            print(f"\n=== CONTEO POR {first_date_col} ===")
            result = conn.execute(text(f"""
                SELECT {first_date_col}, COUNT(*) as total
                FROM finplanillamovilidaddet
                GROUP BY {first_date_col}
                ORDER BY {first_date_col} DESC
            """))
            for row in result:
                print(f"  {row[0]}: {row[1]} registros")
        else:
            print("  No se encontraron columnas de fecha/periodo")
        
        conn.close()
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_sql_server_209()
