import numpy as np
import pandas as pd

masks = [pd.Series([True, False, False])]
choices = [pd.Series(['A', 'B', 'C'])]
default_val = pd.Series(['X', 'Y', 'Z'])

res = np.select(masks, choices, default=default_val)
print(list(res))
