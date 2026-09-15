#!/usr/bin/env python3
"""Script para investigar el asiento huérfano 2026-07-209-1."""
import sys
sys.path.insert(0, '/app')

import logging
logging.disable(logging.CRITICAL)

from backend.app.core.database import get_dest_db
from sqlalchemy import text

def check_asiento_huerfano():
    db = next(get_dest_db())
    
    try:
        print("=== INVESTIGANDO ASIENTO HUÉRFANO 2026-07-209-1 ===")
        
        # Buscar líneas del asiento en staging
        result = db.execute(text("""
            SELECT cper, cmes, ccodori, nasiento, nidlin, ccodcue, ndebe, nhaber, estado
            FROM cf_diariol
            WHERE subcategoria_id = 116
            AND cper = '2026'
            AND cmes = '07'
            AND ccodori = '209'
            AND nasiento = 1
        """))
        
        print("Líneas del asiento en staging:")
        for row in result:
            print(f"  nidlin: {row[4]} | ccodcue: {row[5]} | ndebe: {row[6]} | nhaber: {row[7]} | estado: {row[8]}")
        
        # Buscar cabecera del asiento en staging
        result = db.execute(text("""
            SELECT cper, cmes, ccodori, nasiento, estado
            FROM cf_diario
            WHERE subcategoria_id = 116
            AND cper = '2026'
            AND cmes = '07'
            AND ccodori = '209'
            AND nasiento = 1
        """))
        
        print("\nCabecera del asiento en staging:")
        has_cabecera = False
        for row in result:
            has_cabecera = True
            print(f"  cper: {row[0]} | cmes: {row[1]} | ccodori: {row[2]} | nasiento: {row[3]} | estado: {row[4]}")
        
        if not has_cabecera:
            print("  No hay cabecera en staging")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_asiento_huerfano()
