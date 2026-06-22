import os
from sqlalchemy import create_engine, text

os.environ["POSTGRES_CONNECTION_STRING"] = "postgresql://postgres:postgres@localhost:5434/migconta_db"

def main():
    engine = create_engine(os.environ["POSTGRES_CONNECTION_STRING"])
    with engine.connect() as conn:
        # We start a transaction
        trans = conn.begin()
        try:
            # Let's insert a test row
            res = conn.execute(text("""
                INSERT INTO cf_diariol (company_id, subcategoria_id, lote_id, estado, nasiento, nidlin, ccodcue, ndebe, nhaber, ndebes, nhabers)
                VALUES (4, 76, 'TEST_INS', '1', 9999, 1, '1671', 400.0, 0.0, 400.0, 0.0)
                RETURNING id, ndebe, ndebes
            """))
            row = res.mappings().first()
            print("Inserted row via raw SQL:", dict(row))
            
            # Now let's query it back
            res_query = conn.execute(text("SELECT id, ndebe, ndebes FROM cf_diariol WHERE id = :id"), {"id": row['id']})
            row_query = res_query.mappings().first()
            print("Queried row back:", dict(row_query))
        except Exception as e:
            print("Error:", e)
        finally:
            # Rollback so we don't pollute the database
            trans.rollback()

if __name__ == "__main__":
    main()
