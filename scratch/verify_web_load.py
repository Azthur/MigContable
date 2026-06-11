import urllib.request

try:
    url = "http://localhost:8080/companies/1"
    print(f"Requesting GET {url}...")
    with urllib.request.urlopen(url) as response:
        print(f"Response status: {response.status}")
        if response.status == 200:
            print("SUCCESS! The page loaded correctly.")
            # Read first few lines of response to confirm
            html = response.read(500).decode()
            print("Snippet:")
            print(html)
        else:
            print(f"Failed loading page. Status: {response.status}")
except Exception as e:
    print(f"Error requesting page: {e}")
