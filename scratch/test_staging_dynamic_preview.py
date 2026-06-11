import sys
sys.path.append('c:/SistemaMigConta')
from backend.app.api.endpoints.mapeo import list_cf_diariol
from backend.app.core.database import DestSessionLocal

db = DestSessionLocal()
try:
    print("Testing dynamic list_cf_diariol for company 1, subcat 56...")
    res = list_cf_diariol(
        company_id=1,
        subcategoria_id=56,
        skip=0,
        limit=5,
        db=db
    )
    print("Total rows reported:", res["total"])
    items = res["items"]
    print("Number of items returned:", len(items))
    if len(items) > 0:
        first = items[0]
        print("\nFirst row fields returned to frontend:")
        for k in ["id", "company_id", "subcategoria_id", "cper", "cmes", "nasiento", "nidlin", "idcontrol", "ccodcue", "ndebe", "nhaber", "cglosa", "estado", "subcategoria_nombre"]:
            print(f"  {k}: {first.get(k)}")
        
        print("\nAll keys in payload (including custom columns from cg_entitrib):")
        print(sorted(list(first.keys())))
        
        # Test search filter
        print("\nTesting text search on dynamic fields (e.g. searching 'MARIA' or similar)...")
        res_search = list_cf_diariol(
            company_id=1,
            subcategoria_id=56,
            search="MARIA",
            skip=0,
            limit=5,
            db=db
        )
        print("Search total matches:", res_search["total"])
        if len(res_search["items"]) > 0:
            print("First match crazsoc:", res_search["items"][0].get("crazsoc"))
finally:
    db.close()
