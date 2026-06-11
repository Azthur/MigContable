from backend.app.core.database import dest_engine
from sqlalchemy import text

with dest_engine.connect() as conn:
    print("--- COMPANIES ---")
    companies = conn.execute(text("SELECT id, name, is_active FROM companies")).fetchall()
    for c in companies:
        print(c)
        
    print("\n--- STAGING (cf_diariol) TOTAL COUNTS ---")
    counts = conn.execute(text("""
        SELECT company_id, estado, COUNT(*) 
        FROM cf_diariol 
        GROUP BY company_id, estado
    """)).fetchall()
    for ct in counts:
        print(ct)

    print("\n--- STAGING BY PERIOD/MONTH FOR COMPANY ---")
    pm_counts = conn.execute(text("""
        SELECT company_id, cper, cmes, estado, COUNT(*) 
        FROM cf_diariol 
        GROUP BY company_id, cper, cmes, estado
        ORDER BY company_id, cper, cmes, estado
    """)).fetchall()
    for pm in pm_counts:
        print(pm)
