import pandas as pd
import sys
sys.path.insert(0, '.')

from sqlalchemy import create_engine

engine = create_engine("postgresql://postgres:postgres@127.0.0.1:5434/migconta_db")

df = pd.read_sql('SELECT * FROM "tbl_conciliados" LIMIT 100', engine)
print(f"Total rows: {len(df)}")
print(f"Columns: {list(df.columns)}")
print(f"\nDistinct empresa values: {df['empresa'].unique()}")
print(f"Distinct IdCobranza_CodCia values: {df['IdCobranza_CodCia'].unique()}")

# Now manually simulate the formula
formula = 'Y(empresa="002", O(IdCobranza_CodCia="007", IdCobranza_CodCia="005", IdCobranza_CodCia="003",IdCobranza_CodCia="001", IdCobranza_CodCia="004"))'

from backend.app.core.formula_parser import evaluate_formula_on_df

class FakeDB:
    def query(self, *a, **kw):
        return self
    def filter(self, *a, **kw):
        return self
    def first(self):
        return None

result = evaluate_formula_on_df(df, formula, FakeDB(), 1, default=False)
print(f"\nFormula result type: {type(result)}")
print(f"Formula result dtype: {result.dtype}")
print(f"Formula result value_counts:\n{result.value_counts()}")

# Apply the mask like mapeo.py does
mask = pd.to_numeric(result, errors='coerce').fillna(0).astype(bool) | (result.astype(str).str.strip().str.upper() == 'TRUE')
filtered = df[mask]
print(f"\nFiltered rows: {len(filtered)}")
if not filtered.empty:
    print(filtered[['empresa', 'IdCobranza_CodCia']].head(10))
else:
    print("*** NO ROWS PASSED THE CONDITION ***")
    # Debug: check individual parts
    print("\n--- DEBUG individual parts ---")
    emp_mask = df['empresa'].astype(str).str.strip().str.upper() == '002'
    print(f"empresa='002': {emp_mask.sum()} rows match")
    
    codcia_vals = ['007', '005', '003', '001', '004']
    codcia_mask = df['IdCobranza_CodCia'].astype(str).str.strip().str.upper().isin(codcia_vals)
    print(f"IdCobranza_CodCia IN {codcia_vals}: {codcia_mask.sum()} rows match")
    
    combined = emp_mask & codcia_mask
    print(f"Combined (AND): {combined.sum()} rows match")
