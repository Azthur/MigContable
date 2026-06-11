import sys
sys.path.append('c:/SistemaMigConta')
from backend.app.core.database import DestSessionLocal
from backend.app.models.models import User

db = DestSessionLocal()
try:
    users = db.query(User).all()
    for u in users:
        print(f"Email: {u.email}, Name: {u.full_name}, Role: {u.role}, Active: {u.is_active}")
finally:
    db.close()
