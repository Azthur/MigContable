#!/usr/bin/env python3
"""Script para verificar qué cuentas existen en cf_plan para el período 2026."""
import sys
sys.path.insert(0, '/app')

import logging
logging.disable(logging.CRITICAL)

from backend.app.core.database import get_dest_db
from sqlalchemy import text

def check_cf_plan_accounts():
    db = next(get_dest_db())
    
    try:
        print("=== VERIFICANDO CUENTAS EN CF_PLAN PARA PERÍODO 2026 ===")
        
        # Verificar si la cuenta 6556179 existe
        result = db.execute(text("""
            SELECT cper, ccodcue, cdes
            FROM cf_plan
            WHERE cper = '2026' AND ccodcue = '6556179'
        """))
        
        account_6556179 = result.fetchall()
        if account_6556179:
            print("Cuenta 6556179 encontrada:")
            for row in account_6556179:
                print(f"  cper: {row[0]} | ccodcue: {row[1]} | cdes: {row[2]}")
        else:
            print("Cuenta 6556179 NO encontrada en cf_plan para período 2026")
        
        # Verificar si la cuenta 469901 existe
        result = db.execute(text("""
            SELECT cper, ccodcue, cdes
            FROM cf_plan
            WHERE cper = '2026' AND ccodcue = '469901'
        """))
        
        account_469901 = result.fetchall()
        if account_469901:
            print("\nCuenta 469901 encontrada:")
            for row in account_469901:
                print(f"  cper: {row[0]} | ccodcue: {row[1]} | cdes: {row[2]}")
        else:
            print("\nCuenta 469901 NO encontrada en cf_plan para período 2026")
        
        # Listar todas las cuentas disponibles para período 2026
        result = db.execute(text("""
            SELECT cper, ccodcue, cdes
            FROM cf_plan
            WHERE cper = '2026'
            ORDER BY ccodcue
            LIMIT 20
        """))
        
        print("\nPrimeras 20 cuentas disponibles en cf_plan para período 2026:")
        for row in result:
            print(f"  cper: {row[0]} | ccodcue: {row[1]} | cdes: {row[2]}")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_cf_plan_accounts()
