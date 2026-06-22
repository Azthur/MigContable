import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ["POSTGRES_CONNECTION_STRING"] = "postgresql://postgres:postgres@localhost:5434/migconta_db"

def main():
    engine = create_engine(os.environ["POSTGRES_CONNECTION_STRING"])
    Session = sessionmaker(bind=engine)
    db = Session()

    # Monkeypatch the session execute to intercept insertions into DetTable (cf_diariol)
    original_execute = db.execute
    
    def patched_execute(statement, *args, **kwargs):
        # Check if statement is an insert into cf_diariol
        stmt_str = str(statement).lower()
        if "insert" in stmt_str and "cf_diariol" in stmt_str:
            print("\n[MONKEYPATCH] Intercepted insert into cf_diariol:")
            # args can contain a list/tuple of parameters
            if args:
                print("  args:", args)
            if kwargs:
                print("  kwargs:", kwargs)
        return original_execute(statement, *args, **kwargs)
        
    db.execute = patched_execute

    from backend.app.api.endpoints.mapeo import generate_to_cf_diariol
    
    body = {
        "company_id": 4,
        "subcategoria_id": 76,
        "clear_previous": True,
        "is_realtime": False
    }
    
    print("Running generate_to_cf_diariol with monkeypatch...")
    res = generate_to_cf_diariol(body, db)
    print("Result:", res)

if __name__ == "__main__":
    main()
