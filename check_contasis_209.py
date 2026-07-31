#!/usr/bin/env python3
"""Script para verificar el libro 209 en Contasis."""
import sys
sys.path.insert(0, '/app')

from backend.app.core.database import get_dest_db
from backend.app.models.models import FinalDestConnection, Company
from backend.app.services.connection_manager import ConnectionManager
from sqlalchemy import text

def check_contasis_209():
    db = next(get_dest_db())
    
    try:
        # Get company 5 (YELAVE NATURE S.A.C.)
        company = db.query(Company).filter(Company.id == 5).first()
        print(f"=== EMPRESA: {company.name if company else 'No encontrada'} ===")
        
        # Get final destination connection
        final_conn = db.query(FinalDestConnection).filter(
            FinalDestConnection.company_id == 5,
            FinalDestConnection.is_active == True
        ).first()
        
        if not final_conn:
            print("ERROR: No hay conexión destino final configurada")
            return
            
        print(f"Host: {final_conn.host}:{final_conn.port}")
        print(f"Base de datos: {final_conn.database_name}")
        
        # Connect to Contasis
        conn_data = {
            "host": final_conn.host,
            "port": final_conn.port,
            "database_name": final_conn.database_name,
            "username": final_conn.username,
            "password": final_conn.password
        }
        final_engine = ConnectionManager.get_dest_engine(conn_data)
        conn = final_engine.connect()
        
        print("\n=== TABLAS EN CONTASIS ===")
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE 'cf_%'
            ORDER BY table_name
        """))
        for row in result:
            print(f"  - {row[0]}")
        
        print("\n=== VERIFICAR LIBRO 209 EN cf_diariol ===")
        result = conn.execute(text("""
            SELECT ccodori, COUNT(*) as total,
                   COUNT(CASE WHEN cglosa LIKE '%209%' THEN 1 END) as libro_209,
                   COUNT(CASE WHEN ccoddoc = '209' THEN 1 END) as doc_209
            FROM cf_diariol
            WHERE cper = '2026'
            GROUP BY ccodori
            ORDER BY total DESC
            LIMIT 10
        """))
        for row in result:
            print(f"  Origen {row[0]}: Total={row[1]}, Libro 209={row[2]}, Doc 209={row[3]}")
        
        print("\n=== VERIFICAR SUBCATEGORÍA 35 EN STAGING ===")
        # Check what subcategory 35 is
        result = conn.execute(text("""
            SELECT DISTINCT subcategoria_id, COUNT(*) as total,
                   COUNT(CASE WHEN estado = 'MIGRADO' THEN 1 END) as migrados,
                   COUNT(CASE WHEN estado IS NULL THEN 1 END) as sin_estado,
                   COUNT(CASE WHEN estado NOT IN ('MIGRADO', 'PENDIENTE', 'ERROR') AND estado IS NOT NULL THEN 1 END) as otros_estados
            FROM cf_diariol
            WHERE subcategoria_id = 35
            GROUP BY subcategoria_id
        """))
        for row in result:
            print(f"  Subcategoría {row[0]}: Total={row[1]}, Migrados={row[2]}, Sin estado={row[3]}, Otros estados={row[4]}")
        
        conn.close()
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_contasis_209()
