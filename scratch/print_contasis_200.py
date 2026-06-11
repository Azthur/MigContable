import sys
sys.path.append('c:/SistemaMigConta')
from backend.app.core.database import DestSessionLocal
from backend.app.models.models import FinalDestConnection
from backend.app.services.connection_manager import ConnectionManager
from sqlalchemy import text

db = DestSessionLocal()
try:
    final_conn = db.query(FinalDestConnection).filter(
        FinalDestConnection.company_id == 1,
        FinalDestConnection.is_active == True
    ).first()
    
    if final_conn:
        conn_data = {
            "host": final_conn.host, "port": final_conn.port,
            "database_name": final_conn.database_name,
            "username": final_conn.username, "password": final_conn.password
        }
        final_engine = ConnectionManager.get_dest_engine(conn_data)
        
        with final_engine.connect() as conn:
            # 1. Cabeceras en Contasis
            res_h = conn.execute(text("SELECT nasiento, cper, cmes, ccodori FROM cf_diario WHERE ccodori = '200' AND cper = '2026' AND cmes = '06' ORDER BY nasiento LIMIT 10")).fetchall()
            print("Contasis cf_diario (headers) for ccodori='200' in 2026-06:")
            for r in res_h:
                print(f"  nasiento: {r[0]} | cper: {r[1]} | cmes: {r[2]} | ccodori: {r[3]}")
                
            # 2. Detalles en Contasis
            res_d = conn.execute(text("SELECT nasiento, cper, cmes, ccodori, nidlin, ccodcue, ndebe, nhaber FROM cf_diariol WHERE ccodori = '200' AND cper = '2026' AND cmes = '06' ORDER BY nasiento, nidlin LIMIT 15")).fetchall()
            print("\nContasis cf_diariol (details) for ccodori='200' in 2026-06:")
            for r in res_d:
                print(f"  nasiento: {r[0]} | cper: {r[1]} | cmes: {r[2]} | ccodori: {r[3]} | lin: {r[4]} | cta: {r[5]} | debe: {r[6]} | haber: {r[7]}")
finally:
    db.close()
