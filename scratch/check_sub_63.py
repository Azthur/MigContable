from backend.app.core.database import DestSessionLocal
from sqlalchemy import text

db = DestSessionLocal()
try:
    sql = """
        SELECT idcontrol, estado, nasiento, cmonxacre, ccodcue, ndebe, nhaber, cglosa 
        FROM cf_diariol 
        WHERE company_id = 4 AND subcategoria_id = 63
    """
    rows = db.execute(text(sql)).fetchall()
    print("Subcat 63 rows in cf_diariol:")
    for r in rows:
        print(f"idcontrol: {r[0]} | Estado: {r[1]} | Asiento: {r[2]} | Cue: {r[4]} | Debe: {r[5]} | Haber: {r[6]} | Glosa: {r[7]}")
finally:
    db.close()
