from backend.app.core.database import DestSessionLocal
from backend.app.models.models import EtlEjecucion

session = DestSessionLocal()
errors = session.query(EtlEjecucion).filter(EtlEjecucion.status == 'ERROR').order_by(EtlEjecucion.started_at.desc()).limit(5).all()

for e in errors:
    msg = e.error_message[:200] if e.error_message else 'None'
    print(f'ID: {e.id}, Empresa: {e.empresa_id}, Error: {msg}')
    if e.error_traceback:
        print(f'Traceback: {e.error_traceback[:300]}')
    print('---')

session.close()
