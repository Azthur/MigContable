from backend.app.core.database import DestSessionLocal
from sqlalchemy import text
import pandas as pd

db = DestSessionLocal()
try:
    # Fetch some rows from ccbrrdoc where we expect lookups to be resolved
    query = text('SELECT "C_car", "codref1", "C_moneda", "C_tipoNC", "C_SerieNC", "C_numeroNC", "C_fechaNC_Contasis" FROM "ccbrrdoc" WHERE company_id = 1 LIMIT 50')
    df = pd.read_sql(query, db.bind)
    
    print("Sample records from ccbrrdoc:")
    print(df.to_string(index=False))
    
    print("\nNull counts for key lookup columns:")
    print(df.isnull().sum())
    
    # Let's count how many have non-null values for the entire table
    total_query = text('SELECT COUNT(*) as total, COUNT("codref1") as has_codref1, COUNT("C_moneda") as has_cmoneda FROM "ccbrrdoc" WHERE company_id = 1')
    res = db.execute(total_query).fetchone()
    print(f"\nOverall Stats for ccbrrdoc (Company 1):")
    print(f"Total rows: {res[0]}")
    print(f"Rows with codref1 populated: {res[1]}")
    print(f"Rows with C_moneda populated: {res[2]}")
finally:
    db.close()
