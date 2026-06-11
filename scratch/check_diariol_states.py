import sys
sys.path.append('c:/SistemaMigConta')
from backend.app.core.database import dest_engine
from sqlalchemy import text

with dest_engine.connect() as conn:
    # Contar registros agrupados por estado para subcategoría 200 o en general
    res = conn.execute(text("SELECT estado, count(*) FROM cf_diariol GROUP BY estado"))
    print("cf_diariol states:")
    for row in res:
        print(f"  Estado: '{row[0]}' | Count: {row[1]}")
        
    res_h = conn.execute(text("SELECT estado, count(*) FROM cf_diario GROUP BY estado"))
    print("\ncf_diario states:")
    for row in res_h:
        print(f"  Estado: '{row[0]}' | Count: {row[1]}")
