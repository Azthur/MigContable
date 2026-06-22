import re
import subprocess
import sys

html_path = "backend/app/templates/realtime_etl.html"
js_path = "scratch/temp_script.js"

try:
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()
except Exception as e:
    print("Could not read HTML file:", e)
    sys.exit(1)

# Find all script blocks
scripts = re.findall(r"<script>(.*?)</script>", html, re.DOTALL)
if not scripts:
    print("No script blocks found in HTML.")
    sys.exit(0)

# Combine script blocks
combined_js = "\n".join(scripts)

# Replace Jinja2 templates with mock values to avoid JS syntax errors
# Jinja expressions look like {{ ... }} or {% ... %}
combined_js = re.sub(r"\{\{.*?\}\}", "null", combined_js)
combined_js = re.sub(r"\{%.*?%\}", "", combined_js)

try:
    with open(js_path, "w", encoding="utf-8") as f:
        f.write(combined_js)
    print(f"Extracted JS block written to {js_path}.")
except Exception as e:
    print("Could not write JS file:", e)
    sys.exit(1)

# Check syntax using node
try:
    res = subprocess.run(["node", "--check", js_path], capture_output=True, text=True)
    if res.returncode == 0:
        print("JavaScript syntax is VALID (no parsing errors found by Node).")
    else:
        print("JavaScript syntax is INVALID. Node check output:")
        print(res.stderr)
        print(res.stdout)
except Exception as e:
    print("Could not run node check:", e)
