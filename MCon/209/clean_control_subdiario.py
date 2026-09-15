#!/usr/bin/env python3
"""Script para limpiar la tabla de control de migración del Subdiario 209."""

import pyodbc
import sys

def clean_control():
    """Limpia la tabla de control de migración."""
    try:
        conn_str = (
            "DRIVER=ODBC Driver 17 for SQL Server;"
            "SERVER=192.168.1.17;"
            "DATABASE=YELAVE22;"
            "UID=sa;"
            "PWD=Pa$$word;"
            "Timeout=10"
        )
        print("Conectando a SQL Server...")
        conn = pyodbc.connect(conn_str)
        
        cursor = conn.cursor()
        
        # Verificar cantidad de registros antes de limpiar
        query_count = "SELECT COUNT(*) FROM Subdiario209_ControlMigracion"
        cursor.execute(query_count)
        count = cursor.fetchone()[0]
        print(f"Registros en control antes de limpiar: {count}")
        
        if count == 0:
            print("No hay registros para limpiar.")
            cursor.close()
            conn.close()
            return True
        
        print(f"Eliminando {count} registros de control...")
        
        # Eliminar todos los registros de control
        query_delete = "DELETE FROM Subdiario209_ControlMigracion"
        cursor.execute(query_delete)
        
        conn.commit()
        
        # Verificar cantidad después de limpiar
        cursor.execute(query_count)
        count_after = cursor.fetchone()[0]
        print(f"Registros en control después de limpiar: {count_after}")
        
        cursor.close()
        conn.close()
        print("Limpieza de control completada exitosamente.")
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    success = clean_control()
    sys.exit(0 if success else 1)
