from backend.app.core.database import dest_engine
from sqlalchemy import text

def run_migration():
    print("Running migration to add col_origen_periodo and col_origen_mes to mapeo_subcategorias...")
    with dest_engine.connect() as conn:
        # PostgreSQL syntax to add columns if they don't exist
        conn.execute(text("ALTER TABLE mapeo_subcategorias ADD COLUMN IF NOT EXISTS col_origen_periodo VARCHAR(100);"))
        conn.execute(text("ALTER TABLE mapeo_subcategorias ADD COLUMN IF NOT EXISTS col_origen_mes VARCHAR(100);"))
        conn.commit()
    print("Migration finished successfully.")

if __name__ == "__main__":
    run_migration()
