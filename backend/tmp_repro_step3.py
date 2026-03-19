from sqlalchemy import create_engine, Table, MetaData, text
import pandas as pd

local_engine = create_engine('postgresql://postgres:postgres@localhost:5434/migconta_db')
final_engine = create_engine('postgresql://postgres:postgres@192.168.2.90:5432/contasis_005')

metadata_local = MetaData()
metadata_final = MetaData()

print("Reflecting tables...")
LocalHeadTable = Table('cf_diario', metadata_local, autoload_with=local_engine)
LocalDetTable = Table('cf_diariol', metadata_local, autoload_with=local_engine)
FinalHeadTable = Table('cf_diario', metadata_final, autoload_with=final_engine)
FinalDetTable = Table('cf_diariol', metadata_final, autoload_with=final_engine)

company_id = 4
sub_id = 28

# Fetch Headers
stmt_c = LocalHeadTable.select().where(
    LocalHeadTable.c.company_id == company_id,
    LocalHeadTable.c.estado == "1",
    LocalHeadTable.c.subcategoria_id == sub_id
)

with local_engine.connect() as local_conn:
    cabeceras_rows = local_conn.execute(stmt_c).fetchall()
    print(f"Found {len(cabeceras_rows)} headers local.")

    # Fetch Details
    stmt_l = LocalDetTable.select().where(
        LocalDetTable.c.company_id == company_id,
        LocalDetTable.c.estado == "1",
        LocalDetTable.c.subcategoria_id == sub_id
    )
    detalle_rows = local_conn.execute(stmt_l).fetchall()
    print(f"Found {len(detalle_rows)} lines local.")

# Prepare inserts
remote_head_cols = [c.name for c in FinalHeadTable.columns]
remote_det_cols = [c.name for c in FinalDetTable.columns]

insert_heads = []
for row in cabeceras_rows:
    r_d = row._mapping
    insert_heads.append({k: v for k, v in r_d.items() if k in remote_head_cols})

insert_lines = []
for row in detalle_rows:
    r_d = row._mapping
    insert_item = {}
    for k, v in r_d.items():
        if k in remote_det_cols:
            insert_item[k] = v
    insert_lines.append(insert_item)

print(f"Prepared {len(insert_heads)} headers and {len(insert_lines)} lines for insertion.")

try:
    with final_engine.begin() as final_conn:
        print("Inserting headers...")
        if insert_heads:
            final_conn.execute(FinalHeadTable.insert(), insert_heads)
            print("Headers inserted successfully.")
        
        print("Inserting lines...")
        if insert_lines:
            final_conn.execute(FinalDetTable.insert(), insert_lines)
            print("Lines inserted successfully.")
except Exception as e:
    print(f"MIGRATION FAILED: {e}")
