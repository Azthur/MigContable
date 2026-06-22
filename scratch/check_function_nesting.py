import re

with open("scratch/temp_script.js", "r", encoding="utf-8") as f:
    code = f.read()

# Strip comments and strings
code_clean = re.sub(r"//.*", "", code)
code_clean = re.sub(r"/\*.*?\*/", "", code_clean, flags=re.DOTALL)

# Track braces and find function definitions
lines = code_clean.split("\n")
brace_level = 0
for idx, line in enumerate(lines):
    # Count braces in this line
    opens = line.count("{")
    closes = line.count("}")
    
    # Check if a function is defined on this line
    func_match = re.search(r"function\s+(\w+)\s*\(", line)
    if func_match:
        func_name = func_match.group(1)
        print(f"Line {idx+1}: Function '{func_name}' defined at brace level {brace_level}")
        
    brace_level += opens - closes
