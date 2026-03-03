
import sys
import os
# Add backend to path
sys.path.append(os.getcwd())

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from backend.app.core.database import get_dest_db
from backend.app.models.models import IntegLog, Company

# Manually create engine/session if needed or import
# I'll use a direct connection based on what I know or use the app's db module
# The app uses DATABASE_URL. I might need to mock it or just use the code.

def check_logs():
    print("Checking IntegLog table...")
    # I'll try to use the session from backend.app.core.database if possible
    # But I need to initialize it.
    # Simpler: raw psycopg2 or sqlalchemy with hardcoded string if I know it.
    # The default is postgresql://postgres:postgres@localhost:5433/migconta_db
    
    DB_URL = "postgresql://postgres:postgres@localhost:5433/migconta_db"
    
    try:
        engine = create_engine(DB_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Query last 10 logs
        logs = session.query(IntegLog).order_by(IntegLog.created_at.desc()).limit(10).all()
        
        if not logs:
            print("No logs found.")
        else:
            for log in logs:
                print(f"[{log.created_at}] Status: {log.status} | Process: {log.process_name}")
                print(f"Message: {log.message}")
                print("-" * 40)
                
        # Check tables existence
        print("\nChecking tables in migconta_db (public schema)...")
        result = session.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
        tables = [row[0] for row in result]
        if tables:
            for t in tables:
                col_res = session.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{t}'"))
                cols = [r[0] for r in col_res]
                print(f"Table '{t}': {len(cols)} columns")
                if '_migration_id' in cols:
                    print(f"  [OK] Found '_migration_id'")
                    # Count rows
                    try:
                        row_res = session.execute(text(f'SELECT COUNT(*) FROM "{t}"'))
                        count = row_res.fetchone()[0]
                        print(f"  Rows: {count}")
                    except:
                        pass
                elif t not in ['integ_logs', 'companies', 'source_connections', 'destination_connections', 'table_selections', 'migration_controls', 'column_filters', 'mapeo_categorias', 'mapeo_subcategorias', 'mapeo_lineas_asiento', 'cat_cuentas_contables', 'cat_cuentas_presupuesto', 'cat_centros_costo', 'cat_tipo_analitica', 'cat_productos', 'cat_tipo_movimiento', 'config_account_mapping', 'config_document_mapping', 'config_transformation_rules', 'accounting_entries', 'final_dest_connections', 'final_table_selections']:
                    print(f"  [WARN] '_migration_id' missing in potential data table '{t}'")
                    
    except Exception as e:
        print(f"Error checking logs: {e}")

if __name__ == "__main__":
    check_logs()
