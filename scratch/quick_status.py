import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from sqlalchemy import create_engine, text

LOCAL_DB = "postgresql://postgres:postgres@localhost:5434/migconta_db"
CONTASIS_DB = "postgresql://postgres:postgres@192.168.2.90:5432/contasis_003"

local_engine = create_engine(LOCAL_DB)
contasis_engine = create_engine(CONTASIS_DB)

with local_engine.connect() as c:
    h = c.execute(text("SELECT count(*) FROM cf_diario WHERE company_id=1 AND subcategoria_id=43 AND cper='2026' AND cmes='06'")).scalar()
    d = c.execute(text("SELECT count(*) FROM cf_diariol WHERE company_id=1 AND subcategoria_id=43 AND cper='2026' AND cmes='06'")).scalar()
    print(f"LOCAL staging 2026-06: cabeceras={h}, detalles={d}")

with contasis_engine.connect() as c:
    h = c.execute(text("SELECT count(*) FROM cf_diario WHERE ccodori='200' AND cper='2026' AND cmes='06'")).scalar()
    d = c.execute(text("SELECT count(*) FROM cf_diariol WHERE ccodori='200' AND cper='2026' AND cmes='06'")).scalar()
    print(f"CONTASIS 2026-06: cabeceras={h}, detalles={d}")
