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

# 2. Get list of companies
try:
    req = urllib.request.Request(f"{base_url}/companies", headers=auth_headers, method="GET")
    with urllib.request.urlopen(req) as res:
        companies = json.loads(res.read().decode("utf-8"))
        print(f"Companies fetched: {len(companies)}")
        if not companies:
            print("No companies found. Create one first.")
            sys.exit(1)
        active_companies = [c for c in companies if c.get("is_active")]
        if not active_companies:
            print("No active companies found. Create or activate one first.")
            sys.exit(1)
        company_id = active_companies[0]["id"]
        company_name = active_companies[0]["name"]
        print(f"Using active company: {company_name} (ID: {company_id})")
except Exception as e:
    print("Fetch companies FAILED:", e)
    sys.exit(1)

# 3. Get categories / subcategories of that company to configure a correlative
subcat_id = None
try:
    req = urllib.request.Request(f"{base_url}/mapeo/categorias?company_id={company_id}", headers=auth_headers, method="GET")
    with urllib.request.urlopen(req) as res:
        cats = json.loads(res.read().decode("utf-8"))
        print(f"Categories fetched: {len(cats)}")
        for cat in cats:
            if cat.get("subcategorias"):
                subcat_id = cat["subcategorias"][0]["id"]
                subcat_name = cat["subcategorias"][0]["nombre"]
                print(f"Using subcategory: {subcat_name} (ID: {subcat_id})")
                break
        if not subcat_id:
            print("No subcategories found for company. Creating correlativo test might fail/skip.")
except Exception as e:
    print("Fetch categories FAILED:", e)

# 4. CRUD Correlativos
if subcat_id:
    # A. List
    try:
        req = urllib.request.Request(f"{base_url}/etl/correlativos", headers=auth_headers, method="GET")
        with urllib.request.urlopen(req) as res:
            corrs = json.loads(res.read().decode("utf-8"))
            print(f"Correlativos count: {len(corrs)}")
    except Exception as e:
        print("List correlativos FAILED:", e)

    # B. Create
    import random
    random_period = str(random.randint(2100, 2900))
    corr_data = json.dumps({
        "company_id": company_id,
        "subcategoria_id": subcat_id,
        "periodo": random_period,
        "mes": "06",
        "asiento_inicial": 100
    }).encode("utf-8")
    
    corr_id = None
    try:
        req = urllib.request.Request(f"{base_url}/etl/correlativos", data=corr_data, headers=auth_headers, method="POST")
        with urllib.request.urlopen(req) as res:
            create_res = json.loads(res.read().decode("utf-8"))
            corr_id = create_res["id"]
            print(f"Create correlativo SUCCESS. ID: {corr_id}")
    except Exception as e:
        print("Create correlativo FAILED:", e)

    # C. Update
    if corr_id:
        update_data = json.dumps({
            "asiento_inicial": 150,
            "asiento_actual": 149
        }).encode("utf-8")
        try:
            req = urllib.request.Request(f"{base_url}/etl/correlativos/{corr_id}", data=update_data, headers=auth_headers, method="PUT")
            with urllib.request.urlopen(req) as res:
                print("Update correlativo SUCCESS:", res.read().decode("utf-8"))
        except Exception as e:
            print("Update correlativo FAILED:", e)

        # D. Delete
        try:
            req = urllib.request.Request(f"{base_url}/etl/correlativos/{corr_id}", headers=auth_headers, method="DELETE")
            with urllib.request.urlopen(req) as res:
                print("Delete correlativo SUCCESS:", res.read().decode("utf-8"))
        except Exception as e:
            print("Delete correlativo FAILED:", e)

# 5. Run Realtime ETL manually
run_data = json.dumps({
    "company_id": company_id
}).encode("utf-8")
try:
    print("Triggering run-realtime ETL...")
    req = urllib.request.Request(f"{base_url}/etl/run-realtime", data=run_data, headers=auth_headers, method="POST")
    with urllib.request.urlopen(req) as res:
        run_res = json.loads(res.read().decode("utf-8"))
        print("Run Realtime ETL finished.")
        print("Results:")
        print(json.dumps(run_res, indent=2))
except Exception as e:
    print("Run Realtime ETL FAILED:", e)

# 6. Read logs
try:
    req = urllib.request.Request(f"{base_url}/etl/realtime-logs", headers=auth_headers, method="GET")
    with urllib.request.urlopen(req) as res:
        logs = json.loads(res.read().decode("utf-8"))
        print(f"Realtime execution logs count: {len(logs)}")
        if logs:
            print("Latest log summary:", logs[0]["message"])
except Exception as e:
    print("List realtime logs FAILED:", e)
