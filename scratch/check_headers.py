import urllib.request

url = "http://localhost:8080/api/v1/companies/"
req = urllib.request.Request(url)
with urllib.request.urlopen(req) as resp:
    print("=== Response Headers ===")
    for header, value in resp.getheaders():
        if header.lower() in ('cache-control', 'pragma', 'expires'):
            print(f"  {header}: {value}")
    
    print("\n=== Status ===")
    print(f"  HTTP {resp.status}")
