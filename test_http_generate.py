import requests
import json

url = "http://localhost:8000/api/v1/mapeo/generate-to-cf-diariol"
body = {
    "company_id": 1,
    "clear_previous": True
}

try:
    print("Sending POST to", url)
    res = requests.post(url, json=body)
    print("Status Code:", res.status_code)
    print("Response JSON:", json.dumps(res.json(), indent=2))
except Exception as e:
    print("Error:", e)
