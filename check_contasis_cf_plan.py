#!/usr/bin/env python3
"""Script para verificar qué cuentas existen en cf_plan en la base de datos de Contasis."""
import sys
sys.path.insert(0, '/app')

import logging
logging.disable(logging.CRITICAL)

from backend.app.core.database import get_dest_db
from backend.app.models.models import FinalDestConnection
from backend.app.services.connection_manager import ConnectionManager
from sqlalchemy import text

def check_contasis_cf_plan():
    db = next(get_dest_db())
    
    try:
        print("=== VERIFICANDO CUENTAS EN CF_PLAN EN CONTASIS ===")
        
        # Obtener conexión a Contasis
        final_conn = db.query(FinalDestConnection).filter(
            FinalDestConnection.company_id == 5,  # YLV Nature
            FinalDestConnection.is_active == True
        ).first()
        
        if not final_conn:
            print("No hay conexión Contasis configurada para company_id 5")
            return
        
        conn_data = {
            "host": final_conn.host,
            "port": final_conn.port,
            "database_name": final_conn.database_name,
            "username": final_conn.username,
            "password": final_conn.password
        }
        
        contasis_engine = ConnectionManager.get_dest_engine(conn_data)
        
        with contasis_engine.connect() as conn:
            # Verificar esquema de cf_plan
            result = conn.execute(text("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'cf_plan'
                ORDER BY ordinal_position
            """))
            
            print("Esquema de cf_plan:")
            for row in result:
                print(f"  {row[0]}: {row[1]}")
            
            # Verificar si la cuenta 6556179 existe
            result = conn.execute(text("""
                SELECT cper, ccodcue
                FROM cf_plan
                WHERE cper = '2026' AND ccodcue = '6556179'
            """))
            
            account_6556179 = result.fetchall()
            if account_6556179:
                print("\nCuenta 6556179 encontrada:")
                for row in account_6556179:
                    print(f"  cper: {row[0]} | ccodcue: {row[1]}")
            else:
                print("\nCuenta 6556179 NO encontrada en cf_plan para período 2026")
            
            # Verificar si la cuenta 469901 existe
            result = conn.execute(text("""
                SELECT cper, ccodcue
                FROM cf_plan
                WHERE cper = '2026' AND ccodcue = '469901'
            """))
            
            account_469901 = result.fetchall()
            if account_469901:
                print("\nCuenta 469901 encontrada:")
                for row in account_469901:
                    print(f"  cper: {row[0]} | ccodcue: {row[1]}")
            else:
                print("\nCuenta 469901 NO encontrada en cf_plan para período 2026")
            
            # Listar todas las cuentas disponibles para período 2026
            result = conn.execute(text("""
                SELECT cper, ccodcue, cdescue
                FROM cf_plan
                WHERE cper = '2026'
                ORDER BY ccodcue
                LIMIT 20
            """))
            
            print("\nPrimeras 20 cuentas disponibles en cf_plan para período 2026:")
            for row in result:
                print(f"  cper: {row[0]} | ccodcue: {row[1]} | cdescue: {row[2]}")
            
            # Buscar cuentas que empiecen con 6 (gastos)
            result = conn.execute(text("""
                SELECT cper, ccodcue, cdescue
                FROM cf_plan
                WHERE cper = '2026' AND ccodcue LIKE '6%'
                ORDER BY ccodcue
                LIMIT 20
            """))
            
            print("\nCuentas que empiezan con 6 (gastos) para período 2026:")
            for row in result:
                print(f"  cper: {row[0]} | ccodcue: {row[1]} | cdescue: {row[2]}")
            
            # Buscar cuentas relacionadas con gastos de personal/viáticos
            result = conn.execute(text("""
                SELECT cper, ccodcue, cdescue
                FROM cf_plan
                WHERE cper = '2026' AND (cdescue ILIKE '%VIATIC%' OR cdescue ILIKE '%MOVILIDAD%' OR cdescue ILIKE '%REMU%' OR cdescue ILIKE '%SUELDO%' OR cdescue ILIKE '%PERSONAL%')
                ORDER BY ccodcue
            """))
            
            print("\nCuentas relacionadas con gastos de personal/viáticos:")
            for row in result:
                print(f"  cper: {row[0]} | ccodcue: {row[1]} | cdescue: {row[2]}")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_contasis_cf_plan()
