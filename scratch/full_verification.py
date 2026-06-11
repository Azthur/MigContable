import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from sqlalchemy import create_engine, text

CONTASIS_DB = "postgresql://postgres:postgres@192.168.2.90:5432/contasis_003"
LOCAL_DB = "postgresql://postgres:postgres@localhost:5434/migconta_db"

contasis_engine = create_engine(CONTASIS_DB)
local_engine = create_engine(LOCAL_DB)

print("=== CONTASIS: Verificacion 2026-06 ccodori=200 ===")
with contasis_engine.connect() as c:
    h = c.execute(text("SELECT count(*) FROM cf_diario WHERE ccodori='200' AND cper='2026' AND cmes='06'")).scalar()
    d = c.execute(text("SELECT count(*) FROM cf_diariol WHERE ccodori='200' AND cper='2026' AND cmes='06'")).scalar()
    print(f"  Cabeceras: {h}, Detalles: {d}")
    
    # Orphan check
    orphans = c.execute(text("""
        SELECT count(*) FROM cf_diario h
        LEFT JOIN cf_diariol d ON h.cper=d.cper AND h.cmes=d.cmes AND h.ccodori=d.ccodori AND h.nasiento=d.nasiento
        WHERE h.ccodori='200' AND h.cper='2026' AND h.cmes='06' AND d.nasiento IS NULL
    """)).scalar()
    print(f"  Cabeceras huerfanas (sin detalles): {orphans}")
    
    # All periods summary
    print("\n=== CONTASIS: Todos los periodos ccodori=200 ===")
    periods = c.execute(text("""
        SELECT h.cper, h.cmes, 
               count(DISTINCT h.nasiento) as cabeceras,
               (SELECT count(*) FROM cf_diariol d WHERE d.ccodori='200' AND d.cper=h.cper AND d.cmes=h.cmes) as detalles,
               (SELECT count(*) FROM cf_diario h2 
                LEFT JOIN cf_diariol d2 ON h2.cper=d2.cper AND h2.cmes=d2.cmes AND h2.ccodori=d2.ccodori AND h2.nasiento=d2.nasiento
                WHERE h2.ccodori='200' AND h2.cper=h.cper AND h2.cmes=h.cmes AND d2.nasiento IS NULL) as huerfanas
        FROM cf_diario h
        WHERE h.ccodori='200'
        GROUP BY h.cper, h.cmes
        ORDER BY h.cper, h.cmes
    """)).fetchall()
    for p in periods:
        flag = " *** HUERFANAS ***" if p[4] > 0 else " OK"
        print(f"  {p[0]}-{p[1]}: cabeceras={p[2]}, detalles={p[3]}, huerfanas={p[4]}{flag}")

print("\n=== LOCAL: Estado del staging para subcat 43 ===")
with local_engine.connect() as c:
    estados = c.execute(text("""
        SELECT estado, count(*) FROM cf_diario 
        WHERE company_id=1 AND subcategoria_id=43 AND cper='2026' AND cmes='06'
        GROUP BY estado
    """)).fetchall()
    for e in estados:
        print(f"  cf_diario estado={e[0]}: {e[1]}")
    
    estados_d = c.execute(text("""
        SELECT estado, count(*) FROM cf_diariol 
        WHERE company_id=1 AND subcategoria_id=43 AND cper='2026' AND cmes='06'
        GROUP BY estado
    """)).fetchall()
    for e in estados_d:
        print(f"  cf_diariol estado={e[0]}: {e[1]}")
