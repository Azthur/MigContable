#!/usr/bin/env python3
"""Script para buscar tablas de configuración de cuentas."""
import sys
sys.path.insert(0, '/app')

import logging
logging.disable(logging.CRITICAL)

from backend.app.core.database import get_dest_db
from sqlalchemy import text

def check_config_cuentas():
    db = next(get_dest_db())
    
    try:
        print("=== BUSCANDO TABLAS DE CONFIGURACIÓN DE CUENTAS ===")
        
        # Buscar tablas que tengan "cuenta" o "config" en el nombre
        result = db.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            AND (table_name ILIKE '%cuenta%' OR table_name ILIKE '%config%' OR table_name ILIKE '%mapeo%')
            ORDER BY table_name
        """))
        
        print("Tablas encontradas:")
        for row in result:
            print(f"  {row[0]}")
        
        # Revisar estructura de mapeo_subcategorias
        print("\n=== ESTRUCTURA DE MAPEO_SUBCATEGORÍAS ===")
        result = db.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'mapeo_subcategorias'
            ORDER BY ordinal_position
        """))
        
        for row in result:
            print(f"  {row[0]}: {row[1]}")
        
        # Revisar si hay campos de cuentas en mapeo_subcategorias
        print("\n=== CAMPOS DE CUENTAS EN MAPEO_SUBCATEGORÍAS ===")
        result = db.execute(text("""
            SELECT id, nombre, ccodcue_debe, ccodcue_haber, ccodcue_debe2, ccodcue_haber2
            FROM mapeo_subcategorias
            WHERE id IN (80, 81, 82, 83, 116)
        """))
        
        for row in result:
            print(f"  ID {row[0]} ({row[1]}):")
            print(f"    ccodcue_debe: {row[2]}")
            print(f"    ccodcue_haber: {row[3]}")
            print(f"    ccodcue_debe2: {row[4]}")
            print(f"    ccodcue_haber2: {row[5]}")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_config_cuentas()
