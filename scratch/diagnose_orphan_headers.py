"""
Analyze WHY 66 headers in local staging have no matching details.
Check cf_diario columns to understand the data.
"""
from sqlalchemy import create_engine, text

LOCAL_DB = "postgresql://postgres:postgres@localhost:5434/migconta_db"

def main():
    engine = create_engine(LOCAL_DB)
    
    with engine.connect() as conn:
        # 1. Get columns of cf_diario
        print("=== cf_diario columns ===")
        cols = conn.execute(text("""
            SELECT column_name, data_type FROM information_schema.columns 
            WHERE table_name = 'cf_diario' ORDER BY ordinal_position
        """)).fetchall()
        for c in cols:
            print(f"  {c[0]}: {c[1]}")
        
        print("\n=== cf_diariol columns ===")
        cols = conn.execute(text("""
            SELECT column_name, data_type FROM information_schema.columns 
            WHERE table_name = 'cf_diariol' ORDER BY ordinal_position
        """)).fetchall()
        for c in cols:
            print(f"  {c[0]}: {c[1]}")
    
    with engine.connect() as conn:
        # 2. Sample a header that HAS details (seat 2) vs one that DOESN'T (seat 32)
        print("\n=== SAMPLE: seat 2 (has details) ===")
        h2 = conn.execute(text("""
            SELECT * FROM cf_diario 
            WHERE company_id = 1 AND subcategoria_id = 43 AND cper = '2026' AND cmes = '06' AND nasiento = 2
        """)).mappings().all()
        for h in h2:
            print(f"  Header: {dict(h)}")
        
        d2 = conn.execute(text("""
            SELECT nasiento, nidlin, ccodcue, ndebe, nhaber FROM cf_diariol 
            WHERE company_id = 1 AND subcategoria_id = 43 AND cper = '2026' AND cmes = '06' AND nasiento = 2
        """)).mappings().all()
        for d in d2:
            print(f"  Detail: {dict(d)}")
    
    with engine.connect() as conn:
        print("\n=== SAMPLE: seat 32 (NO details) ===")
        h32 = conn.execute(text("""
            SELECT * FROM cf_diario 
            WHERE company_id = 1 AND subcategoria_id = 43 AND cper = '2026' AND cmes = '06' AND nasiento = 32
        """)).mappings().all()
        for h in h32:
            print(f"  Header: {dict(h)}")
        
        d32 = conn.execute(text("""
            SELECT nasiento, nidlin, ccodcue, ndebe, nhaber FROM cf_diariol 
            WHERE company_id = 1 AND subcategoria_id = 43 AND cper = '2026' AND cmes = '06' AND nasiento = 32
        """)).mappings().all()
        print(f"  Details count: {len(d32)}")

    # 3. Check: do all these orphan headers share some pattern (maybe a different lote_id)?
    with engine.connect() as conn:
        print("\n=== LOTE_ID analysis for 2026-06 ===")
        lotes = conn.execute(text("""
            SELECT lote_id, count(*) as cnt,
                   count(DISTINCT nasiento) as distinct_seats
            FROM cf_diario 
            WHERE company_id = 1 AND subcategoria_id = 43 AND cper = '2026' AND cmes = '06'
            GROUP BY lote_id
            ORDER BY lote_id
        """)).mappings().all()
        for l in lotes:
            print(f"  lote_id={l['lote_id']}: rows={l['cnt']}, distinct_seats={l['distinct_seats']}")

        print("\n=== LOTE_ID analysis for cf_diariol 2026-06 ===")
        lotes_d = conn.execute(text("""
            SELECT lote_id, count(*) as cnt,
                   count(DISTINCT nasiento) as distinct_seats
            FROM cf_diariol 
            WHERE company_id = 1 AND subcategoria_id = 43 AND cper = '2026' AND cmes = '06'
            GROUP BY lote_id
            ORDER BY lote_id
        """)).mappings().all()
        for l in lotes_d:
            print(f"  lote_id={l['lote_id']}: rows={l['cnt']}, distinct_seats={l['distinct_seats']}")

    # 4. Check seats in headers vs details per lote_id
    with engine.connect() as conn:
        for lote_row in lotes:
            lid = lote_row['lote_id']
            h_seats = conn.execute(text("""
                SELECT DISTINCT nasiento FROM cf_diario 
                WHERE company_id = 1 AND subcategoria_id = 43 AND cper = '2026' AND cmes = '06'
                AND lote_id = :lid ORDER BY nasiento
            """), {"lid": lid}).fetchall()
            h_set = set(int(s[0]) for s in h_seats)
            
            d_seats = conn.execute(text("""
                SELECT DISTINCT nasiento FROM cf_diariol 
                WHERE company_id = 1 AND subcategoria_id = 43 AND cper = '2026' AND cmes = '06'
                AND lote_id = :lid ORDER BY nasiento
            """), {"lid": lid}).fetchall()
            d_set = set(int(s[0]) for s in d_seats)
            
            orphans = h_set - d_set
            print(f"\n  Lote {lid}: h_seats={len(h_set)}, d_seats={len(d_set)}, orphans={len(orphans)}")
            if orphans:
                print(f"    Orphan seats: {sorted(orphans)[:20]}...")

if __name__ == "__main__":
    main()
