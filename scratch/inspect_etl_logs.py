import sys
sys.path.append('c:/SistemaMigConta')
from backend.app.core.database import DestSessionLocal, dest_engine
from sqlalchemy import text
import pandas as pd

db = DestSessionLocal()
try:
    with db.bind.connect() as conn:
        print("=== Recent Realtime ETL Logs ===")
        # check if realtime_etl_log exists
        from sqlalchemy import inspect
        insp = inspect(dest_engine)
        tables = insp.get_table_names()
        print("=== Tables in destination database ===")
        print(tables)
        tables_lower = [t.lower() for t in tables]
        
        # Query etl_realtime_logs
        if 'etl_realtime_logs' in tables:
            print("\n=== Recent etl_realtime_logs ===")
            query = "SELECT id, created_at, company_id, status, records_extracted, records_generated, records_migrated FROM etl_realtime_logs ORDER BY id DESC LIMIT 5"
            try:
                res = conn.execute(text(query))
                df = pd.DataFrame([dict(zip(res.keys(), r)) for r in res.fetchall()])
                print(df.to_string())
            except Exception as e:
                print(f"Error reading etl_realtime_logs: {e}")
                
        # Query integ_logs for CcbRRdoc
        if 'integ_logs' in tables:
            print("\n=== Recent CcbRRdoc runs in integ_logs ===")
            query = "SELECT id, company_id, process_name, status, message, created_at FROM integ_logs WHERE process_name LIKE '%CcbRRdoc%' ORDER BY id DESC LIMIT 5"
            try:
                res = conn.execute(text(query))
                df = pd.DataFrame([dict(zip(res.keys(), r)) for r in res.fetchall()])
                print(df.to_string())
            except Exception as e:
                print(f"Error reading integ_logs: {e}")
            
        print("\n=== Recent Computed Runs/Tasks ===")
        # Check any logs or tables that might indicate run history
        if 'table_selection' in tables:
            res_sel = conn.execute(text('SELECT id, company_id, table_name, last_extracted FROM table_selection WHERE is_selected = true'))
            df_sel = pd.DataFrame([dict(zip(res_sel.keys(), r)) for r in res_sel.fetchall()])
            print(df_sel.to_string())

finally:
    db.close()
