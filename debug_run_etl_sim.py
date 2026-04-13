import sys, os
sys.path.append(os.getcwd())
from backend.app.core.database import dest_engine, DestSessionLocal
from backend.app.models.models import TableSelection, ComputedColumnRule
from sqlalchemy import text
import pandas as pd

db = DestSessionLocal()
sel = db.query(TableSelection).filter(TableSelection.table_name == 'VtaRItem', TableSelection.company_id == 4).first()
if sel:
    computed_rules = db.query(ComputedColumnRule).filter(ComputedColumnRule.table_selection_id == sel.id, ComputedColumnRule.is_active == True).all()
    print(f"Rules length: {len(computed_rules)}")
    
    where_clause = "company_id = 4"
    query_pend = text(f'SELECT * FROM "vtaritem" WHERE ' + where_clause)
    with dest_engine.connect() as conn:
        df_pending = pd.read_sql(query_pend, conn)
    print(f"df_pending length: {len(df_pending)}")
    
    from backend.app.api.endpoints.etl import __apply_computed_rules
    print("Applying computed rules...")
    __apply_computed_rules(df_pending, computed_rules, db, 4, sel.table_name)
    print("Finished applying computed rules!")
    
    for col in df_pending.select_dtypes(include=['object']).columns:
        df_pending[col] = df_pending[col].apply(lambda x: None if x == "" else x)
    
    update_cols = []
    df_cols_lower_pending = {str(c).lower(): str(c) for c in df_pending.columns}
    for r in computed_rules:
        r_lower = r.new_column_name.lower()
        if r_lower in df_cols_lower_pending:
            actual_col_name = df_cols_lower_pending[r_lower]
            if actual_col_name not in update_cols:
                update_cols.append(actual_col_name)
                
    print(f"Update cols count: {len(update_cols)}")
    
    temp_table = f"temp_update_vtaritem_4"
    print("Executing to_sql...")
    df_pending.to_sql(temp_table, dest_engine, if_exists="replace", index=False)
    print("Finished to_sql.")
    
    match_col = "_migration_id"
    
    set_clause = ", ".join([f'"{c}" = temp."{c}"' for c in update_cols])
    update_sql = f'UPDATE "vtaritem" t SET {set_clause} FROM "{temp_table}" temp WHERE t."{match_col}" = temp."{match_col}"'
    
    print("Executing UPDATE SQL...")
    with dest_engine.begin() as conn:
        conn.execute(text(update_sql))
        conn.execute(text(f'DROP TABLE "{temp_table}"'))
    print("UPDATE SQL EXECUTED SUCCESSFULLY!")
