import sys
sys.path.append('c:/SistemaMigConta')
from backend.app.core.database import DestSessionLocal
from sqlalchemy import text
db = DestSessionLocal()
with db.bind.connect() as conn:
    res = conn.execute(text("SELECT * FROM ccbrrdoc WHERE c_car = 'N/AB050000015'"))
    rows = res.fetchall()
    if rows:
        keys = res.keys()
        for row in rows:
            print(dict(zip(keys, row)))
    else:
        print('No rows found')
