#!/usr/bin/env python3
"""Script para crear cabecera faltante para asiento huérfano."""
import sys
sys.path.insert(0, '/app')

import logging
logging.disable(logging.CRITICAL)

from backend.app.core.database import get_dest_db
from sqlalchemy import text

def create_cabecera_huerfana():
    db = next(get_dest_db())
    
    try:
        print("=== CREANDO CABECERA FALTANTE PARA ASIENTO 2026-07-209-1 ===")
        
        # Calcular totales del asiento
        result = db.execute(text("""
            SELECT SUM(ndebe) as total_debe, SUM(nhaber) as total_haber
            FROM cf_diariol
            WHERE subcategoria_id = 116
            AND cper = '2026'
            AND cmes = '07'
            AND ccodori = '209'
            AND nasiento = 1
        """))
        
        row = result.fetchone()
        total_debe = row[0] or 0
        total_haber = row[1] or 0
        
        print(f"Total debe: {total_debe}, Total haber: {total_haber}")
        
        # Insertar cabecera
        result = db.execute(text("""
            INSERT INTO cf_diario 
            (company_id, subcategoria_id, cper, cmes, ccodori, nasiento, ndebe, nhaber, estado, ffecasi, cmoneda, ccodusu, tregistro, ccodsu, ntcblo, ccodbas, nidreg, nidlin, chknotc, cglosa_2)
            VALUES 
            (7, 116, '2026', '07', '209', 1, :total_debe, :total_haber, '1', '2026-07-01', 'S  ', 'SISTEMAS', '2026-07-01', '05', '0', '0', '0', '0', '0', 'Planilla de Movilidad Julio 2026')
        """), {"total_debe": total_debe, "total_haber": total_haber})
        
        print(f"Cabecera insertada: {result.rowcount} filas")
        
        db.commit()
        
        print("\nVerificando cabecera creada...")
        result = db.execute(text("""
            SELECT cper, cmes, ccodori, nasiento, ndebe, nhaber, estado
            FROM cf_diario
            WHERE subcategoria_id = 116
            AND cper = '2026'
            AND cmes = '07'
            AND ccodori = '209'
            AND nasiento = 1
        """))
        
        for row in result:
            print(f"  cper: {row[0]} | cmes: {row[1]} | ccodori: {row[2]} | nasiento: {row[3]} | ndebe: {row[4]} | nhaber: {row[5]} | estado: {row[6]}")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_cabecera_huerfana()
