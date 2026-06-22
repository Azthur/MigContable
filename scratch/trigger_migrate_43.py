import urllib.request
import json
import sys
from urllib.parse import urlencode

base_url = "http://localhost:8080/api/v1"

# 1. Login
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

# 2. Trigger migration for subcat 43
url = f"{base_url}/mapeo/migrate-to-final/1?subcategoria_id=43"
req = urllib.request.Request(url, headers=auth_headers, method="POST")

try:
    print("Triggering migration to final for subcategory 43...")
    with urllib.request.urlopen(req) as res:
        result = json.loads(res.read().decode("utf-8"))
        print("Migration response:")
        print(json.dumps(result, indent=2))
except Exception as e:
    import urllib.error
    if isinstance(e, urllib.error.HTTPError):
        print("Migration FAILED (HTTPError):", e.code, e.reason)
        print("Response body:", e.read().decode("utf-8"))
    else:
        print("Migration FAILED:", e)
