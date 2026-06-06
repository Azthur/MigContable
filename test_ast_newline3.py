import ast
formula = r"CONCAT('PDF: ', '\n', URLVTA_pdf)"
tree = ast.parse(formula, mode='eval')
print(repr(tree.body.args[1].value))
