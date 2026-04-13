import sys, os
sys.path.append(os.getcwd())
import pandas as pd
from backend.app.core.database import dest_engine, DestSessionLocal
from backend.app.models.models import TableSelection, ComputedColumnRule
from sqlalchemy import text, inspect
import numpy as np

db = DestSessionLocal()
sel = db.query(TableSelection).filter(TableSelection.table_name == 'VtaRItem', TableSelection.company_id == 6).first()
if sel:
    computed_rules = db.query(ComputedColumnRule).filter(ComputedColumnRule.table_selection_id == sel.id, ComputedColumnRule.is_active == True).all()
    print('Company 6 Rules:', len(computed_rules))
    
    table_dest_name = "vtaritem"
    where_clause = "company_id = 6"
    query_pend = text(f'SELECT * FROM "{table_dest_name}" WHERE {where_clause}')
    with dest_engine.connect() as conn:
        df_pending = pd.read_sql(query_pend, conn)
    
    print('df_pending rows:', len(df_pending))
    if not df_pending.empty:
        try:
            from backend.app.api.endpoints.etl import __apply_computed_rules
            __apply_computed_rules(df_pending, computed_rules, db, 6, sel.table_name)
            print('Applied rules magically!')
            
            # Formatear números terminados en .0 si están en variables string
            for col in df_pending.columns:
                if df_pending[col].dtype == 'object':
                    df_pending[col] = df_pending[col].apply(lambda x: None if pd.isna(x) or str(x).strip() in ['', 'nan', 'None', '<NA>'] else str(x).replace('.0', '') if str(x).endswith('.0') and str(x)[:-2].lstrip('-').replace('.','',1).isdigit() else x)
            
            update_cols = []
            df_cols_lower_pending = {str(c).lower(): str(c) for c in df_pending.columns}
            
            for r in computed_rules:
                r_lower = r.new_column_name.lower()
                if r_lower in df_cols_lower_pending:
                    actual_col_name = df_cols_lower_pending[r_lower]
                    if actual_col_name not in update_cols:
                        update_cols.append(actual_col_name)
                        
            print('update_cols:', len(update_cols))
            
            insp = inspect(dest_engine)
            dest_cols = {c['name']: c['type'] for c in insp.get_columns(table_dest_name)}
            dtype_map = {c: dest_cols[c] for c in df_pending.columns if c in dest_cols}
            
            temp_table = f"temp_update_{table_dest_name}_6"
            df_pending.to_sql(temp_table, dest_engine, if_exists="replace", index=False, dtype=dtype_map)
            print('to_sql success!')
            
            match_col = "_migration_id"
            if update_cols:
                set_clause = ", ".join([f'"{c}" = temp."{c}"' for c in update_cols])
                update_sql = f'UPDATE "{table_dest_name}" t SET {set_clause} FROM "{temp_table}" temp WHERE t."{match_col}" = temp."{match_col}"'
                with dest_engine.begin() as conn:
                    conn.execute(text(update_sql))
                    conn.execute(text(f'DROP TABLE "{temp_table}"'))
                print('UPDATE SUCCESS!')
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f'CRASHED: {e}')
