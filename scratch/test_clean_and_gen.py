import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.core.database import DestSessionLocal
from backend.app.api.endpoints.mapeo import generate_to_cf_diariol
from sqlalchemy import text

db = DestSessionLocal()

try:
    print("--- BEFORE RE-GENERATION ---")
    h_count = db.execute(text("SELECT estado, COUNT(*) FROM cf_diario WHERE company_id = 4 GROUP BY estado")).fetchall()
    print("Staging Headers (cf_diario):")
    for r in h_count:
        print(f"  Estado: {r[0]}, Count: {r[1]}")
        
    d_count = db.execute(text("SELECT estado, COUNT(*) FROM cf_diariol WHERE company_id = 4 AND subcategoria_id = 63 GROUP BY estado")).fetchall()
    print("Staging Details (cf_diariol) for subcat 63:")
    for r in d_count:
        print(f"  Estado: {r[0]}, Count: {r[1]}")
        
    print("\n--- TRIGGERING GENERATION ---")
    body = {"company_id": 4, "subcategoria_id": 63, "clear_previous": True}
    res = generate_to_cf_diariol(body, db)
    print("API Response:")
    print(res)
    
    print("\n--- AFTER RE-GENERATION ---")
    h_count = db.execute(text("SELECT estado, COUNT(*) FROM cf_diario WHERE company_id = 4 GROUP BY estado")).fetchall()
    print("Staging Headers (cf_diario):")
    for r in h_count:
        print(f"  Estado: {r[0]}, Count: {r[1]}")
        
    d_count = db.execute(text("SELECT estado, COUNT(*) FROM cf_diariol WHERE company_id = 4 AND subcategoria_id = 63 GROUP BY estado")).fetchall()
    print("Staging Details (cf_diariol) for subcat 63:")
    for r in d_count:
        print(f"  Estado: {r[0]}, Count: {r[1]}")
        
    # Check if there are any orphan headers in cf_diario (headers with NO details in cf_diariol) for the ones generated in this run
    orphans = db.execute(text("""
        SELECT h.nasiento, h.estado, h.cper, h.cmes, h.ccodori
        FROM cf_diario h
        LEFT JOIN cf_diariol d ON h.nasiento = d.nasiento AND h.company_id = d.company_id
        WHERE h.company_id = 4 AND h.lote_id = :lote_id AND d.nasiento IS NULL
    """), {"lote_id": res.get("lote_id")}).fetchall()
    print(f"\nOrphan Headers from this run (lote_id = {res.get('lote_id')}): {len(orphans)}")
    for row in orphans:
        print(f"  Nasiento: {row[0]}, Estado: {row[1]}, Periodo: {row[2]}, Mes: {row[3]}, Origen: {row[4]}")
        
except Exception as e:
    print(f"Error during test: {e}")
finally:
    db.close()
