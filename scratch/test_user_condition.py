import pandas as pd
from backend.app.core.formula_parser import evaluate_formula_on_df
from sqlalchemy.orm import Session

# Setup mock dataframe matching the user's database values
df = pd.DataFrame([
    {
        "CodCia": "005",
        "C_TipoDoc": "01",
        "C_mes": "06",
        "C_periodo": "2026",
        "idcontrol": "359"
    },
    {
        "CodCia": "004",
        "C_TipoDoc": "01",
        "C_mes": "06",
        "C_periodo": "2026",
        "idcontrol": "360"
    },
    {
        "CodCia": "005",
        "C_TipoDoc": "03",
        "C_mes": "06",
        "C_periodo": "2026",
        "idcontrol": "361"
    },
    {
        "CodCia": "005",
        "C_TipoDoc": "14",
        "C_mes": "06",
        "C_periodo": "2026",
        "idcontrol": "362"
    }
])

formula = 'Y(CodCia="005", O(C_TipoDoc="01",C_TipoDoc="14"))'

print("Mock DataFrame:")
print(df)

print("\nEvaluating formula...")
# Pass None for db since the formula doesn't need database queries (no BUSCARX or BUSCARX_EXT)
res = evaluate_formula_on_df(df, formula, None, 4, default=False)
print("Result Series:")
print(res)
