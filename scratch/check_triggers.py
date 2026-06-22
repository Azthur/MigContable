import os
from sqlalchemy import create_engine, text

os.environ["POSTGRES_CONNECTION_STRING"] = "postgresql://postgres:postgres@localhost:5434/migconta_db"

def main():
    engine = create_engine(os.environ["POSTGRES_CONNECTION_STRING"])
    with engine.connect() as conn:
        print("--- Triggers on cf_diariol ---")
        triggers = conn.execute(text("""
            SELECT trigger_name, event_manipulation, action_statement, action_timing
            FROM information_schema.triggers
            WHERE event_object_table = 'cf_diariol'
        """)).mappings().all()
        for t in triggers:
            print(dict(t))
        if not triggers:
            print("No triggers found.")

if __name__ == "__main__":
    main()
