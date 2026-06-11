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
            # Obtener una cabecera para ccodori = '200' en 2026-06
            row_h = conn.execute(text("SELECT nasiento, cper, cmes, ccodori FROM cf_diario WHERE ccodori = '200' AND cper = '2026' AND cmes = '06' LIMIT 1")).first()
            if row_h:
                print("Contasis cf_diario Link Fields:")
                h_nasiento, h_cper, h_cmes, h_ccodori = row_h
                print(f"  nasiento: val={repr(h_nasiento)}, type={type(h_nasiento)}")
                print(f"  cper    : val={repr(h_cper)}, len={len(h_cper) if h_cper else 0}, type={type(h_cper)}")
                print(f"  cmes    : val={repr(h_cmes)}, len={len(h_cmes) if h_cmes else 0}, type={type(h_cmes)}")
                print(f"  ccodori : val={repr(h_ccodori)}, len={len(h_ccodori) if h_ccodori else 0}, type={type(h_ccodori)}")
                
                # Obtener detalles para esta misma cabecera en cf_diariol
                # Intentamos buscar haciendo match con los valores directamente
                res_d = conn.execute(
                    text("SELECT nasiento, cper, cmes, ccodori, nidlin, ccodcue, ndebe, nhaber FROM cf_diariol WHERE nasiento = :nas AND cper = :cper AND cmes = :cmes AND ccodori = :ccodori"),
                    {"nas": h_nasiento, "cper": h_cper, "cmes": h_cmes, "ccodori": h_ccodori}
                ).fetchall()
                
                print(f"\nDetails found matching these exact fields: {len(res_d)}")
                for idx, r in enumerate(res_d):
                    print(f"\n  Line {idx}:")
                    print(f"    nasiento: val={repr(r[0])}, type={type(r[0])}")
                    print(f"    cper    : val={repr(r[1])}, len={len(r[1]) if r[1] else 0}, type={type(r[1])}")
                    print(f"    cmes    : val={repr(r[2])}, len={len(r[2]) if r[2] else 0}, type={type(r[2])}")
                    print(f"    ccodori : val={repr(r[3])}, len={len(r[3]) if r[3] else 0}, type={type(r[3])}")
                    print(f"    nidlin  : val={repr(r[4])}, type={type(r[4])}")
                    print(f"    ccodcue : val={repr(r[5])}, len={len(r[5]) if r[5] else 0}, type={type(r[5])}")
                    print(f"    ndebe   : val={repr(r[6])}, type={type(r[6])}")
                    print(f"    nhaber  : val={repr(r[7])}, type={type(r[7])}")
            else:
                print("No headers found in Contasis for ccodori='200' in 2026-06.")
finally:
    db.close()
