from backend.app.core.database import dest_engine
from sqlalchemy import text

def run_migration():
    print("Running migration to add indexes on cper and cmes inside cf_diariol staging table...")
    with dest_engine.connect() as conn:
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_cf_diariol_cper ON cf_diariol (cper);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_cf_diariol_cmes ON cf_diariol (cmes);"))
        conn.commit()
    print("Indexes migration finished successfully.")

if __name__ == "__main__":
    run_migration()
