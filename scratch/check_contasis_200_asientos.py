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
            # 1. Cabeceras con ccodori = '200' en 2026-06
            res_h = conn.execute(text("SELECT count(*) FROM cf_diario WHERE ccodori = '200' AND cper = '2026' AND cmes = '06'"))
            print("Headers with ccodori='200' in 2026-06:", res_h.scalar())
            
            # 2. Detalles con ccodori = '200' en 2026-06
            res_d = conn.execute(text("SELECT count(*) FROM cf_diariol WHERE ccodori = '200' AND cper = '2026' AND cmes = '06'"))
            print("Details with ccodori='200' in 2026-06:", res_d.scalar())
            
            # Si hay cabeceras, mostrar los primeros 5 nasiento
            if res_h.scalar() > 0:
                res_h_rows = conn.execute(text("SELECT nasiento, cper, cmes, ccodori FROM cf_diario WHERE ccodori = '200' AND cper = '2026' AND cmes = '06' LIMIT 5"))
                print("\nHeaders in Contasis:")
                h_seats = []
                for r in res_h_rows:
                    print(f"  nasiento: {r[0]} ({type(r[0])})")
                    h_seats.append(r[0])
                
                # Ver si estos nasientos existen en cf_diariol
                print("\nChecking details in cf_diariol for those specific nasientos:")
                for seat in h_seats:
                    res_spec = conn.execute(text("SELECT count(*) FROM cf_diariol WHERE nasiento = :seat AND ccodori = '200' AND cper = '2026' AND cmes = '06'"), {"seat": seat})
                    print(f"  Details for nasiento {seat}: {res_spec.scalar()}")
                    
                    # Vamos a listar un detalle de ejemplo si los hay
                    if res_spec.scalar() > 0:
                        res_det = conn.execute(text("SELECT nasiento, nidlin, ccodcue, ndebe, nhaber FROM cf_diariol WHERE nasiento = :seat AND ccodori = '200' AND cper = '2026' AND cmes = '06' LIMIT 2"), {"seat": seat})
                        for d in res_det:
                            print(f"    Line: {d[1]} | Account: {d[2]} | Debe: {d[3]} | Haber: {d[4]}")
finally:
    db.close()
