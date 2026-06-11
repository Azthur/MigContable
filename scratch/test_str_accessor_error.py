import pandas as pd
import numpy as np

def old_safe_str(s: pd.Series) -> pd.Series:
    return s.fillna('').astype(str).replace({'NaT': '', 'None': '', 'nan': '', '<NA>': ''})

def new_safe_str(s: pd.Series) -> pd.Series:
    if pd.api.types.is_datetime64_any_dtype(s):
        return s.dt.strftime('%Y-%m-%d %H:%M:%S').fillna('')
    return s.apply(lambda x: "" if pd.isna(x) or x is None or str(x).strip() in ['None', 'nan', 'NaT', '<NA>', ''] else str(x))

# Let's create a float Series with NaNs
s = pd.Series([12.0, np.nan, 18.0])

# Using new_safe_str
res_new = new_safe_str(s)
print("res_new dtype:", res_new.dtype)
print("res_new types:", [type(x) for x in res_new])

try:
    print("new strip:", list(res_new.str.strip()))
except Exception as e:
    print("new strip failed:", e)

# Wait! What if we do:
s_all_nan = pd.Series([np.nan, np.nan])
res_all_nan = new_safe_str(s_all_nan)
print("\nres_all_nan dtype:", res_all_nan.dtype)
print("res_all_nan types:", [type(x) for x in res_all_nan])
try:
    print("all nan strip:", list(res_all_nan.str.strip()))
except Exception as e:
    print("all nan strip failed:", e)
