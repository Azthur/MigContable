from sqlalchemy import create_engine, text
e = create_engine("postgresql://postgres:postgres@localhost:5434/migconta_db")
with e.connect() as c:
    cols = c.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'mapeo_lineas_asiento' ORDER BY ordinal_position")).fetchall()
    print("mapeo_lineas_asiento columns:")
    for r in cols:
        print(f"  {r[0]}")
    
    print("\nSample lineas for subcat 43:")
    rows = c.execute(text("SELECT * FROM mapeo_lineas_asiento WHERE subcategoria_id = 43 ORDER BY orden")).mappings().all()
    for r in rows:
        print(f"\n  {dict(r)}")
