import pandas as pd
s = pd.Series([" \nXML: "])
print(repr(s.str.strip().iloc[0]))
