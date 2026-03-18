import sys

filepath = r"c:\SistemaMigConta\backend\app\api\endpoints\mapeo.py"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

target_block = """    if nasiento_key not in counters_por_asiento:
        last_nasiento_in_db = 0
        if DetTable is not None:
            check_col_nasiento = sub.col_destino_nasiento or "nasiento"
            if check_col_nasiento in det_cols:
                # Include MIGRADO entries in the max count to continue numbering after them
                stmt_nas = db.query(func.max(getattr(DetTable.c, check_col_nasiento))).filter(
                    DetTable.c.company_id == company_id,
                    DetTable.c.estado.in_(["PENDIENTE", "1", "MIGRADO"])
                )
                last_nasiento_in_db = db.execute(stmt_nas).scalar() or 0
        
        counters_por_asiento[nasiento_key] = last_nasiento_in_db"""

fixed_block = """    if nasiento_key not in counters_por_asiento:
        last_nasiento_in_db = 0
        from backend.app.models.models import FinalDestConnection
        from backend.app.services.connection_manager import ConnectionManager
        from sqlalchemy import select
        
        # Connect to Target Database to get continuous numbering
        final_conn = db.query(FinalDestConnection).filter(FinalDestConnection.company_id == company_id, FinalDestConnection.is_active == True).first()
        if final_conn and DetTable is not None:
            try:
                conn_data = {"host": final_conn.host, "port": final_conn.port, "database_name": final_conn.database_name, "username": final_conn.username, "password": final_conn.password}
                final_engine = ConnectionManager.get_dest_engine(conn_data)
                check_col_nasiento = sub.col_destino_nasiento or "nasiento"
                
                with final_engine.connect() as f_conn:
                    remote_metadata = MetaData()
                    RemoteDetTable = Table(tabla_det_name, remote_metadata, autoload_with=final_engine)
                    # Query Max
                    r_stmt = select(func.max(getattr(RemoteDetTable.c, check_col_nasiento)))
                    last_nasiento_in_db = f_conn.execute(r_stmt).scalar() or 0
            except Exception as e:
                print(f"Error fetching remote max nasiento: {e}")

        # Fallback to local staging if remote max is 0
        if last_nasiento_in_db == 0 and DetTable is not None:
            check_col_nasiento = sub.col_destino_nasiento or "nasiento"
            if check_col_nasiento in det_cols:
                stmt_nas = db.query(func.max(getattr(DetTable.c, check_col_nasiento))).filter(
                    DetTable.c.company_id == company_id,
                    DetTable.c.estado.in_(["PENDIENTE", "1", "MIGRADO"])
                )
                last_nasiento_in_db = db.execute(stmt_nas).scalar() or 0
        
        counters_por_asiento[nasiento_key] = last_nasiento_in_db"""

if target_block in content:
    content = content.replace(target_block, fixed_block)
    print("Replaced Nasiento successfully!")
else:
    print("Nasiento Block not found!")
    sys.exit(1)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
