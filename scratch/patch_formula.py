import re

with open('c:/SistemaMigConta/backend/app/core/formula_parser.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Insert _safe_str
safe_str_def = '''    def eval_ast(node: ast.AST) -> pd.Series:
        def _safe_str(s: pd.Series) -> pd.Series:
            return s.fillna('').astype(str).replace({'NaT': '', 'None': '', 'nan': '', '<NA>': ''})
'''
if 'def _safe_str' not in code:
    code = code.replace('    def eval_ast(node: ast.AST) -> pd.Series:', safe_str_def)

# Replace .fillna('').astype(str) where it's called on val or eval_ast(...)
code = re.sub(r'val\.fillna\(\'\'\)\.astype\(str\)', r'_safe_str(val)', code)
code = re.sub(r'eval_ast\(([^)]+)\)\.fillna\(\'\'\)\.astype\(str\)', r'_safe_str(eval_ast(\1))', code)

# Replace .astype(str) in cases where it isn't part of .fillna('').astype(str) but we want to intercept NaT
# Left & Right in Compare:
code = re.sub(r'left\.astype\(str\)', r'_safe_str(left)', code)
code = re.sub(r'right\.astype\(str\)', r'_safe_str(right)', code)
# mask Y/O:
code = re.sub(r'val\.astype\(str\)', r'_safe_str(val)', code)
# SUMAR.SI.CONJUNTO c_range, c_val
code = re.sub(r'c_range = eval_ast\([^)]+\)\.astype\(str\)', lambda m: m.group(0).replace('.astype(str)', '._safe_str()').replace('._safe_str()', '') + " # hand replaced", code) # Wait, better to just use re.sub for all `eval_ast(x).astype(str)`
code = re.sub(r'eval_ast\(([^)]+)\)\.astype\(str\)', r'_safe_str(eval_ast(\1))', code)
# search/source in ENCONTRAR
code = re.sub(r'search\.astype\(str\)', r'_safe_str(search)', code)
code = re.sub(r'source\.astype\(str\)', r'_safe_str(source)', code)
# src in TEXTO, BUSCARX...
code = re.sub(r'src\.astype\(str\)', r'_safe_str(src)', code)

# Fix SI_CONJUNTO np.select string issue
si_conjunto_fix = '''                    default_val = default if default else ""
                    arr = np.select(masks, choices, default=default_val)
                    res_series = pd.Series(arr, index=df.index)
                    # Convert to numeric if possible to prevent object array issues
                    res_series = pd.to_numeric(res_series, errors='ignore')
                    return res_series'''

code = code.replace('''                    default_val = default if default else ""
                    arr = np.select(masks, choices, default=default_val)
                    return pd.Series(arr, index=df.index)''', si_conjunto_fix)

with open('c:/SistemaMigConta/backend/app/core/formula_parser.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Patch applied")
