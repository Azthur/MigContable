import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.core.database import DestSessionLocal
from sqlalchemy import text

db = DestSessionLocal()
try:
    res = db.execute(text("SELECT estado, COUNT(*) FROM cf_diario WHERE company_id = 4 AND subcategoria_id = 63 GROUP BY estado")).fetchall()
    print("Staging Headers (cf_diario) for Company 4 and Subcat 63:")
    for row in res:
        print(f"  Estado: {row[0]}, Count: {row[1]}")
        
    res_l = db.execute(text("SELECT estado, COUNT(*) FROM cf_diariol WHERE company_id = 4 AND subcategoria_id = 63 GROUP BY estado")).fetchall()
    print("\nStaging Details (cf_diariol) for Company 4 and Subcat 63:")
    for row in res_l:
        print(f"  Estado: {row[0]}, Count: {row[1]}")
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
