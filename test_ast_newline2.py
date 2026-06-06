import ast
formula = "CONCAT('PDF: ', '\\n', URLVTA_pdf)"
tree = ast.parse(formula, mode='eval')
print(ast.dump(tree))
