from sqlalchemy import create_engine, text
e = create_engine("postgresql://postgres:postgres@localhost:5434/migconta_db")
with e.connect() as c:
    # Check what IdCobranza_CodCia and empresa values exist in the source
    print("=== IdCobranza_CodCia distribution ===")
    dist = c.execute(text("""
        SELECT "IdCobranza_CodCia", count(*) FROM tbl_conciliados 
        WHERE company_id = 1
        GROUP BY "IdCobranza_CodCia"
        ORDER BY "IdCobranza_CodCia"
    """)).fetchall()
    for d in dist:
        print(f"  {d[0]!r}: {d[1]}")
    
    print("\n=== empresa distribution ===")
    dist2 = c.execute(text("""
        SELECT empresa, count(*) FROM tbl_conciliados 
        WHERE company_id = 1
        GROUP BY empresa
        ORDER BY empresa
    """)).fetchall()
    for d in dist2:
        print(f"  {d[0]!r}: {d[1]}")
    
    # Rows that DON'T match ANY active condition
    # Condition 1-2: IdCobranza_CodCia = '002'
    # Condition 3-4: empresa = '002' AND IdCobranza_CodCia IN ('007','005','003','001','004')
    print("\n=== Rows NOT matching ANY condition ===")
    unmatched = c.execute(text("""
        SELECT count(*) FROM tbl_conciliados 
        WHERE company_id = 1
        AND NOT (
            "IdCobranza_CodCia" = '002'
            OR (empresa = '002' AND "IdCobranza_CodCia" IN ('007','005','003','001','004'))
        )
    """)).scalar()
    print(f"  Unmatched rows: {unmatched}")
    
    # For the period 2026-06 specifically
    print("\n=== For period 2026-06 ===")
    # Need to check what the filter_rules actually produce during realtime
    # filter_rules has cper=2026, c_mes=05 but realtime overrides to current month
    total_06 = c.execute(text("""
        SELECT count(*) FROM tbl_conciliados 
        WHERE company_id = 1 AND "C_periodo" = '2026' AND "C_mes" = '06'
    """)).scalar()
    print(f"  Total rows for 2026-06: {total_06}")
    
    matched_06 = c.execute(text("""
        SELECT count(*) FROM tbl_conciliados 
        WHERE company_id = 1 AND "C_periodo" = '2026' AND "C_mes" = '06'
        AND (
            "IdCobranza_CodCia" = '002'
            OR (empresa = '002' AND "IdCobranza_CodCia" IN ('007','005','003','001','004'))
        )
    """)).scalar()
    print(f"  Rows matching at least one condition: {matched_06}")
    print(f"  Rows NOT matching any condition: {total_06 - matched_06}")
    
    # Check distinct IDCOBRANZA_CODDOC,IDCOBRANZA_NRODOC for unmatched
    unmatched_groups = c.execute(text("""
        SELECT count(DISTINCT ("IdCobranza_coddoc" || '-' || "IdCobranza_nrodoc")) 
        FROM tbl_conciliados 
        WHERE company_id = 1 AND "C_periodo" = '2026' AND "C_mes" = '06'
        AND NOT (
            "IdCobranza_CodCia" = '002'
            OR (empresa = '002' AND "IdCobranza_CodCia" IN ('007','005','003','001','004'))
        )
    """)).scalar()
    print(f"  Distinct unmatched seat groups: {unmatched_groups}")
    
    total_groups = c.execute(text("""
        SELECT count(DISTINCT ("IdCobranza_coddoc" || '-' || "IdCobranza_nrodoc")) 
        FROM tbl_conciliados 
        WHERE company_id = 1 AND "C_periodo" = '2026' AND "C_mes" = '06'
    """)).scalar()
    print(f"  Total seat groups for 2026-06: {total_groups}")
    
    # Sample of unmatched rows
    print("\n=== Sample unmatched rows ===")
    samples = c.execute(text("""
        SELECT "IdCobranza_CodCia", empresa, "IdCobranza_coddoc", "IdCobranza_nrodoc"
        FROM tbl_conciliados 
        WHERE company_id = 1 AND "C_periodo" = '2026' AND "C_mes" = '06'
        AND NOT (
            "IdCobranza_CodCia" = '002'
            OR (empresa = '002' AND "IdCobranza_CodCia" IN ('007','005','003','001','004'))
        )
        LIMIT 10
    """)).fetchall()
    for s in samples:
        print(f"  CodCia={s[0]!r}, empresa={s[1]!r}, coddoc={s[2]!r}, nrodoc={s[3]!r}")
