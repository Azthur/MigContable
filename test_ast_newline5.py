import pandas as pd
s = pd.Series(["PDF: ", "\n", " XML: "])
print(s.str.strip().tolist())
