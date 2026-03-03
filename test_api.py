import urllib.request
import urllib.error
import json

url = 'http://127.0.0.1:8000/api/v1/mapeo/generate-to-cf-diariol'
data = json.dumps({'subcategoria_id': 4, 'periodo': '2026', 'mes': '01'}).encode('utf-8')
headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

req = urllib.request.Request(url, data=data, headers=headers, method='POST')

try:
    with urllib.request.urlopen(req) as response:
        print('STATUS:', response.status)
        print('BODY:', response.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print('HTTP ERROR:', e.code)
    try:
        print('BODY:', e.read().decode('utf-8'))
    except Exception as re:
        print('Could not read error body:', re)
except Exception as e:
    print('OTHER ERROR:', e)
