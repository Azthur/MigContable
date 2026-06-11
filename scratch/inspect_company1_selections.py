import sys
sys.path.append('c:/SistemaMigConta')
from backend.app.core.database import DestSessionLocal
from backend.app.models.models import SourceConnection, TableSelection
from sqlalchemy import text

db = DestSessionLocal()
try:
    conn_info = db.query(SourceConnection).filter(SourceConnection.company_id == 1).first()
    if conn_info:
        print("=== Source Connection for Company 1 ===")
        print(f"Host: {conn_info.host}, Database: {conn_info.database_name}, Username: {conn_info.username}")
    else:
        print("No source connection found for Company 1.")
        
    sel = db.query(TableSelection).filter(TableSelection.company_id == 1, TableSelection.table_name == 'CcbRRdoc').first()
    if sel:
        print("\n=== Table Selection for ccbrrdoc (Company 1) ===")
        print(f"ID: {sel.id}, Custom Query: {sel.custom_query}, Date Col: {sel.date_column}")
        
        # Check column filters
        from backend.app.models.models import ColumnFilter
        filters = db.query(ColumnFilter).filter(ColumnFilter.table_selection_id == sel.id, ColumnFilter.is_active == True).all()
        print("Filters:")
        for f in filters:
            print(f"  Col: {f.column_name}, Op: {f.operator}, Val: {f.filter_value}")
            
finally:
    db.close()
