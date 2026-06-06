import re

with open("c:\\SistemaMigConta\\backend\\app\\api\\endpoints\\mapeo.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Find _generate_subcategoria_cf_diariol start line
start_line = -1
for i, line in enumerate(lines):
    if "def _generate_subcategoria_cf_diariol" in line:
        start_line = i
        break

if start_line != -1:
    print(f"Found _generate_subcategoria_cf_diariol at line {start_line + 1}")
    # Print lines that assign DetTable
    for idx in range(start_line, start_line + 200):
        line_content = lines[idx]
        if "DetTable" in line_content or "diariol_entries" in line_content:
            print(f"{idx+1}: {line_content.strip()}")
else:
    print("Function not found!")
