import pandas as pd
import numpy as np

def old_safe_str(s: pd.Series) -> pd.Series:
    return s.fillna('').astype(str).replace({'NaT': '', 'None': '', 'nan': '', '<NA>': ''})

def new_safe_str(s: pd.Series) -> pd.Series:
    # Handle datetime Series converting NaT properly before apply
    if pd.api.types.is_datetime64_any_dtype(s):
        s_str = s.dt.strftime('%Y-%m-%d %H:%M:%S').fillna('')
        return s_str
    return s.apply(lambda x: "" if pd.isna(x) or x is None or str(x).strip() in ['None', 'nan', 'NaT', '<NA>', ''] else str(x))

# Test with datetime series
s_dt = pd.Series([pd.Timestamp('2026-06-01 12:00:00'), pd.NaT, None])
print("DT series:")
try:
    print("Old:", list(old_safe_str(s_dt)))
except Exception as e:
    print("Old failed:", e)

print("New:", list(new_safe_str(s_dt)))

# Test with float series
s_fl = pd.Series([1.2, np.nan, None])
print("\nFloat series:")
print("Old:", list(old_safe_str(s_fl)))
print("New:", list(new_safe_str(s_fl)))
