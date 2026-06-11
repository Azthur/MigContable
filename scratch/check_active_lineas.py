from sqlalchemy import create_engine, text
e = create_engine("postgresql://postgres:postgres@localhost:5434/migconta_db")
with e.connect() as c:
    print("=== ACTIVE LINEAS for subcat 43 ===")
    rows = c.execute(text("""
        SELECT id, orden, nombre_linea, nivel, condicion_aplicacion, is_active, aplica_ajuste_redondeo
        FROM mapeo_lineas_asiento 
        WHERE subcategoria_id = 43 AND is_active = true
        ORDER BY orden
    """)).mappings().all()
    for r in rows:
        print(f"  orden={r['orden']}, nombre={r['nombre_linea']}, nivel={r['nivel']}")
        print(f"    condicion={r['condicion_aplicacion']}")
        print(f"    ajuste_redondeo={r['aplica_ajuste_redondeo']}")
    
    print(f"\n  Total active lineas: {len(rows)}")
    
    # Now check what conditions look like  
    conditions = set()
    for r in rows:
        if r['condicion_aplicacion']:
            conditions.add(r['condicion_aplicacion'])
    print(f"\n  Unique conditions: {conditions}")
    
    # Check tbl_conciliados - what does the source data look like?
    print("\n=== SOURCE TABLE: tbl_conciliados for subcat 43 ===")
    sub = c.execute(text("SELECT tabla_origen, clave_asiento, filter_rules FROM mapeo_subcategorias WHERE id = 43")).mappings().first()
    print(f"  tabla_origen: {sub['tabla_origen']}")
    print(f"  clave_asiento: {sub['clave_asiento']}")
    print(f"  filter_rules: {sub['filter_rules']}")
    
    # Check total source rows for period 06
    src_count = c.execute(text("""
        SELECT count(*) FROM tbl_conciliados WHERE company_id = 1
    """)).scalar()
    print(f"\n  Total source rows (all periods): {src_count}")
    
    # Check columns
    print("\n=== tbl_conciliados columns ===")
    cols = c.execute(text("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = 'tbl_conciliados' ORDER BY ordinal_position LIMIT 30
    """)).fetchall()
    for col in cols:
        print(f"  {col[0]}")
