"""
Cleanup script:
1. Remove orphan headers from Contasis final (headers without details)
2. Mark orphan headers in local staging as SIN_DETALLE  
3. Remove duplicate orphan headers from repeated ETL runs
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from sqlalchemy import create_engine, text

LOCAL_DB = "postgresql://postgres:postgres@localhost:5434/migconta_db"
CONTASIS_DB = "postgresql://postgres:postgres@192.168.2.90:5432/contasis_003"

def main():
    local_engine = create_engine(LOCAL_DB)
    contasis_engine = create_engine(CONTASIS_DB)
    
    # STEP 1: Clean up Contasis final - remove orphan headers
    print("=== STEP 1: Cleaning Contasis final (orphan headers) ===")
    with contasis_engine.begin() as conn:
        orphans = conn.execute(text("""
            SELECT h.cper, h.cmes, h.ccodori, h.nasiento
            FROM cf_diario h
            LEFT JOIN cf_diariol d 
                ON h.cper = d.cper AND h.cmes = d.cmes AND h.ccodori = d.ccodori AND h.nasiento = d.nasiento
            WHERE h.ccodori = '200'
            AND d.nasiento IS NULL
        """)).fetchall()
        
        print(f"  Found {len(orphans)} orphan headers in Contasis for ccodori='200'")
        
        if orphans:
            for o in orphans:
                conn.execute(text("""
                    DELETE FROM cf_diario 
                    WHERE cper = :cper AND cmes = :cmes AND ccodori = :ccodori AND nasiento = :nasiento
                """), {"cper": o[0], "cmes": o[1], "ccodori": o[2], "nasiento": o[3]})
            print(f"  Deleted {len(orphans)} orphan headers from Contasis cf_diario")
    
    # STEP 2: Clean up local staging
    print("\n=== STEP 2: Cleaning local staging ===")
    with local_engine.begin() as conn:
        orphan_local_count = conn.execute(text("""
            SELECT count(*) FROM cf_diario h
            LEFT JOIN cf_diariol d 
                ON h.company_id = d.company_id 
                AND h.subcategoria_id = d.subcategoria_id 
                AND h.cper = d.cper AND h.cmes = d.cmes AND h.nasiento = d.nasiento
            WHERE h.company_id = 1 AND h.subcategoria_id = 43
            AND d.id IS NULL
        """)).scalar()
        print(f"  Found {orphan_local_count} orphan header rows in local cf_diario for subcat 43")
        
        updated = conn.execute(text("""
            UPDATE cf_diario h
            SET estado = 'SIN_DETALLE'
            FROM (
                SELECT h2.id FROM cf_diario h2
                LEFT JOIN cf_diariol d 
                    ON h2.company_id = d.company_id 
                    AND h2.subcategoria_id = d.subcategoria_id 
                    AND h2.cper = d.cper AND h2.cmes = d.cmes AND h2.nasiento = d.nasiento
                WHERE h2.company_id = 1 AND h2.subcategoria_id = 43
                AND d.id IS NULL
            ) orphans
            WHERE h.id = orphans.id
        """))
        print(f"  Marked {updated.rowcount} orphan header rows as SIN_DETALLE")
        
        # Remove duplicate headers from repeated lote_ids
        dupes = conn.execute(text("""
            SELECT count(*) FROM cf_diario
            WHERE company_id = 1 AND subcategoria_id = 43
            AND id NOT IN (
                SELECT max(id) FROM cf_diario
                WHERE company_id = 1 AND subcategoria_id = 43
                GROUP BY cper, cmes, ccodori, nasiento
            )
        """)).scalar()
        print(f"\n  Found {dupes} duplicate header rows (from repeated ETL runs)")
        
        if dupes > 0:
            deleted = conn.execute(text("""
                DELETE FROM cf_diario
                WHERE company_id = 1 AND subcategoria_id = 43
                AND id NOT IN (
                    SELECT max(id) FROM cf_diario
                    WHERE company_id = 1 AND subcategoria_id = 43
                    GROUP BY cper, cmes, ccodori, nasiento
                )
            """))
            print(f"  Deleted {deleted.rowcount} duplicate header rows")
    
    # STEP 3: Verify
    print("\n=== STEP 3: Verification ===")
    with local_engine.connect() as conn:
        h_total = conn.execute(text("""
            SELECT count(*) FROM cf_diario WHERE company_id = 1 AND subcategoria_id = 43
        """)).scalar()
        h_migrado = conn.execute(text("""
            SELECT count(*) FROM cf_diario WHERE company_id = 1 AND subcategoria_id = 43 AND estado = 'MIGRADO'
        """)).scalar()
        h_sin_det = conn.execute(text("""
            SELECT count(*) FROM cf_diario WHERE company_id = 1 AND subcategoria_id = 43 AND estado = 'SIN_DETALLE'
        """)).scalar()
        d_total = conn.execute(text("""
            SELECT count(*) FROM cf_diariol WHERE company_id = 1 AND subcategoria_id = 43
        """)).scalar()
        print(f"  Local cf_diario: total={h_total}, MIGRADO={h_migrado}, SIN_DETALLE={h_sin_det}")
        print(f"  Local cf_diariol: total={d_total}")
        
        remaining = conn.execute(text("""
            SELECT count(DISTINCT (h.cper || '-' || h.cmes || '-' || h.nasiento::text))
            FROM cf_diario h
            LEFT JOIN cf_diariol d 
                ON h.company_id = d.company_id 
                AND h.subcategoria_id = d.subcategoria_id 
                AND h.cper = d.cper AND h.cmes = d.cmes AND h.nasiento = d.nasiento
            WHERE h.company_id = 1 AND h.subcategoria_id = 43 AND h.estado = 'MIGRADO'
            AND d.id IS NULL
        """)).scalar()
        print(f"  Remaining orphan headers (MIGRADO without details): {remaining}")
    
    with contasis_engine.connect() as conn:
        h_final = conn.execute(text("""
            SELECT count(*) FROM cf_diario WHERE ccodori = '200'
        """)).scalar()
        d_final = conn.execute(text("""
            SELECT count(*) FROM cf_diariol WHERE ccodori = '200'
        """)).scalar()
        print(f"\n  Contasis cf_diario (ccodori=200): {h_final}")
        print(f"  Contasis cf_diariol (ccodori=200): {d_final}")
        
        orphans_final = conn.execute(text("""
            SELECT count(*) FROM cf_diario h
            LEFT JOIN cf_diariol d 
                ON h.cper = d.cper AND h.cmes = d.cmes AND h.ccodori = d.ccodori AND h.nasiento = d.nasiento
            WHERE h.ccodori = '200'
            AND d.nasiento IS NULL
        """)).scalar()
        print(f"  Remaining orphan headers in Contasis: {orphans_final}")

    print("\nCleanup complete!")

if __name__ == "__main__":
    main()
