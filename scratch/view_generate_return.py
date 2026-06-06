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
    # Print the last 60 lines of the function (usually where returns/inserts are)
    # Let's find function end by looking for def or @ at start of line
    end_line = start_line + 1
    for j in range(start_line + 1, len(lines)):
        if re.match(r"^(@|def\s)", lines[j]):
            end_line = j
            break
    print(f"Function ends around line {end_line}")
    
    # Print lines that do database insert or return
    for idx in range(start_line, end_line):
        line_content = lines[idx]
        if "insert" in line_content.lower() or "execute(" in line_content.lower() or "return " in line_content.lower() or "bulk_" in line_content.lower():
            print(f"{idx+1}: {line_content.strip()}")
else:
    print("Function not found!")
