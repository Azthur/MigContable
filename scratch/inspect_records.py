import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.core.database import DestSessionLocal
from sqlalchemy import text

db = DestSessionLocal()

try:
    # Query count of staging headers
    h_res = db.execute(text("SELECT estado, COUNT(*) FROM cf_diario WHERE company_id = 4 AND lote_id IS NOT NULL GROUP BY estado")).fetchall()
    print("Staging Headers (cf_diario) for Company 4:")
    for row in h_res:
        print(f"  Estado: {row[0]}, Count: {row[1]}")
    
    # Query count of staging details for subcategory 63
    d_res = db.execute(text("SELECT estado, COUNT(*) FROM cf_diariol WHERE company_id = 4 AND subcategoria_id = 63 GROUP BY estado")).fetchall()
    print("\nStaging Details (cf_diariol) for Company 4, Subcat 63:")
    for row in d_res:
        print(f"  Estado: {row[0]}, Count: {row[1]}")
        
    # Check if there are staging details for OTHER subcategories
    d_other = db.execute(text("SELECT subcategoria_id, estado, COUNT(*) FROM cf_diariol WHERE company_id = 4 AND subcategoria_id != 63 GROUP BY subcategoria_id, estado")).fetchall()
    if d_other:
        print("\nStaging Details for other subcategories:")
        for row in d_other:
            print(f"  Subcat: {row[0]}, Estado: {row[1]}, Count: {row[2]}")
            
    # Check if there are orphan headers (headers in cf_diario with no details in cf_diariol)
    orphans = db.execute(text("""
        SELECT h.nasiento, h.estado, h.cper, h.cmes, h.ccodori
        FROM cf_diario h
        LEFT JOIN cf_diariol d ON h.nasiento = d.nasiento AND h.company_id = d.company_id
        WHERE h.company_id = 4 AND d.nasiento IS NULL
    """)).fetchall()
    print(f"\nOrphan Headers (in cf_diario but not in cf_diariol): {len(orphans)}")
    for row in orphans[:10]:
        print(f"  Nasiento: {row[0]}, Estado: {row[1]}, Periodo: {row[2]}, Mes: {row[3]}, Origen: {row[4]}")
        
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
