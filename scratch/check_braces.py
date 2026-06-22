with open("scratch/temp_script.js", "r", encoding="utf-8") as f:
    code = f.read()

# Strip out single-line comments, multi-line comments and strings
import re
# Remove single line comments
code_clean = re.sub(r"//.*", "", code)
# Remove multi line comments
code_clean = re.sub(r"/\*.*?\*/", "", code_clean, flags=re.DOTALL)

# Let's count open/close braces
open_braces = code_clean.count("{")
close_braces = code_clean.count("}")
open_parens = code_clean.count("(")
close_parens = code_clean.count(")")
open_brackets = code_clean.count("[")
close_brackets = code_clean.count("]")

print(f"Braces ({{}}): open={open_braces}, close={close_braces}, diff={open_braces - close_braces}")
print(f"Parens (()): open={open_parens}, close={close_parens}, diff={open_parens - close_parens}")
print(f"Brackets ([]): open={open_brackets}, close={close_brackets}, diff={open_brackets - close_brackets}")

# Find any unbalanced braces with context
brace_diff = 0
for i, char in enumerate(code_clean):
    if char == "{":
        brace_diff += 1
    elif char == "}":
        brace_diff -= 1
        if brace_diff < 0:
            print(f"Brace closed before opening around index {i}:")
            print(code_clean[max(0, i-100):i+50])
            break
