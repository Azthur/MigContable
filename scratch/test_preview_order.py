import urllib.request
import json
import urllib.error

# We query the local backend port 8000 directly inside uvicorn or port 8080 exposed by Docker
url = "http://localhost:8080/api/v1/mapeo/origen-preview?company_id=1"

try:
    with urllib.request.urlopen(url) as res:
        data = json.loads(res.read().decode("utf-8"))
        print("Received tables in preview:")
        for t in data:
            tname = t["table_name"]
            items = t.get("items", [])
            print(f"\nTable: {tname}")
            if items:
                keys = list(items[0].keys())
                print(f"Columns count: {len(keys)}")
                # Print index of FCHDOC, and the columns around it
                if "fchdoc" in keys:
                    fch_idx = keys.index("fchdoc")
                    print(f"Index of 'fchdoc': {fch_idx}")
                    print("Surrounding columns:")
                    start = max(0, fch_idx - 3)
                    end = min(len(keys), fch_idx + 4)
                    print(keys[start:end])
                else:
                    print("'fchdoc' not found in keys!")
            else:
                print("No records loaded to inspect column order.")
except Exception as e:
    print("Failed to query preview API:", e)
