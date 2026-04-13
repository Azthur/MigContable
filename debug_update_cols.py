import sys, os
sys.path.append(os.getcwd())
import pandas as pd
from backend.app.core.database import dest_engine, DestSessionLocal
from backend.app.models.models import TableSelection, ComputedColumnRule
from sqlalchemy import text

db = DestSessionLocal()
with dest_engine.connect() as conn:
    sel = db.query(TableSelection).filter(TableSelection.table_name == 'VtaRItem', TableSelection.company_id == 4).first()
    computed_rules = db.query(ComputedColumnRule).filter(ComputedColumnRule.table_selection_id == sel.id, ComputedColumnRule.is_active == True).all()

    df_pending = pd.read_sql(text('SELECT * FROM vtaritem LIMIT 1'), conn)
    
    update_cols = []
    df_cols_lower_pending = {str(c).lower(): str(c) for c in df_pending.columns}
    
    for r in computed_rules:
        r_lower = r.new_column_name.lower()
        if r_lower in df_cols_lower_pending:
            actual_col_name = df_cols_lower_pending[r_lower]
            if actual_col_name not in update_cols:
                update_cols.append(actual_col_name)
                
    print(f'Update Cols: {update_cols}')
