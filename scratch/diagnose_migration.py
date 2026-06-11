"""
Diagnose why details (cf_diariol) are not being migrated to Contasis final DB.
"""
from sqlalchemy import create_engine, text

LOCAL_DB = "postgresql://postgres:postgres@localhost:5434/migconta_db"

def main():
    engine = create_engine(LOCAL_DB)
    
    # 1. Companies
    with engine.connect() as conn:
        print("=== COMPANIES ===")
        companies = conn.execute(text("SELECT id, name FROM companies")).mappings().all()
        for c in companies:
            print(f"  ID={c['id']}, name={c['name']}")

    # 2. Subcategories for 200-Cancelacion
    with engine.connect() as conn:
        print("\n=== SUBCATEGORIES (200-Cancelacion) ===")
        subcats = conn.execute(text("""
            SELECT s.id, s.nombre, s.tabla_destino_cabecera, s.tabla_destino_detalle,
                   s.col_destino_nasiento, s.generate_headers, c.company_id
            FROM mapeo_subcategorias s
            JOIN mapeo_categorias c ON s.categoria_id = c.id
            WHERE s.nombre ILIKE '%200-Cancelacion%'
        """)).mappings().all()
        for s in subcats:
            print(f"  ID={s['id']}, nombre={s['nombre']}")
            print(f"    tabla_cabecera={s['tabla_destino_cabecera']}, tabla_detalle={s['tabla_destino_detalle']}")
            print(f"    col_nasiento={s['col_destino_nasiento']}, generate_headers={s['generate_headers']}")
            print(f"    company_id={s['company_id']}")

    # 3. Local staging counts
    with engine.connect() as conn:
        print("\n=== LOCAL cf_diario (headers) for 200-Cancelacion subcat ===")
        # first get the subcat id
        subcat_id = conn.execute(text("""
            SELECT s.id FROM mapeo_subcategorias s
            JOIN mapeo_categorias c ON s.categoria_id = c.id
            WHERE s.nombre ILIKE '%200-Cancelacion%' LIMIT 1
        """)).scalar()
        company_id_val = conn.execute(text("""
            SELECT c.company_id FROM mapeo_subcategorias s
            JOIN mapeo_categorias c ON s.categoria_id = c.id
            WHERE s.id = :sid
        """), {"sid": subcat_id}).scalar()
        print(f"  subcat_id={subcat_id}, company_id={company_id_val}")

        # Headers
        h_count = conn.execute(text("""
            SELECT count(*) FROM cf_diario 
            WHERE company_id = :cid AND subcategoria_id = :sid
        """), {"cid": company_id_val, "sid": subcat_id}).scalar()
        print(f"  Total headers in cf_diario: {h_count}")

        h_by_estado = conn.execute(text("""
            SELECT estado, count(*) FROM cf_diario 
            WHERE company_id = :cid AND subcategoria_id = :sid
            GROUP BY estado
        """), {"cid": company_id_val, "sid": subcat_id}).fetchall()
        for e in h_by_estado:
            print(f"    estado={e[0]}: {e[1]}")

        # Details
        d_count = conn.execute(text("""
            SELECT count(*) FROM cf_diariol 
            WHERE company_id = :cid AND subcategoria_id = :sid
        """), {"cid": company_id_val, "sid": subcat_id}).scalar()
        print(f"\n  Total details in cf_diariol: {d_count}")

        d_by_estado = conn.execute(text("""
            SELECT estado, count(*) FROM cf_diariol 
            WHERE company_id = :cid AND subcategoria_id = :sid
            GROUP BY estado
        """), {"cid": company_id_val, "sid": subcat_id}).fetchall()
        for e in d_by_estado:
            print(f"    estado={e[0]}: {e[1]}")

    # 4. Sample seat keys from local staging - check types
    with engine.connect() as conn:
        print("\n=== SAMPLE SEAT KEYS (cf_diario headers) ===")
        samples_h = conn.execute(text("""
            SELECT cper, cmes, ccodori, nasiento, pg_typeof(cper) as type_cper, 
                   pg_typeof(cmes) as type_cmes, pg_typeof(ccodori) as type_ccodori, 
                   pg_typeof(nasiento) as type_nasiento
            FROM cf_diario 
            WHERE company_id = :cid AND subcategoria_id = :sid
            LIMIT 5
        """), {"cid": company_id_val, "sid": subcat_id}).mappings().all()
        for s in samples_h:
            print(f"  cper={s['cper']!r} ({s['type_cper']}), cmes={s['cmes']!r} ({s['type_cmes']}), ccodori={s['ccodori']!r} ({s['type_ccodori']}), nasiento={s['nasiento']!r} ({s['type_nasiento']})")

        print("\n=== SAMPLE SEAT KEYS (cf_diariol details) ===")
        samples_d = conn.execute(text("""
            SELECT cper, cmes, ccodori, nasiento, pg_typeof(cper) as type_cper, 
                   pg_typeof(cmes) as type_cmes, pg_typeof(ccodori) as type_ccodori, 
                   pg_typeof(nasiento) as type_nasiento
            FROM cf_diariol 
            WHERE company_id = :cid AND subcategoria_id = :sid
            LIMIT 5
        """), {"cid": company_id_val, "sid": subcat_id}).mappings().all()
        for s in samples_d:
            print(f"  cper={s['cper']!r} ({s['type_cper']}), cmes={s['cmes']!r} ({s['type_cmes']}), ccodori={s['ccodori']!r} ({s['type_ccodori']}), nasiento={s['nasiento']!r} ({s['type_nasiento']})")

    # 5. Check seat key matching - do headers and details actually match?
    with engine.connect() as conn:
        print("\n=== SEAT KEY MATCHING ANALYSIS ===")
        # Headers with distinct seat keys
        distinct_h = conn.execute(text("""
            SELECT DISTINCT cper, cmes, ccodori, nasiento 
            FROM cf_diario 
            WHERE company_id = :cid AND subcategoria_id = :sid
            ORDER BY nasiento
        """), {"cid": company_id_val, "sid": subcat_id}).fetchall()
        print(f"  Distinct header seats: {len(distinct_h)}")

        # Details with distinct seat keys  
        distinct_d = conn.execute(text("""
            SELECT DISTINCT cper, cmes, ccodori, nasiento 
            FROM cf_diariol 
            WHERE company_id = :cid AND subcategoria_id = :sid
            ORDER BY nasiento
        """), {"cid": company_id_val, "sid": subcat_id}).fetchall()
        print(f"  Distinct detail seats: {len(distinct_d)}")

        # Find headers without matching details
        orphan_headers = conn.execute(text("""
            SELECT h.cper, h.cmes, h.ccodori, h.nasiento 
            FROM (SELECT DISTINCT cper, cmes, ccodori, nasiento FROM cf_diario WHERE company_id = :cid AND subcategoria_id = :sid) h
            LEFT JOIN (SELECT DISTINCT cper, cmes, ccodori, nasiento FROM cf_diariol WHERE company_id = :cid AND subcategoria_id = :sid) d
            ON h.cper = d.cper AND h.cmes = d.cmes AND h.ccodori = d.ccodori AND h.nasiento = d.nasiento
            WHERE d.nasiento IS NULL
            ORDER BY h.nasiento
            LIMIT 20
        """), {"cid": company_id_val, "sid": subcat_id}).fetchall()
        print(f"\n  Headers WITHOUT matching details (orphan headers): {len(orphan_headers)}")
        for o in orphan_headers[:10]:
            print(f"    cper={o[0]!r}, cmes={o[1]!r}, ccodori={o[2]!r}, nasiento={o[3]!r}")

        # Find details without matching headers
        orphan_details = conn.execute(text("""
            SELECT d.cper, d.cmes, d.ccodori, d.nasiento, count(*) as cnt
            FROM (SELECT DISTINCT cper, cmes, ccodori, nasiento FROM cf_diariol WHERE company_id = :cid AND subcategoria_id = :sid) d
            LEFT JOIN (SELECT DISTINCT cper, cmes, ccodori, nasiento FROM cf_diario WHERE company_id = :cid AND subcategoria_id = :sid) h
            ON h.cper = d.cper AND h.cmes = d.cmes AND h.ccodori = d.ccodori AND h.nasiento = d.nasiento
            WHERE h.nasiento IS NULL
            GROUP BY d.cper, d.cmes, d.ccodori, d.nasiento
            ORDER BY d.nasiento
            LIMIT 20
        """), {"cid": company_id_val, "sid": subcat_id}).fetchall()
        print(f"\n  Details WITHOUT matching headers (orphan details): {len(orphan_details)}")
        for o in orphan_details[:10]:
            print(f"    cper={o[0]!r}, cmes={o[1]!r}, ccodori={o[2]!r}, nasiento={o[3]!r}, count={o[4]}")

    # 6. Check the FinalDestConnection config
    with engine.connect() as conn:
        print("\n=== FINAL DEST CONNECTION ===")
        fdest = conn.execute(text("""
            SELECT id, company_id, host, port, database_name, username, is_active
            FROM final_dest_connections
            WHERE company_id = :cid
        """), {"cid": company_id_val}).mappings().all()
        for f in fdest:
            print(f"  {dict(f)}")

if __name__ == "__main__":
    main()
