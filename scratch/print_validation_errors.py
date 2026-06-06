with open("c:\\SistemaMigConta\\scratch\\test_verify_generate_fresh.log", "r", encoding="utf-16") as f:
    for line in f:
        if "Err:" in line or "validation error" in line.lower() or "error" in line.lower():
            if "sqlalchemy.engine" not in line and "pandas" not in line and "fragmented" not in line and "loc" not in line:
                print(line.strip())
