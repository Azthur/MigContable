
import urllib.request
import json
import sys

BASE_URL = "http://localhost:8001/api/v1"

def get_json(url):
    try:
        with urllib.request.urlopen(url) as response:
            if response.status == 200:
                return json.loads(response.read().decode())
    except Exception as e:
        print(f"Error GET {url}: {e}")
    return None

def post_json(url, data=None):
    try:
        req = urllib.request.Request(url, method='POST')
        if data:
            req.add_header('Content-Type', 'application/json')
            jsondata = json.dumps(data).encode('utf-8')
            req.data = jsondata
            
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                return json.loads(response.read().decode())
    except Exception as e:
        print(f"Error POST {url}: {e}")
    return None

def run_verification():
    print("--- 1. Verification of Companies ---")
    companies = get_json(f"{BASE_URL}/companies/")
    if not companies:
        print("No companies found.")
        return
        
    company = companies[0]
    company_id = company['id']
    print(f"Using Company: {company['name']} (ID: {company_id})")

    print("\n--- 2. Checking Selected Tables ---")
    tables = get_json(f"{BASE_URL}/companies/{company_id}/tables")
    if tables:
        selected = [t for t in tables if t.get('is_selected')]
        print(f"Found {len(selected)} selected tables.")
        for t in selected[:3]:
            print(f" - {t['table_name']} (Incr: {t.get('control_column')})")
            
        if not selected:
             print("No tables selected. Attempting to select 'ANEX' for testing.")
             # Select a table
             # POST /companies/{id}/table-selections
             # Need source connection ID
    
    print("\n--- 3. Running ETL Extraction ---")
    # Using POST with empty body or params
    # Endpoint expects query params: start_date, end_date (REQUIRED)
    url = f"{BASE_URL}/etl/run-etl/?company_id={company_id}&start_date=2024-01-01&end_date=2024-12-31"
    print(f"POST {url}")
    # urllib requires data for POST, even if empty
    res = post_json(url, {}) # Empty dict as body? No, query params are used.
    # But runs as POST.
    
    if res:
        print(f"SUCCESS: {res.get('message')}")
        print(f"Records: {res.get('records')}")
    else:
        print("FAILED Extraction")

if __name__ == "__main__":
    run_verification()
