import requests
try:
    r = requests.get("http://localhost:8080/api/v1/mapeo/categorias")
    print("Status:", r.status_code)
    print("Body:", r.text[:1000])
except Exception as e:
    print("Exception:", e)
