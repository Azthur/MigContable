import os
import sys
import traceback
# Add parent dir to PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
import pandas as pd
from backend.app.core.database import DestSessionLocal, dest_engine
from backend.app.models.models import ComputedColumnRule, TableSelection
from backend.app.api.endpoints.etl import __apply_computed_rules

db = DestSessionLocal()
try:
    company_id = 1
    table_name = "ccbrrdoc"
    
    sel = db.query(TableSelection).filter(
        TableSelection.company_id == company_id,
        TableSelection.table_name.ilike(table_name)
    ).first()
    
    if not sel:
        print("TableSelection not found")
        sys.exit(1)
        
    computed_rules = db.query(ComputedColumnRule).filter(
        ComputedColumnRule.table_selection_id == sel.id,
        ComputedColumnRule.is_active == True
    ).order_by(ComputedColumnRule.priority).all()
    
    table_dest_name = sel.table_name.lower().replace(" ", "_")
    where_clause = "company_id = :cid"
    
    query_pend = text(f'SELECT * FROM "{table_dest_name}" WHERE {where_clause}')
    with dest_engine.connect() as conn:
        df_pending = pd.read_sql(query_pend, conn, params={"cid": company_id})
        
    print(f"Loaded {len(df_pending)} pending rows from {table_dest_name}.")
    
    try:
        __apply_computed_rules(df_pending, computed_rules, db, company_id, sel.table_name, db_engine=dest_engine)
        print("Success! No error.")
    except Exception as e:
        print("Error occurred:")
        traceback.print_exc()
finally:
    db.close()
