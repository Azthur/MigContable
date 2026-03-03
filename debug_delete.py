import sys
sys.path.append("c:\\SistemaMigConta")
from backend.app.core.database import DestSessionLocal
from backend.app.models.models import CfDiariol

db = DestSessionLocal()

total = db.query(CfDiariol).count()
print(f"Total cf_diariol records: {total}")

to_del = db.query(CfDiariol).filter(
    CfDiariol.estado == "PENDIENTE"
).count()
print(f"Total with PENDIENTE: {to_del}")

# Check distinct cper, cmes
distinct_periods = db.query(CfDiariol.cper, CfDiariol.cmes).distinct().all()
print(f"Distinct periods: {distinct_periods}")

# Just print 1 record
r = db.query(CfDiariol).first()
if r:
    print(f"Sample: id={r.id}, cper='{r.cper}', cmes='{r.cmes}', estado='{r.estado}', subcat_id={r.subcategoria_id}")

