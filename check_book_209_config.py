#!/usr/bin/env python3
"""Script para verificar configuración y errores del libro 209."""
import sys
sys.path.insert(0, '/app')

from backend.app.core.database import dest_engine
from sqlalchemy import text

def check_book_209_config():
    conn = dest_engine.connect()
    
    print("=== CONFIGURACIÓN DE SUBCATEGORÍAS DEL LIBRO 209 ===")
    result = conn.execute(text("""
        SELECT id, nombre, tabla_origen, filter_rules, clave_asiento, 
               generate_headers, generate_details, asiento_inicial
        FROM mapeo_subcategorias 
        WHERE nombre LIKE '%209%'
        ORDER BY id
    """))
    
    subcats_209 = []
    for row in result:
        subcats_209.append(row[0])
        print(f"\nID: {row[0]} | {row[1]}")
        print(f"  Tabla origen: {row[2]}")
        print(f"  Filter rules: {row[3]}")
        print(f"  Clave asiento: {row[4]}")
        print(f"  Generate headers: {row[5]}")
        print(f"  Generate details: {row[6]}")
        print(f"  Asiento inicial: {row[7]}")
    
    if subcats_209:
        print(f"\n=== ESTADOS EN cf_diariol PARA LIBRO 209 ===")
        placeholders = ','.join([str(sid) for sid in subcats_209])
        result = conn.execute(text(f"""
            SELECT subcategoria_id, estado, COUNT(*) as total
            FROM cf_diariol 
            WHERE subcategoria_id IN ({placeholders})
            GROUP BY subcategoria_id, estado
            ORDER BY subcategoria_id, estado
        """))
        
        for row in result:
            print(f"  Subcategoría {row[0]} | Estado '{row[1]}': {row[2]} registros")
        
        print(f"\n=== REGISTROS CON ERROR (estado='0') DEL LIBRO 209 ===")
        result = conn.execute(text(f"""
            SELECT subcategoria_id, nasiento, nidlin, ccodcue, 
                   ndebe, nhaber, cglosa, idcontrol
            FROM cf_diariol 
            WHERE subcategoria_id IN ({placeholders})
            AND estado = '0'
            ORDER BY subcategoria_id, nasiento, nidlin
            LIMIT 20
        """))
        
        error_rows = list(result)
        if error_rows:
            for row in error_rows:
                print(f"  Subcat {row[0]} | Asiento {row[1]} Lín {row[2]}")
                print(f"    Cuenta: {row[3]} | Debe: {row[4]} | Haber: {row[5]}")
                print(f"    Glosa: {row[6][:100] if row[6] else 'None'}...")
                print(f"    ID Control: {row[7]}")
                print()
        else:
            print("  No hay registros con estado '0' (error)")
            
        print(f"\n=== REGISTROS PENDIENTES (estado='1') DEL LIBRO 209 ===")
        result = conn.execute(text(f"""
            SELECT subcategoria_id, COUNT(*) as total
            FROM cf_diariol 
            WHERE subcategoria_id IN ({placeholders})
            AND estado = '1'
            GROUP BY subcategoria_id
        """))
        
        pending_rows = list(result)
        if pending_rows:
            for row in pending_rows:
                print(f"  Subcategoría {row[0]}: {row[1]} registros pendientes")
        else:
            print("  No hay registros pendientes")
    else:
        print("No se encontraron subcategorías del libro 209")
    
    conn.close()

if __name__ == "__main__":
    check_book_209_config()
