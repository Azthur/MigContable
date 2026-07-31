#!/usr/bin/env python3
"""Script para listar todas las tablas en SQL Server."""

import pyodbc
import sys

def list_all_tables():
    """Lista todas las tablas en SQL Server."""
    try:
        conn_str = (
            f"DRIVER=ODBC Driver 17 for SQL Server;"
            f"SERVER=192.168.1.17;"
            f"DATABASE=YELAVE22;"
            f"UID=sa;"
            f"PWD=Pa$$word;"
            f"Timeout=10"
        )
        print("Conectando a SQL Server...")
        conn = pyodbc.connect(conn_str)
        
        cursor = conn.cursor()
        
        # Listar todas las tablas
        query = """
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_NAME
        """
        cursor.execute(query)
        tables = cursor.fetchall()
        
        print(f"\nTodas las tablas en YELAVE22 ({len(tables)}):")
        for table in tables:
            print(f"  - {table[0]}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    success = list_all_tables()
    sys.exit(0 if success else 1)
