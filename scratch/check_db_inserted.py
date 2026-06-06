import os
from sqlalchemy import create_engine, text

os.environ["POSTGRES_CONNECTION_STRING"] = "postgresql://postgres:postgres@localhost:5434/migconta_db"

def main():
    engine = create_engine(os.environ["POSTGRES_CONNECTION_STRING"])
    with engine.connect() as conn:
        # Check cf_diario count
        res_h = conn.execute(text("SELECT count(*) FROM cf_diario WHERE company_id = 4 AND subcategoria_id = 63")).scalar()
        print("Total in cf_diario (headers) for company 4, subcat 63:", res_h)
        
        # Check cf_diariol count
        res_d = conn.execute(text("SELECT count(*) FROM cf_diariol WHERE company_id = 4 AND subcategoria_id = 63")).scalar()
        print("Total in cf_diariol (details) for company 4, subcat 63:", res_d)
        
        # Sample of inserted headers
        if res_h > 0:
            print("\nSample headers:")
            rows = conn.execute(text("SELECT id, nasiento, cmes, cper, cglosa FROM cf_diario WHERE company_id = 4 AND subcategoria_id = 63 LIMIT 5")).mappings().all()
            for r in rows:
                print(dict(r))
                
        # Sample of inserted details
        if res_d > 0:
            print("\nSample details:")
            rows = conn.execute(text("SELECT id, nasiento, ccodcue, ndebe, nhaber, cglosa FROM cf_diariol WHERE company_id = 4 AND subcategoria_id = 63 LIMIT 5")).mappings().all()
            for r in rows:
                print(dict(r))

if __name__ == "__main__":
    main()
