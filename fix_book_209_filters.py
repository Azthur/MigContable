#!/usr/bin/env python3
"""Script para corregir los filtros del libro 209."""
import sys
sys.path.insert(0, '/app')

from backend.app.core.database import dest_engine
from sqlalchemy import text
import json

def fix_book_209_filters():
    conn = dest_engine.connect()
    
    # Definir las subcategorías del libro 209 y sus filtros corregidos
    fixes = [
        {
            "id": 80,
            "nombre": "209-Planilla de Movilidad - YLV Industrias",
            "mes": "06",
            "filter_rules": [
                {"column": "Fecha", "operator": ">=", "value": "2026-06-01", "value2": ""},
                {"column": "Fecha", "operator": "<", "value": "2026-07-01", "value2": ""}
            ]
        },
        {
            "id": 81,
            "nombre": "209-Planilla de Movilidad - YLV Nature", 
            "mes": "07",
            "filter_rules": [
                {"column": "Fecha", "operator": ">=", "value": "2026-07-01", "value2": ""},
                {"column": "Fecha", "operator": "<", "value": "2026-08-01", "value2": ""}
            ]
        },
        {
            "id": 82,
            "nombre": "209-Planilla de Movilidad - YLV Corpo",
            "mes": "06", 
            "filter_rules": [
                {"column": "Fecha", "operator": ">=", "value": "2026-06-01", "value2": ""},
                {"column": "Fecha", "operator": "<", "value": "2026-07-01", "value2": ""}
            ]
        },
        {
            "id": 83,
            "nombre": "209-Planilla de Movilidad - YLV Botica",
            "mes": "07",
            "filter_rules": [
                {"column": "Fecha", "operator": ">=", "value": "2026-07-01", "value2": ""},
                {"column": "Fecha", "operator": "<", "value": "2026-08-01", "value2": ""}
            ]
        },
        {
            "id": 116,
            "nombre": "209-Planilla de Movilidad - YLV Grupo",
            "mes": "06",
            "filter_rules": [
                {"column": "Fecha", "operator": ">=", "value": "2026-06-01", "value2": ""},
                {"column": "Fecha", "operator": "<", "value": "2026-07-01", "value2": ""}
            ]
        }
    ]
    
    print("=== ACTUALIZANDO FILTROS DEL LIBRO 209 ===")
    
    for fix in fixes:
        print(f"\nSubcategoría {fix['id']}: {fix['nombre']}")
        print(f"  Nuevo filtro: Fecha >= 2026-{fix['mes']}-01 AND Fecha < 2026-{int(fix['mes'])+1:02d}-01")
        
        # Convertir filter_rules a JSON string
        filter_json = json.dumps(fix['filter_rules'])
        
        # Actualizar en la base de datos
        result = conn.execute(text("""
            UPDATE mapeo_subcategorias 
            SET filter_rules = :filter_rules
            WHERE id = :id
        """), {"filter_rules": filter_json, "id": fix['id']})
        
        print(f"  Filas actualizadas: {result.rowcount}")
    
    # Commit changes
    conn.commit()
    
    print("\n=== VERIFICACIÓN ===")
    result = conn.execute(text("""
        SELECT id, nombre, filter_rules
        FROM mapeo_subcategorias 
        WHERE nombre LIKE '%209%'
        ORDER BY id
    """))
    
    for row in result:
        print(f"\nID: {row[0]} | {row[1]}")
        print(f"  Filter rules: {row[2]}")
    
    conn.close()

if __name__ == "__main__":
    fix_book_209_filters()
