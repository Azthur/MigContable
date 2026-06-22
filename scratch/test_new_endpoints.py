import urllib.request
import json
import sys
from urllib.parse import urlencode

base_url = "http://localhost:8080/api/v1"

# 1. Login to get token
login_url = f"{base_url}/auth/login"
login_data = urlencode({
    "username": "admin@migconta.com",
    "password": "admin123"
}).encode("utf-8")

headers = {
    "Content-Type": "application/x-www-form-urlencoded"
}

req = urllib.request.Request(login_url, data=login_data, headers=headers, method="POST")
try:
    with urllib.request.urlopen(req) as res:
        login_res = json.loads(res.read().decode("utf-8"))
        token = login_res["access_token"]
        print("Login SUCCESS. Token acquired.")
except Exception as e:
    print("Login FAILED:", e)
    sys.exit(1)

auth_headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

company_id = 4
subcat_id = 63
idcontrol = "588"

# 2. Test GET /raw-row-detail
try:
    print("\n--- Testing GET /etl/raw-row-detail ---")
    detail_url = f"{base_url}/etl/raw-row-detail?company_id={company_id}&subcategoria_id={subcat_id}&idcontrol={idcontrol}"
    req = urllib.request.Request(detail_url, headers=auth_headers, method="GET")
    with urllib.request.urlopen(req) as res:
        detail_res = json.loads(res.read().decode("utf-8"))
        print("Raw Row Detail GET SUCCESS.")
        print("Source Table:", detail_res.get("source_table"))
        print("Headers Count:", len(detail_res.get("headers", [])))
        print("Row keys:", list(detail_res.get("row", {}).keys())[:5])
        print("Sample Row Value (cglosa):", detail_res.get("row", {}).get("cglosa") or detail_res.get("row", {}).get("cglosa1"))
except Exception as e:
    print("Raw Row Detail GET FAILED:", e)
    if hasattr(e, 'read'):
        print("Body:", e.read().decode('utf-8'))

# 3. Setup a staging row as MIGRADO to test reset
# We can do this directly in local staging DB
print("\n--- Setting up staging row 587 as MIGRADO for reset testing ---")
from backend.app.core.database import DestSessionLocal
from sqlalchemy import text
db = DestSessionLocal()
try:
    db.execute(text("UPDATE cf_diariol SET estado = 'MIGRADO' WHERE company_id = 4 AND subcategoria_id = 63 AND idcontrol = '587'"))
    db.commit()
    print("Staging row 587 status updated to MIGRADO in database.")
finally:
    db.close()

# 4. Test POST /reset-migrated-row
try:
    print("\n--- Testing POST /etl/reset-migrated-row ---")
    reset_url = f"{base_url}/etl/reset-migrated-row"
    payload = json.dumps({
        "company_id": company_id,
        "subcategoria_id": subcat_id,
        "idcontrol": "587"
    }).encode("utf-8")
    
    req = urllib.request.Request(reset_url, data=payload, headers=auth_headers, method="POST")
    with urllib.request.urlopen(req) as res:
        reset_res = json.loads(res.read().decode("utf-8"))
        print("Reset Migrated Row POST SUCCESS.")
        print("Response status:", reset_res.get("status"))
        print("Response message:", reset_res.get("message"))
        print("Affected Rows:", reset_res.get("affected_rows"))
        
    # Verify status is back to '1' (Pending) in staging DB
    db = DestSessionLocal()
    try:
        row_state = db.execute(text("SELECT estado FROM cf_diariol WHERE company_id = 4 AND subcategoria_id = 63 AND idcontrol = '587' LIMIT 1")).scalar()
        print("Verified row status in staging DB is now:", row_state)
        assert row_state == '1', f"Expected status '1', got '{row_state}'"
        print("Verification SUCCESS: Staging row reset correctly back to '1'.")
    finally:
        db.close()
except Exception as e:
    print("Reset Migrated Row FAILED:", e)
    if hasattr(e, 'read'):
        print("Body:", e.read().decode('utf-8'))
