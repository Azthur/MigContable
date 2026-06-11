from backend.app.core.database import DestSessionLocal
from backend.app.models.models import DestinationConnection, SourceConnection, Company

db = DestSessionLocal()
try:
    companies = db.query(Company).all()
    for c in companies:
        print(f"Company: ID={c.id}, Name={c.name}")
        src = db.query(SourceConnection).filter(SourceConnection.company_id == c.id).first()
        if src:
            print(f"  Source Connection: host={src.host}, port={src.port}, database={src.database_name}, username={src.username}")
        else:
            print("  No Source Connection")
        dest = db.query(DestinationConnection).filter(DestinationConnection.company_id == c.id).first()
        if dest:
            print(f"  Dest Connection: host={dest.host}, port={dest.port}, database={dest.database_name}, username={dest.username}")
        else:
            print("  No Dest Connection")
finally:
    db.close()
