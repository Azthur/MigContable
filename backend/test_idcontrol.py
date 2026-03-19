import sys
from sqlalchemy import create_engine, text

def main():
    try:
        engine = create_engine("postgresql://postgres:migconta2024*@localhost:5432/micont_db")
        with engine.connect() as conn:
            query = text("SELECT COUNT(*) FROM information_schema.columns WHERE table_name='cf_diariol' AND column_name='idcontrol'")
            res = conn.execute(query).scalar()
            print("cf_diariol has idcontrol:", res > 0)
            
            query2 = text("SELECT COUNT(*) FROM information_schema.columns WHERE table_name='cf_diario' AND column_name='idcontrol'")
            res2 = conn.execute(query2).scalar()
            print("cf_diario has idcontrol:", res2 > 0)
    except Exception as e:
        print("ERROR:", str(e).encode('ascii', 'ignore').decode('ascii'))

if __name__ == "__main__":
    main()
