import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.database import DestSessionLocal
from backend.app.models.models import MapeoSubcategoria, AsientoCorrelativo
from sqlalchemy import create_engine, text

client = TestClient(app)

def run_test():
    # Let's inspect some records first to choose a target
    db = DestSessionLocal()
    try:
        # Find a subcategory and period that has records in cf_diariol
        sql = text("""
            SELECT company_id, subcategoria_id, cper, cmes, COUNT(*) 
            FROM cf_diariol 
            GROUP BY company_id, subcategoria_id, cper, cmes 
            LIMIT 5
        """)
        rows = db.execute(sql).fetchall()
        if not rows:
            print("No records found in cf_diariol to clear.")
            return

        for r in rows:
            print(f"Candidate: Company={r[0]}, Subcategory={r[1]}, Period={r[2]}, Month={r[3]}, Count={r[4]}")
        
        # Pick the first candidate
        company_id, subcat_id, cper, cmes, count = rows[0]
        print(f"\nTesting clear-period-staging for Company={company_id}, Subcategory={subcat_id}, Period={cper}, Month={cmes}")

        # Let's call the endpoint
        payload = {
            "company_id": int(company_id),
            "subcategoria_id": int(subcat_id),
            "periodo": str(cper),
            "mes": str(cmes)
        }
        
        response = client.post("/api/v1/etl/clear-period-staging", json=payload)
        print("Status Code:", response.status_code)
        print("JSON Response:", response.json())

        # Verify that records are cleared
        sql_check = text("""
            SELECT COUNT(*) FROM cf_diariol 
            WHERE company_id = :cid AND subcategoria_id = :sid AND cper = :cper AND cmes = :cmes
        """)
        c = db.execute(sql_check, {"cid": company_id, "sid": subcat_id, "cper": cper, "cmes": cmes}).scalar()
        print(f"Remaining staging rows: {c}")

        # Check correlative reset
        corr = db.query(AsientoCorrelativo).filter(
            AsientoCorrelativo.company_id == company_id,
            AsientoCorrelativo.subcategoria_id == subcat_id,
            AsientoCorrelativo.periodo == cper,
            AsientoCorrelativo.mes == cmes
        ).first()
        if corr:
            print(f"Correlativo: inicial={corr.asiento_inicial}, actual={corr.asiento_actual}")
        else:
            print("No specific period correlative exists (might be global).")

        # Check last generated control value
        sub = db.query(MapeoSubcategoria).filter(MapeoSubcategoria.id == subcat_id).first()
        print(f"Subcategory control column: {sub.control_column_origen}, last_val={sub.last_generated_control_value}")

    except Exception as e:
        print("Error during test:", e)
    finally:
        db.close()

if __name__ == "__main__":
    run_test()
