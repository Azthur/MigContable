#!/usr/bin/env python3
"""Script para verificar la migración del libro 209."""
import sys
sys.path.insert(0, '/app')

from backend.app.core.database import dest_engine
from sqlalchemy import text

def check_book_209():
    conn = dest_engine.connect()
    
    print("=== TABLAS EN MIGCONTA_DB ===")
    result = conn.execute(text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name LIKE 'cf_%'
        ORDER BY table_name
    """))
    tables = [r[0] for r in result]
    for table in tables:
        print(f"  - {table}")
    
    print("\n=== CONFIGURACIÓN DE SUBCATEGORÍAS ===")
    result = conn.execute(text("""
        SELECT id, nombre, tabla_origen, tabla_destino_detalle, tabla_destino_cabecera
        FROM mapeo_subcategorias
        WHERE is_active = true
        ORDER BY id
    """))
    for row in result:
        print(f"  ID: {row[0]} | {row[1]}")
        print(f"    Origen: {row[2]}")
        print(f"    Destino Detalle: {row[3]}")
        print(f"    Destino Cabecera: {row[4]}")
        print()
    
    print("=== VERIFICAR LIBRO 209 EN STAGING (cf_diariol) ===")
    try:
        result = conn.execute(text("""
            SELECT subcategoria_id, COUNT(*) as total, 
                   COUNT(CASE WHEN estado = 'MIGRADO' THEN 1 END) as migrados,
                   COUNT(CASE WHEN estado = 'PENDIENTE' THEN 1 END) as pendientes,
                   COUNT(CASE WHEN estado = 'ERROR' THEN 1 END) as errores
            FROM cf_diariol
            WHERE cglosa LIKE '%209%' OR ccoddoc = '209'
            GROUP BY subcategoria_id
        """))
        rows = list(result)
        if rows:
            for row in rows:
                print(f"  Subcategoría {row[0]}: Total={row[1]}, Migrados={row[2]}, Pendientes={row[3]}, Errores={row[4]}")
        else:
            print("  No se encontraron registros del libro 209 en cf_diariol")
    except Exception as e:
        print(f"  Error: {e}")
    
    print("\n=== VERIFICAR LIBRO 209 EN CABECERA (cf_diario) ===")
    try:
        result = conn.execute(text("""
            SELECT subcategoria_id, COUNT(*) as total,
                   COUNT(CASE WHEN estado = 'MIGRADO' THEN 1 END) as migrados,
                   COUNT(CASE WHEN estado = 'PENDIENTE' THEN 1 END) as pendientes,
                   COUNT(CASE WHEN estado = 'ERROR' THEN 1 END) as errores
            FROM cf_diario
            WHERE cglosa LIKE '%209%' OR ccoddoc = '209'
            GROUP BY subcategoria_id
        """))
        rows = list(result)
        if rows:
            for row in rows:
                print(f"  Subcategoría {row[0]}: Total={row[1]}, Migrados={row[2]}, Pendientes={row[3]}, Errores={row[4]}")
        else:
            print("  No se encontraron registros del libro 209 en cf_diario")
    except Exception as e:
        print(f"  Error: {e}")
    
    print("\n=== REGISTROS CON ERROR EN STAGING ===")
    try:
        result = conn.execute(text("""
            SELECT nasiento, nidlin, ccodcue, ndebe, nhaber, cglosa, estado
            FROM cf_diariol
            WHERE estado = 'ERROR'
            LIMIT 10
        """))
        rows = list(result)
        if rows:
            for row in rows:
                print(f"  Asiento {row[0]} Lín {row[1]}: Cuenta={row[2]}, Debe={row[3]}, Haber={row[4]}, Glosa={row[5][:50]}...")
        else:
            print("  No hay registros con estado ERROR")
    except Exception as e:
        print(f"  Error: {e}")
    
    conn.close()

if __name__ == "__main__":
    check_book_209()
