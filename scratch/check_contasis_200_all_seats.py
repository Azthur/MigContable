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
            # Obtener todas las cabeceras para 2026-06 y ccodori = '200'
            res_h = conn.execute(text("SELECT DISTINCT nasiento FROM cf_diario WHERE ccodori = '200' AND cper = '2026' AND cmes = '06' ORDER BY nasiento")).fetchall()
            headers_seats = [float(r[0]) for r in res_h]
            
            # Obtener todos los detalles para 2026-06 y ccodori = '200'
            res_d = conn.execute(text("SELECT DISTINCT nasiento FROM cf_diariol WHERE ccodori = '200' AND cper = '2026' AND cmes = '06' ORDER BY nasiento")).fetchall()
            details_seats = [float(r[0]) for r in res_d]
            
            print(f"Total unique seat numbers in cf_diario (headers): {len(headers_seats)}")
            print(f"Headers seats: {headers_seats}")
            
            print(f"\nTotal unique seat numbers in cf_diariol (details): {len(details_seats)}")
            print(f"Details seats: {details_seats}")
            
            # Ver la diferencia
            diff_h_d = set(headers_seats) - set(details_seats)
            print(f"\nSeats in headers that have NO matching details: {sorted(list(diff_h_d))}")
            
            diff_d_h = set(details_seats) - set(headers_seats)
            print(f"Seats in details that have NO matching headers: {sorted(list(diff_d_h))}")
finally:
    db.close()
