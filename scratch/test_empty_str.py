import pandas as pd

s = pd.Series([], dtype=float)
try:
    print("Direct .str on empty float:")
    s.str.strip()
except Exception as e:
    print("Failed as expected:", e)

try:
    print("\nAfter astype(str):")
    res = s.astype(str)
    print("Dtype:", res.dtype)
    print("Strip result:", list(res.str.strip()))
except Exception as e:
    print("Failed:", e)
