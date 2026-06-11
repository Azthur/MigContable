import pandas as pd
import numpy as np

def _safe_str(s: pd.Series) -> pd.Series:
    return s.fillna('').astype(str).replace({'NaT': '', 'None': '', 'nan': '', '<NA>': ''})

# Test case 1: Series with None and dates
s1 = pd.Series([None, '2026-06-01 00:00:00'], dtype=object)
print("s1 dtype object:")
src1 = _safe_str(s1).str.strip()
print("src1:", list(src1), [type(x) for x in src1])

# Test case 2: Series with float NaN
s2 = pd.Series([np.nan, 2.0], dtype=float)
print("\ns2 dtype float:")
src2 = _safe_str(s2).str.strip()
print("src2:", list(src2), [type(x) for x in src2])

# Let's run a zip comprehension like the one in LEFT
n_series = pd.Series([10, 10])
try:
    res = [s[:10] for s in src2]
    print("\nZip comprehension on s2 success:", res)
except Exception as e:
    print("\nZip comprehension on s2 failed:", e)

# What if src is evaluated from eval_ast and returned directly?
# Let's inspect what happens in LEFT implementation
src = _safe_str(s2).str.strip()
n_series = pd.to_numeric(pd.Series([10, 10]), errors='coerce').fillna(0).astype(int)
try:
    res = [s[:max(0, n)] for s, n in zip(src, n_series)]
    print("LEFT success:", res)
except Exception as e:
    print("LEFT failed:", e)
