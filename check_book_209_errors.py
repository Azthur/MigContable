#!/usr/bin/env python3
"""Script para verificar errores del libro 209."""
import sys
sys.path.insert(0, '/app')

from backend.app.core.database import dest_engine
from sqlalchemy import text

def check_book_209_errors():
    conn = dest_engine.connect()
    
    print("=== REGISTROS CON ERROR (estado='0') DEL LIBRO 209 ===")
    result = conn.execute(text("""
        SELECT subcategoria_id, nasiento, nidlin, cper, cmes, ccodcue, 
               ndebe, nhaber, cglosa, idcontrol, estado
        FROM cf_diariol 
        WHERE subcategoria_id IN (80,81,82,83,116)
        AND estado = '0'
        ORDER BY subcategoria_id, nasiento, nidlin
        LIMIT 20
    """))
    
    error_rows = list(result)
    if error_rows:
        for row in error_rows:
            print(f"\nSubcat {row[0]} | Asiento {row[1]} Lín {row[2]}")
            print(f"  cper: '{row[3]}' | cmes: '{row[4]}'")
            print(f"  Cuenta: {row[5]} | Debe: {row[6]} | Haber: {row[7]}")
            print(f"  Glosa: {row[8][:100] if row[8] else 'None'}...")
            print(f"  ID Control: {row[9]}")
            print(f"  Estado: {row[10]}")
    else:
        print("No hay registros con estado '0' (error)")
    
    print("\n=== RESUMEN DE VALORES cper EN ERRORES ===")
    result = conn.execute(text("""
        SELECT cper, COUNT(*) as total
        FROM cf_diariol 
        WHERE subcategoria_id IN (80,81,82,83,116)
        AND estado = '0'
        GROUP BY cper
        ORDER BY total DESC
    """))
    
    for row in result:
        print(f"  cper='{row[0]}': {row[1]} registros")
    
    print("\n=== RESUMEN DE VALORES cmes EN ERRORES ===")
    result = conn.execute(text("""
        SELECT cmes, COUNT(*) as total
        FROM cf_diariol 
        WHERE subcategoria_id IN (80,81,82,83,116)
        AND estado = '0'
        GROUP BY cmes
        ORDER BY total DESC
    """))
    
    for row in result:
        print(f"  cmes='{row[0]}': {row[1]} registros")
    
    conn.close()

if __name__ == "__main__":
    check_book_209_errors()
