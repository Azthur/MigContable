import os
from sqlalchemy import create_engine, text

os.environ["POSTGRES_CONNECTION_STRING"] = "postgresql://postgres:postgres@localhost:5434/migconta_db"

def main():
    engine = create_engine(os.environ["POSTGRES_CONNECTION_STRING"])
    with engine.connect() as conn:
        # 1. Reset subcategory values
        print("Resetting subcategory 63...")
        conn.execute(text("UPDATE mapeo_subcategorias SET last_generated_control_value = NULL, asiento_inicial = 1 WHERE id = 63"))
        
        # 2. Clear generated headers in cf_diario
        print("Clearing cf_diario...")
        res_h = conn.execute(text("DELETE FROM cf_diario WHERE company_id = 4 AND subcategoria_id = 63"))
        print(f"Deleted {res_h.rowcount} headers.")
        
        # 3. Clear generated details in cf_diariol
        print("Clearing cf_diariol...")
        res_d = conn.execute(text("DELETE FROM cf_diariol WHERE company_id = 4 AND subcategoria_id = 63"))
        print(f"Deleted {res_d.rowcount} details.")
        
        # 4. Commit changes
        conn.execute(text("COMMIT"))
        print("Reset complete!")

if __name__ == "__main__":
    main()
