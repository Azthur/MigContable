import urllib.request
import json
import sys

BASE_URL = "http://localhost:8080/api/v1"

def test_etl():
    company_id = 1
    print(f"Triggering ETL for company {company_id}...")
    url = f"{BASE_URL}/etl/run-etl/?company_id={company_id}&full_refresh=true"
    
    try:
        req = urllib.request.Request(url, method='POST')
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                res = json.loads(response.read().decode())
                print("ETL Triggered successfully!")
                print(json.dumps(res, indent=2))
            else:
                print(f"Failed to trigger ETL, status: {response.status}")
    except Exception as e:
        print(f"Error calling run-etl: {e}")

if __name__ == "__main__":
    test_etl()
