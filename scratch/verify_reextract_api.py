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

# 2. Get active company
try:
    req = urllib.request.Request(f"{base_url}/companies", headers=auth_headers, method="GET")
    with urllib.request.urlopen(req) as res:
        companies = json.loads(res.read().decode("utf-8"))
        active_companies = [c for c in companies if c.get("is_active")]
        if not active_companies:
            print("No active companies found.")
            sys.exit(1)
        company_id = active_companies[0]["id"]
        company_name = active_companies[0]["name"]
        print(f"Using company: {company_name} (ID: {company_id})")
except Exception as e:
    print("Fetch companies FAILED:", e)
    sys.exit(1)

subcat_id = 63
subcat_name = "204-Registro de Compras - YLV Industrias"
print(f"Forced subcategory: {subcat_name} (ID: {subcat_id})")

# 4. Test GET /reextract-preview
try:
    print("\n--- Testing GET /reextract-preview ---")
    preview_url = f"{base_url}/etl/reextract-preview?company_id={company_id}&subcategoria_id={subcat_id}"
    req = urllib.request.Request(preview_url, headers=auth_headers, method="GET")
    with urllib.request.urlopen(req) as res:
        preview_res = json.loads(res.read().decode("utf-8"))
        print("Preview GET SUCCESS.")
        print(f"Subcategory Name: {preview_res.get('subcategory_name')}")
        print(f"Source Table: {preview_res.get('source_table')}")
        items = preview_res.get('items', [])
        print(f"Pending/Error Items Count: {len(items)}")
        if items:
            first_item = items[0]
            print(f"Example Staging Item: idcontrol={first_item.get('idcontrol')}, nasiento={first_item.get('nasiento')}, status={first_item.get('staging_status')}")
            print(f"Row Exists in Intermediate Table: {first_item.get('raw_exists')}")
            if first_item.get('raw_exists'):
                print(f"Raw Info: {first_item.get('raw_info')}")
except Exception as e:
    print("Preview GET FAILED:", e)

# 5. Test POST /reextract-reprocess
import urllib.error
try:
    print("\n--- Testing POST /reextract-reprocess ---")
    reprocess_url = f"{base_url}/etl/reextract-reprocess"
    payload = json.dumps({
        "company_id": company_id,
        "subcategoria_id": subcat_id
    }).encode("utf-8")
    
    req = urllib.request.Request(reprocess_url, data=payload, headers=auth_headers, method="POST")
    with urllib.request.urlopen(req) as res:
        reprocess_res = json.loads(res.read().decode("utf-8"))
        print("Reprocess POST SUCCESS.")
        print("Response status:", reprocess_res.get("status"))
        print("Response message:", reprocess_res.get("message"))
        print("Details:", json.dumps(reprocess_res.get("details"), indent=2))
except urllib.error.HTTPError as e:
    print("Reprocess POST HTTP ERROR:", e)
    try:
        body = e.read().decode("utf-8")
        print("Response Body:", body)
    except Exception as e_read:
        print("Could not read response body:", e_read)
except Exception as e:
    print("Reprocess POST FAILED:", e)
