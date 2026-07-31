#!/usr/bin/env python3
"""Script para probar conexión a SQL Server desde el contenedor Docker."""

import pyodbc
import sys
import os

def test_connection():
    """Prueba conexión a SQL Server."""
    try:
        password = os.getenv('SQL_SERVER_PASSWORD', 'Pa$$word')
        conn_str = (
            f"DRIVER=ODBC Driver 17 for SQL Server;"
            f"SERVER=192.168.1.17;"
            f"DATABASE=YELAVE22;"
            f"UID=sa;"
            f"PWD={password};"
            f"Timeout=10"
        )
        print(f"Intentando conectar a SQL Server en 192.168.1.17 con password: {password}")
        conn = pyodbc.connect(conn_str)
        print("✅ Conexión exitosa a SQL Server")
        
        cursor = conn.cursor()
        cursor.execute("SELECT @@VERSION")
        version = cursor.fetchone()
        print(f"Versión de SQL Server: {version[0][:100]}...")
        
        cursor.execute("SELECT DB_NAME()")
        db_name = cursor.fetchone()
        print(f"Base de datos: {db_name[0]}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error conectando a SQL Server: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
