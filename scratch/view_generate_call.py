with open("c:\\SistemaMigConta\\backend\\app\\api\\endpoints\\mapeo.py", "r", encoding="utf-8") as f:
    for idx, line in enumerate(f):
        if "_generate_subcategoria" in line and "=" in line:
            print(f"{idx+1}: {line.strip()}")
