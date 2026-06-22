from backend.app.core.database import DestSessionLocal
from sqlalchemy import text

db = DestSessionLocal()
try:
    sql = """
        SELECT subcategoria_id, estado, COUNT(*) 
        FROM cf_diariol 
        WHERE company_id = 4 
        GROUP BY subcategoria_id, estado
    """
    rows = db.execute(text(sql)).fetchall()
    print("Staging rows for company 4:")
    for r in rows:
        print(f"Subcat ID: {r[0]} | Estado: {r[1]} | Count: {r[2]}")
finally:
    db.close()
