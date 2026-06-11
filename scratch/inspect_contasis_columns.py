import sys
sys.path.append('c:/SistemaMigConta')
from backend.app.core.database import DestSessionLocal
from backend.app.models.models import FinalDestConnection
from backend.app.services.connection_manager import ConnectionManager
from sqlalchemy import text, inspect

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
        
        # Inspeccionar columnas
        insp = inspect(final_engine)
        print("cf_diario columns:")
        print([c['name'] for c in insp.get_columns("cf_diario")])
        
        print("\ncf_diariol columns:")
        print([c['name'] for c in insp.get_columns("cf_diariol")])
        
        with final_engine.connect() as conn:
            # Seleccionar las primeras 10 filas de cf_diario para 2026-06
            res_h = conn.execute(text("SELECT nasiento, cper, cmes, ccodori FROM cf_diario WHERE cper = '2026' AND cmes = '06' LIMIT 10"))
            print("\ncf_diario sample rows:")
            h_seats = []
            for r in res_h:
                print(f"  nasiento: {r[0]} ({type(r[0])}) | cper: {r[1]} | cmes: {r[2]} | ccodori: {r[3]}")
                h_seats.append(r[0])
                
            # Seleccionar las primeras 10 filas de cf_diariol para 2026-06
            res_d = conn.execute(text("SELECT nasiento, nidlin, cper, cmes, ccodori FROM cf_diariol WHERE cper = '2026' AND cmes = '06' LIMIT 10"))
            print("\ncf_diariol sample rows:")
            for r in res_d:
                print(f"  nasiento: {r[0]} ({type(r[0])}) | nidlin: {r[1]} ({type(r[1])}) | cper: {r[2]} | cmes: {r[3]} | ccodori: {r[4]}")
                
            # Ver si hay algún nasiento de cf_diario que coincida exactamente en cf_diariol
            if h_seats:
                print(f"\nChecking matches in cf_diariol for nasientos from cf_diario {h_seats}:")
                for seat in h_seats:
                    # Contar coincidencias exactas
                    res_match = conn.execute(text("SELECT count(*) FROM cf_diariol WHERE nasiento = :seat AND cper = '2026' AND cmes = '06'"), {"seat": seat})
                    count = res_match.scalar()
                    print(f"  Match for nasiento {seat} (type {type(seat)}): {count}")
                    
                    # Si no hay coincidencia, intentar buscarlo casteado a float o int
                    if count == 0:
                        try:
                            alt_seat = float(seat)
                            res_match_f = conn.execute(text("SELECT count(*) FROM cf_diariol WHERE nasiento = :seat AND cper = '2026' AND cmes = '06'"), {"seat": alt_seat})
                            print(f"    As float {alt_seat}: {res_match_f.scalar()}")
                        except:
                            pass
                            
                        try:
                            alt_seat_i = int(float(seat))
                            res_match_i = conn.execute(text("SELECT count(*) FROM cf_diariol WHERE nasiento = :seat AND cper = '2026' AND cmes = '06'"), {"seat": alt_seat_i})
                            print(f"    As int {alt_seat_i}: {res_match_i.scalar()}")
                        except:
                            pass
finally:
    db.close()
