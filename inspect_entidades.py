import logging
logging.disable(logging.CRITICAL)
from sqlalchemy import text
from backend.app.core.database import DestSessionLocal
from backend.app.models.models import FinalDestConnection
from backend.app.services.connection_manager import ConnectionManager

db = DestSessionLocal()
fc = db.query(FinalDestConnection).filter(FinalDestConnection.company_id == 5, FinalDestConnection.is_active == True).first()
eng = ConnectionManager.get_dest_engine({"host": fc.host, "port": fc.port, "database_name": fc.database_name, "username": fc.username, "password": fc.password})
with eng.connect() as c:
    tabs = c.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND (table_name ILIKE '%enti%' OR table_name ILIKE '%prov%' OR table_name ILIKE '%aux%')")).fetchall()
    print("Tablas candidatas:", [t[0] for t in tabs])
    for t in tabs:
        cols = c.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = :t ORDER BY ordinal_position"), {"t": t[0]}).fetchall()
        print(f"\n{t[0]}: {[x[0] for x in cols][:30]}")
eng.dispose()
db.close()
