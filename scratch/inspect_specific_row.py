import sys
sys.path.append('c:/SistemaMigConta')
from backend.app.core.database import DestSessionLocal, dest_engine
from backend.app.core.formula_parser import evaluate_formula_on_df
from backend.app.models.models import TableSelection, ComputedColumnRule
from sqlalchemy import text
import pandas as pd

db = DestSessionLocal()
try:
    company_id = 1
    query = """
        SELECT * 
        FROM ccbrrdoc
        WHERE company_id = 1 AND "C_car" = 'N/AB050000015'
    """
    df = pd.read_sql(query, dest_engine)
    print(f"Loaded {len(df)} rows for N/AB050000015")
    
    if len(df) > 0:
        print("\n=== Row values in DB ===")
        print(df[['C_car', 'CodDoc', 'NroDoc', 'fchdoc', 'C_fechaNC', 'C_fechaEmision', 'C_fechaNC_Contasis', 'C_moneda']].to_dict('records'))
        
        # Load rules
        sel = db.query(TableSelection).filter(
            TableSelection.company_id == company_id,
            TableSelection.table_name.ilike('%ccbrrdoc%')
        ).first()
        
        rules = db.query(ComputedColumnRule).filter(
            ComputedColumnRule.table_selection_id == sel.id,
            ComputedColumnRule.is_active == True
        ).order_by(ComputedColumnRule.priority).all()
        
        # Run evaluation on this DF
        from backend.app.api.endpoints.etl import __apply_computed_rules
        df_eval = df.copy()
        __apply_computed_rules(df_eval, rules, db, company_id, "ccbrrdoc")
        
        print("\n=== Row values after manual eval in memory ===")
        print(df_eval[['C_car', 'CodDoc', 'NroDoc', 'fchdoc', 'C_fechaNC', 'C_fechaEmision', 'C_fechaNC_Contasis', 'C_moneda']].to_dict('records'))
        
    else:
        print("Rows not found in ccbrrdoc!")

finally:
    db.close()
