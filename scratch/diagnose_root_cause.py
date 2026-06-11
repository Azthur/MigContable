"""
Root cause analysis: Check the estado of orphan headers and detail rows.
"""
from sqlalchemy import create_engine, text

LOCAL_DB = "postgresql://postgres:postgres@localhost:5434/migconta_db"

def main():
    engine = create_engine(LOCAL_DB)
    
    with engine.connect() as conn:
        # 1. Headers per lote_id with estado breakdown for 2026-06
        print("=== HEADERS: lote_id + estado for 2026-06 ===")
        results = conn.execute(text("""
            SELECT lote_id, estado, count(*) as cnt
            FROM cf_diario 
            WHERE company_id = 1 AND subcategoria_id = 43 AND cper = '2026' AND cmes = '06'
            GROUP BY lote_id, estado
            ORDER BY lote_id, estado
        """)).fetchall()
        for r in results:
            print(f"  lote={r[0]}, estado={r[1]}, count={r[2]}")

        # 2. Details per lote_id with estado breakdown for 2026-06
        print("\n=== DETAILS: lote_id + estado for 2026-06 ===")
        results = conn.execute(text("""
            SELECT lote_id, estado, count(*) as cnt
            FROM cf_diariol 
            WHERE company_id = 1 AND subcategoria_id = 43 AND cper = '2026' AND cmes = '06'
            GROUP BY lote_id, estado
            ORDER BY lote_id, estado
        """)).fetchall()
        for r in results:
            print(f"  lote={r[0]}, estado={r[1]}, count={r[2]}")

        # 3. All periods - check if problem exists everywhere
        print("\n=== ALL PERIODS: headers vs details counts ===")
        periods = conn.execute(text("""
            SELECT cper, cmes, 
                   (SELECT count(DISTINCT nasiento) FROM cf_diario WHERE company_id=1 AND subcategoria_id=43 AND cper=p.cper AND cmes=p.cmes) as h_seats,
                   (SELECT count(DISTINCT nasiento) FROM cf_diariol WHERE company_id=1 AND subcategoria_id=43 AND cper=p.cper AND cmes=p.cmes) as d_seats
            FROM (SELECT DISTINCT cper, cmes FROM cf_diario WHERE company_id=1 AND subcategoria_id=43) p
            ORDER BY p.cper, p.cmes
        """)).fetchall()
        for p in periods:
            diff = int(p[2]) - int(p[3])
            flag = " *** MISMATCH ***" if diff != 0 else ""
            print(f"  {p[0]}-{p[1]}: header_seats={p[2]}, detail_seats={p[3]}, diff={diff}{flag}")

        # 4. Count total duplicate headers across all periods (headers with >1 lote_id)
        print("\n=== DUPLICATE HEADERS (same cper/cmes/ccodori/nasiento, different lote_id) ===")
        dupes = conn.execute(text("""
            SELECT cper, cmes, ccodori, nasiento, count(DISTINCT lote_id) as lote_count, count(*) as total_rows
            FROM cf_diario 
            WHERE company_id = 1 AND subcategoria_id = 43
            GROUP BY cper, cmes, ccodori, nasiento
            HAVING count(DISTINCT lote_id) > 1
            ORDER BY cper, cmes, nasiento
            LIMIT 20
        """)).fetchall()
        print(f"  Found {len(dupes)} seat keys with duplicate lote_ids:")
        for d in dupes[:10]:
            print(f"    {d[0]}-{d[1]}, ccodori={d[2]}, nasiento={d[3]}: {d[4]} lotes, {d[5]} total rows")

        # 5. For orphan lotes (ones without details), check their created_at
        print("\n=== ORPHAN LOTES (headers without ANY details in same lote) ===")
        orphan_lotes = conn.execute(text("""
            SELECT DISTINCT h.lote_id, count(*) as h_count, min(h.created_at) as first_created
            FROM cf_diario h
            LEFT JOIN cf_diariol d ON d.company_id = h.company_id 
                AND d.subcategoria_id = h.subcategoria_id 
                AND d.lote_id = h.lote_id
            WHERE h.company_id = 1 AND h.subcategoria_id = 43
            AND d.id IS NULL
            GROUP BY h.lote_id
            ORDER BY first_created
        """)).fetchall()
        for o in orphan_lotes:
            print(f"  lote={o[0]}: {o[1]} orphan headers, created_at={o[2]}")

if __name__ == "__main__":
    main()
