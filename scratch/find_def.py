import re

with open("c:\\SistemaMigConta\\backend\\app\\api\\endpoints\\mapeo.py", "r", encoding="utf-8") as f:
    content = f.read()

print("File length:", len(content))
matches = re.findall(r"def\s+([a-zA-Z0-9_]+)", content)
print("Found functions:", len(matches))
for m in matches:
    if "generate" in m or "subcategoria" in m:
        print("  Match:", m)
