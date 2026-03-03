import urllib.request
import urllib.error
import json
import sys

BASE_URL = "http://localhost:8001/api/v1"

def get_json(url):
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        print(f"Error GET {url}: {e.code} {e.reason}")
        print(e.read().decode())
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
                res = response.read().decode()
                print("Response:", res)
                return json.loads(res)
    except urllib.error.HTTPError as e:
        print(f"Error POST {url}: {e.code} {e.reason}")
        print("Body:", e.read().decode())
    except Exception as e:
        print(f"Error POST {url}: {e}")
    return None

def run():
    print("Fetching table selections...")
    # Use the endpoint that returns tables with is_selected
    tables = get_json(f"{BASE_URL}/companies/1/tables")
    if not tables:
        print("No tables found")
        return

    # Find the backend ID for the selection
    # The endpoint returns list of schemas.TableInfo
    # It has 'selection_id' field if selected
    
    selected = [t for t in tables if t.get('is_selected')]
    if not selected:
        print("No selected tables")
        return

    target = selected[0]
    sel_id = target.get('selection_id')
    print(f"Targeting table: {target['table_name']} (ID: {sel_id})")
    
    # Run Sync Integration
    url = f"{BASE_URL}/etl/run-incremental/1/{sel_id}"
    print(f"Calling {url}...")
    res = post_json(url, {})

if __name__ == "__main__":
    run()
