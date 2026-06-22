import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ["POSTGRES_CONNECTION_STRING"] = "postgresql://postgres:postgres@localhost:5434/migconta_db"

def main():
    engine = create_engine(os.environ["POSTGRES_CONNECTION_STRING"])
    Session = sessionmaker(bind=engine)
    db = Session()
    
    print("--- Applying database fixes ---")
    
    # 1. Fix application condition for Line 346 (Line 2 of subcat 76)
    db.execute(text("""
        UPDATE mapeo_lineas_asiento 
        SET condicion_aplicacion = 'Y(CodCia="005", O(C_TipoDoc="00"))'
        WHERE id = 346
    """))
    print("Fixed condition for Line 346.")
    
    # 2. Fix pares_redondeo for subcategory 76
    import json
    fixed_pairs = [{'debe': 'ndebe', 'haber': 'nhaber'}, {'debe': 'ndebes', 'haber': 'nhabers'}, {'debe': 'ndebed', 'haber': 'nhaberd'}]
    db.execute(text("""
        UPDATE mapeo_subcategorias 
        SET pares_redondeo = :pairs
        WHERE id = 76
    """), {"pairs": json.dumps(fixed_pairs)})
    print("Fixed pares_redondeo for subcategory 76.")
    
    db.commit()
    
    # Run generation
    from backend.app.api.endpoints.mapeo import generate_to_cf_diariol
    
    body = {
        "company_id": 4,
        "subcategoria_id": 76,
        "clear_previous": True,
        "is_realtime": False
    }
    
    print("\nRunning generate_to_cf_diariol after fixes...")
    res = generate_to_cf_diariol(body, db)
    print("Result:", res)
    
    # Query generated details
    lote_id = res.get("lote_id")
    if lote_id:
        print(f"\nQuerying generated detail rows for Lote {lote_id}:")
        with engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT id, nasiento, nidlin, ccodcue, ndebe, nhaber, ndebes, nhabers, ndebed, nhaberd, cglosa 
                FROM cf_diariol 
                WHERE lote_id = :lote 
                ORDER BY nidlin
            """), {"lote": lote_id}).mappings().all()
            for r in rows:
                print(dict(r))

if __name__ == "__main__":
    main()
