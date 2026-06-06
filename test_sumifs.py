import pandas as pd
import numpy as np
import ast
import sys
sys.path.append("c:\\SistemaMigConta")
from backend.app.core.formula_parser import evaluate_formula_on_df

df = pd.DataFrame({
    'VENTA': [100, 200, 300, 400],
    'TIPO': ['A', 'A', 'B', 'B'],
    'TARGET_TIPO': ['A', 'B', 'A', 'A']
}, index=[10, 20, 30, 40])

formula = "SUMAR.SI.CONJUNTO(VENTA, TIPO, TARGET_TIPO)"

# First, need to apply my logic locally just to be sure
def my_logic(df, args):
    sum_range = df[args[0]]
    tmp_df = pd.DataFrame({'_sum': sum_range.values})
    lookup_keys = []
    merge_keys = []
    for i in range(1, len(args), 2):
        c_range = df[args[i]].astype(str).str.strip().str.upper()
        c_val = df[args[i+1]].astype(str).str.strip().str.upper()
        range_col = f'_range_{i}'
        val_col = f'_val_{i}'
        tmp_df[range_col] = c_range.values
        tmp_df[val_col] = c_val.values
        lookup_keys.append(range_col)
        merge_keys.append(val_col)
    
    grouped = tmp_df.groupby(lookup_keys)['_sum'].sum().reset_index()
    tmp_df['_row_idx'] = np.arange(len(tmp_df))
    merged = pd.merge(
        tmp_df,
        grouped,
        left_on=merge_keys,
        right_on=lookup_keys,
        how='left',
        suffixes=('', '_grouped')
    )
    merged = merged.sort_values('_row_idx')
    return pd.Series(merged['_sum_grouped'].fillna(0).values, index=df.index)

print(my_logic(df, ['VENTA', 'TIPO', 'TARGET_TIPO']).tolist())
