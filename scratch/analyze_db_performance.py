import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from backend.app.core.database import DestSessionLocal
from sqlalchemy import text

def analyze():
    db = DestSessionLocal()
    try:
        # 1. Get recent logs with statuses and times
        sql = text("""
            SELECT process_name, status, created_at, message
            FROM integ_logs
            ORDER BY created_at DESC
            LIMIT 20
        """)
        rows = db.execute(sql).fetchall()
        print("--- RECENT INTEGRATION LOGS ---")
        for r in rows:
            print(f"[{r[2]}] {r[0]} | Status: {r[1]} | Msg: {r[3][:120]}")

        # 2. Get recent ETL Realtime Logs
        print("\n--- RECENT ETL REALTIME LOGS ---")
        sql_rt = text("""
            SELECT run_date, status, message, records_extracted, records_generated, records_migrated, subcategorias
            FROM etl_realtime_logs
            ORDER BY run_date DESC
            LIMIT 20
        """)
        rt_rows = db.execute(sql_rt).fetchall()
        for r in rt_rows:
            print(f"[{r[0]}] Status: {r[1]} | Extracted: {r[3]} | Gen: {r[4]} | Mig: {r[5]} | Subcats: {r[6]} | Msg: {r[2][:120] if r[2] else ''}")

        # 3. Analyze tables sizes in Postgres
        print("\n--- STAGING/RAW TABLES SIZES ---")
        sql_tables = text("""
            SELECT table_name, 
                   pg_size_pretty(pg_total_relation_size(quote_ident(table_name))) AS total_size,
                   (xpath('/row/cnt/text()', xmlparse(document query_to_xml(format('select count(*) as cnt from %I', table_name), false, true, ''))))[1]::text::int AS row_count
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
              AND table_name NOT IN ('spatial_ref_sys')
              AND table_type = 'BASE TABLE'
            ORDER BY row_count DESC NULLS LAST
            LIMIT 30;
        """)
        tables = db.execute(sql_tables).fetchall()
        for t in tables:
            print(f"Table: {t[0]:<40} | Size: {t[1]:<10} | Rows: {t[2]}")

    except Exception as e:
        print("Error analyzing:", e)
    finally:
        db.close()

if __name__ == "__main__":
    analyze()
