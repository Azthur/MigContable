with open(r'c:\SistemaMigConta\backend\app\templates\realtime_etl.html', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 'card' in l or 'Section:' in l or 'modal' in l:
        print(f"{i+1}: {l.strip()}")
