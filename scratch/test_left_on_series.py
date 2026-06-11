import os
import sys
# Add parent dir to PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from backend.app.core.formula_parser import evaluate_formula_on_df
from backend.app.core.database import DestSessionLocal

db = DestSessionLocal()
try:
    # Let's construct a dataframe with mixed type in fchdoc
    df = pd.DataFrame({
        "fchdoc": [np.nan, None, "2026-06-01 00:00:00", 2.0, True, 12345]
    })
    print("df:")
    print(df)
    
    # Evaluate LEFT(fchdoc, 10)
    res = evaluate_formula_on_df(df, "LEFT(fchdoc, 10)", db, 1)
    print("\nResult:")
    print(list(res))
    print([type(x) for x in res])
finally:
    db.close()
