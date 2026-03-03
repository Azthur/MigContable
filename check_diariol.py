from sqlalchemy import create_engine, text
from backend.app.core.config import get_settings

def check():
    settings = get_settings()
    engine = create_engine(settings.POSTGRES_CONNECTION_STRING)
    with engine.connect() as conn:
        res = conn.execute(text("SELECT count(*) FROM cf_diariol")).scalar()
        print(f"TOTAL IN DIARIOL: {res}")
        
        if res > 0:
            row = conn.execute(text("SELECT subcategoria_id, cper, cmes, nasiento, nidlin, ccodsu, valida_sunat, crvieap FROM cf_diariol LIMIT 10")).mappings().all()
            for r in row:
                print(r)

if __name__ == "__main__":
    check()
