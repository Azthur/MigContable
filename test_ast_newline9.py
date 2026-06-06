import pandas as pd
s = pd.Series(["\u200b\nXML: "])
print(repr(s.str.strip().iloc[0]))
