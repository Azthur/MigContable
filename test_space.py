import re
import ast

formula_str = "SI.CONJUNTO(ENCONTRAR('-', COL1)>0, EXTRAER(COL1, 1, RESTA(ENCONTRAR('-', COL1), 1)), ENCONTRAR('-', COL1)=0, ' ')"
print('0:', formula_str)
formula_str = formula_str.strip()
print('1:', formula_str)
formula_str = re.sub(r'["\']([^"\']+)["\'][\'"]+', r"'\1'", formula_str)
print('2:', formula_str)
formula_str = re.sub(r'[\'"]+([^"\']+)["\']', r"'\1'", formula_str)
print('3:', formula_str)
formula_ast_str = re.sub(r'(?<![=<>!])=(?![=])', '==', formula_str)
formula_ast_str = formula_ast_str.replace('<>', '!=')
formula_ast_str = formula_ast_str.replace('SI.CONJUNTO', 'SI_CONJUNTO')
print('4:', formula_ast_str)

try:
    ast.parse(formula_ast_str, mode='eval')
    print('AST parse SUCCESS')
except Exception as e:
    print('AST parse ERROR:', e)
