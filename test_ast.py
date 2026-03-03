import ast
import re
import traceback

formula = "CONCAT(SI.CONJUNTO(coddoc='N/A', LEFT(codref, 1), coddoc='N/A', LEFT(coddoc, 1)),LEFT(nrodoc, 3))"
formula_ast_str = re.sub(r'(?<![=<>!])=(?![=])', '==', formula.strip())
formula_ast_str = formula_ast_str.replace("SI.CONJUNTO", "SI_CONJUNTO")

print(f"AST String: {formula_ast_str}")
try:
    tree = ast.parse(formula_ast_str, mode='eval')
    print("PARSE SUCCESS: ", ast.dump(tree))
except Exception as e:
    print("PARSE ERROR!")
    traceback.print_exc()

