with open("c:\\SistemaMigConta\\scratch\\test_verify_generate_fresh.log", "r", encoding="utf-16") as f:
    for idx, line in enumerate(f):
        # Print errors, warnings, exceptions, and key status messages
        lower_line = line.lower()
        if "error" in lower_line or "exception" in lower_line or "fail" in lower_line or "det_cols" in lower_line or "rows inserted" in lower_line or "headers count" in lower_line or "cargando esquema" in lower_line:
            print(f"{idx+1}: {line.strip()}")
