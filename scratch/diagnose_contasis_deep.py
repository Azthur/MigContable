"""
Deep diagnosis: Check what's in Contasis final DB vs local staging.
Focus on period 2026-06 and ccodori='200'.
"""
from sqlalchemy import create_engine, text

LOCAL_DB = "postgresql://postgres:postgres@localhost:5434/migconta_db"
CONTASIS_DB = "postgresql://postgres:postgres@192.168.2.90:5432/contasis_003"

def main():
    local_engine = create_engine(LOCAL_DB)
    contasis_engine = create_engine(CONTASIS_DB)

    # ---- LOCAL STAGING ----
    with local_engine.connect() as conn:
        print("===== LOCAL STAGING (migconta_db) =====")
        
        # Headers for 2026-06
        h_count = conn.execute(text("""
            SELECT count(*) FROM cf_diario 
            WHERE company_id = 1 AND subcategoria_id = 43 AND cper = '2026' AND cmes = '06'
        """)).scalar()
        print(f"  Headers in local cf_diario (2026-06): {h_count}")

        # Details for 2026-06
        d_count = conn.execute(text("""
            SELECT count(*) FROM cf_diariol 
            WHERE company_id = 1 AND subcategoria_id = 43 AND cper = '2026' AND cmes = '06'
        """)).scalar()
        print(f"  Details in local cf_diariol (2026-06): {d_count}")

        # Distinct seats in local headers for 2026-06
        h_seats = conn.execute(text("""
            SELECT DISTINCT nasiento FROM cf_diario 
            WHERE company_id = 1 AND subcategoria_id = 43 AND cper = '2026' AND cmes = '06'
            ORDER BY nasiento
        """)).fetchall()
        h_seat_set = set(s[0] for s in h_seats)
        print(f"  Distinct header seats (2026-06): {len(h_seat_set)}")
        print(f"    Seats: {sorted([int(s) for s in h_seat_set])}")

        # Distinct seats in local details for 2026-06
        d_seats = conn.execute(text("""
            SELECT DISTINCT nasiento FROM cf_diariol 
            WHERE company_id = 1 AND subcategoria_id = 43 AND cper = '2026' AND cmes = '06'
            ORDER BY nasiento
        """)).fetchall()
        d_seat_set = set(s[0] for s in d_seats)
        print(f"\n  Distinct detail seats (2026-06): {len(d_seat_set)}")
        print(f"    Seats: {sorted([int(s) for s in d_seat_set])}")

        # Orphan headers in local (headers without details)
        orphan_local = h_seat_set - d_seat_set
        print(f"\n  LOCAL orphan headers (no details): {len(orphan_local)}")
        if orphan_local:
            print(f"    Seats: {sorted([int(s) for s in orphan_local])}")
            # Check what these orphan headers look like
            for seat in sorted(orphan_local)[:5]:
                row = conn.execute(text("""
                    SELECT nasiento, cglosa, ccodori, cfecdia FROM cf_diario
                    WHERE company_id = 1 AND subcategoria_id = 43 
                    AND cper = '2026' AND cmes = '06' AND nasiento = :n
                """), {"n": int(seat)}).mappings().first()
                if row:
                    print(f"      seat {int(seat)}: glosa={row['cglosa']}, ccodori={row['ccodori']}, cfecdia={row['cfecdia']}")

    # ---- CONTASIS FINAL ----
    with contasis_engine.connect() as conn:
        print("\n\n===== CONTASIS FINAL (contasis_003) =====")
        
        # Headers in Contasis
        h_count_final = conn.execute(text("""
            SELECT count(*) FROM cf_diario 
            WHERE ccodori = '200' AND cper = '2026' AND cmes = '06'
        """)).scalar()
        print(f"  Headers in Contasis cf_diario (200, 2026-06): {h_count_final}")

        # Details in Contasis
        d_count_final = conn.execute(text("""
            SELECT count(*) FROM cf_diariol 
            WHERE ccodori = '200' AND cper = '2026' AND cmes = '06'
        """)).scalar()
        print(f"  Details in Contasis cf_diariol (200, 2026-06): {d_count_final}")

        # Distinct seats in Contasis headers
        h_seats_final = conn.execute(text("""
            SELECT DISTINCT nasiento FROM cf_diario 
            WHERE ccodori = '200' AND cper = '2026' AND cmes = '06'
            ORDER BY nasiento
        """)).fetchall()
        h_final_set = set(s[0] for s in h_seats_final)
        print(f"  Distinct Contasis header seats: {len(h_final_set)}")
        print(f"    Seats: {sorted([int(s) for s in h_final_set])}")

        # Distinct seats in Contasis details
        d_seats_final = conn.execute(text("""
            SELECT DISTINCT nasiento FROM cf_diariol 
            WHERE ccodori = '200' AND cper = '2026' AND cmes = '06'
            ORDER BY nasiento
        """)).fetchall()
        d_final_set = set(s[0] for s in d_seats_final)
        print(f"\n  Distinct Contasis detail seats: {len(d_final_set)}")
        print(f"    Seats: {sorted([int(s) for s in d_final_set])}")

        # Contasis headers WITHOUT details
        orphan_final = h_final_set - d_final_set
        print(f"\n  CONTASIS orphan headers (headers WITHOUT details): {len(orphan_final)}")
        if orphan_final:
            print(f"    Seats: {sorted([int(s) for s in orphan_final])}")

        # ALL periods in contasis for ccodori=200
        print("\n\n=== ALL PERIODS in Contasis for ccodori='200' ===")
        periods = conn.execute(text("""
            SELECT cper, cmes, count(*) as h_count FROM cf_diario
            WHERE ccodori = '200'
            GROUP BY cper, cmes
            ORDER BY cper, cmes
        """)).fetchall()
        for p in periods:
            d_cnt = conn.execute(text("""
                SELECT count(*) FROM cf_diariol
                WHERE ccodori = '200' AND cper = :cper AND cmes = :cmes
            """), {"cper": p[0], "cmes": p[1]}).scalar()
            print(f"  {p[0]}-{p[1]}: headers={p[2]}, details={d_cnt}")

if __name__ == "__main__":
    main()
