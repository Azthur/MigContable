import sys
sys.path.append('c:/SistemaMigConta')
from backend.app.core.database import DestSessionLocal
import pandas as pd
from backend.app.api.endpoints.etl import __apply_computed_rules

df = pd.DataFrame([{
    "C_car": "N/AB050000015",
    "coddoc": "N/A"
}])

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
    DummyRule("fchdoc", "C_car", "", "BUSCARX_EXT(C_car, ccbrgdoc, C_car, fchdoc)", 3),
    DummyRule("C_fechaNC", "C_car", "", "BUSCARX_EXT(C_car, ccbrgdoc, C_car, C_fechaNC)", 37),
    DummyRule("C_fechaEmision", "", "", "LEFT(fchdoc, 10)", 48),
    DummyRule("C_fechaNC_Contasis", "", "", "SI.CONJUNTO(coddoc=\"N/A \",LEFT(C_fechaNC, 10),\" \")", 49)
]

__apply_computed_rules(df, rules, db, 1, "ccbrrdoc")

print("--- Dataframe ---")
print(df[["C_car", "coddoc", "fchdoc", "C_fechaNC", "C_fechaEmision", "C_fechaNC_Contasis"]].to_dict('records'))
