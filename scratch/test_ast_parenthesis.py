import ast
import re

def test_formula(formula_str):
    print(f"Testing formula: {repr(formula_str)}")
    formula_str = formula_str.strip()
    formula_str = re.sub(r'["\']([^"\']+)["\'][\'"]+', r"'\1'", formula_str)
    formula_str = re.sub(r'[\'"]+([^"\']+)["\']', r"'\1'", formula_str)
    # Safe replacement of single '=' with '==' only outside string literals
    pattern = r"'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"|(?<![=<>!])=(?![=])"
    def repl(match):
        val = match.group(0)
        if val == '=':
            return '=='
        return val
    formula_ast_str = re.sub(pattern, repl, formula_str)
    formula_ast_str = formula_ast_str.replace('<>', '!=')
    formula_ast_str = formula_ast_str.replace("SUMAR.SI.CONJUNTO", "SUMAR_SI_CONJUNTO")
    formula_ast_str = formula_ast_str.replace("SI.CONJUNTO", "SI_CONJUNTO")
    
    print(f"AST string to parse: {repr(formula_ast_str)}")
    try:
        tree = ast.parse(formula_ast_str, mode='eval')
        print("Successfully parsed!")
    except Exception as e:
        print(f"Failed to parse: {e}")

if __name__ == "__main__":
    test_formula('Y(CodCia="005", O(C_TipoDoc="00")')
