import sys
sys.path.append('c:/SistemaMigConta')
from backend.app.core.database import DestSessionLocal
import pandas as pd
from backend.app.api.endpoints.etl import __apply_computed_rules

# Test with a missing key so BUSCARX_EXT returns NaT
df = pd.DataFrame({"CodCia": ["01"], "CodDoc": ["03"], "NroDoc": ["B050-0000016"]})

# Create engine/db
db = DestSessionLocal()

class DummyRule:
    def __init__(self, c, s, r, v, p):
        self.new_column_name = c
        self.source_column = s
        self.result_value = r
        self.condition_value = v
        self.priority = p
        self.default_value = None

rules = [
    DummyRule("C_car", "", "", "CONCAT(CodDoc, NroDoc)", 1),
    DummyRule("fchdoc", "C_car", "", "BUSCARX_EXT(C_car, ccbrgdoc, C_car, fchdoc)", 3),
    DummyRule("C_fechaEmision", "", "", "LEFT(fchdoc, 10)", 48)
]

__apply_computed_rules(df, rules, db, 1, "ccbrrdoc")

print(df[["C_car", "fchdoc", "C_fechaEmision"]].to_dict('records'))
