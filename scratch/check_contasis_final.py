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
            # 1. Contar cabeceras en Contasis
            res_h = conn.execute(text("SELECT count(*) FROM cf_diario WHERE cper = '2026' AND cmes = '06'"))
            print("Total headers in Contasis cf_diario for 2026-06:", res_h.scalar())
            
            # 2. Contar detalles en Contasis
            res_d = conn.execute(text("SELECT count(*) FROM cf_diariol WHERE cper = '2026' AND cmes = '06'"))
            print("Total details in Contasis cf_diariol for 2026-06:", res_d.scalar())
            
            # 3. Mostrar algunas cabeceras
            res_h_rows = conn.execute(text("SELECT nasiento, cper, cmes, ccodori, cglosa FROM cf_diario WHERE cper = '2026' AND cmes = '06' LIMIT 5"))
            print("\nSample headers in Contasis for 2026-06:")
            for r in res_h_rows:
                print(f"  Asiento: {r[0]} ({type(r[0])}) | cper: {r[1]} | cmes: {r[2]} | ccodori: {r[3]} | Glosa: {r[4]}")
                
            # 4. Mostrar algunos detalles si los hay
            res_d_rows = conn.execute(text("SELECT nasiento, nidlin, cper, cmes, ccodori, cglosa FROM cf_diariol WHERE cper = '2026' AND cmes = '06' LIMIT 5"))
            print("\nSample details in Contasis for 2026-06:")
            for r in res_d_rows:
                print(f"  Asiento: {r[0]} ({type(r[0])}) | Lin: {r[1]} | cper: {r[2]} | cmes: {r[3]} | ccodori: {r[4]} | Glosa: {r[5]}")
                
            # 5. Buscar si hay detalles con alguna otra subcategoria_id o en general para el periodo 2026-06
            res_gen_d = conn.execute(text("SELECT count(*) FROM cf_diariol WHERE cper = '2026' AND cmes = '06'"))
            print("\nTotal details in Contasis for 2026-06 (any subcat):", res_gen_d.scalar())
            
            res_gen_h = conn.execute(text("SELECT count(*) FROM cf_diario WHERE cper = '2026' AND cmes = '06'"))
            print("Total headers in Contasis for 2026-06 (any subcat):", res_gen_h.scalar())
            
            # 6. ¿Hay algún asiento específico que sí tenga detalles en cf_diariol?
            res_h_nasientos = conn.execute(text("SELECT DISTINCT nasiento FROM cf_diario WHERE cper = '2026' AND cmes = '06' LIMIT 5"))
            nasientos = [r[0] for r in res_h_nasientos]
            if nasientos:
                print(f"\nChecking details in cf_diariol for nasientos {nasientos}:")
                for nas in nasientos:
                    res_spec = conn.execute(text("SELECT count(*) FROM cf_diariol WHERE nasiento = :nas"), {"nas": nas})
                    print(f"  Details for nasiento {nas}: {res_spec.scalar()}")
                    
                    # Probemos buscarlo convirtiendo a float o string por si acaso
                    try:
                        res_spec_f = conn.execute(text("SELECT count(*) FROM cf_diariol WHERE nasiento = :nas"), {"nas": float(nas)})
                        print(f"    As float details: {res_spec_f.scalar()}")
                    except:
                        pass
finally:
    db.close()
