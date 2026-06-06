import pandas as pd
s = pd.Series([" \n XML: "])
print(s.str.strip().tolist())
