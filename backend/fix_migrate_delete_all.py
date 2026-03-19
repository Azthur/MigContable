import sys

filepath = r"c:\SistemaMigConta\backend\app\api\endpoints\mapeo.py"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update Headers Query
target_head_stmt = """                    if LocalHeadTable is not None and FinalHeadTable is not None:
                    stmt_c = LocalHeadTable.select().where(
                        LocalHeadTable.c.company_id == company_id,
                        LocalHeadTable.c.estado == "1","""

fixed_head_stmt = """                    target_estado = "MIGRADO" if only_delete else "1"
                    if LocalHeadTable is not None and FinalHeadTable is not None:
                    stmt_c = LocalHeadTable.select().where(
                        LocalHeadTable.c.company_id == company_id,
                        LocalHeadTable.c.estado == target_estado,"""

# 2. Update Details Query
target_det_stmt = """                    stmt_l = LocalDetTable.select().where(
                        LocalDetTable.c.company_id == company_id,
                        LocalDetTable.c.estado == "1","""

fixed_det_stmt = """                    target_estado_l = "MIGRADO" if only_delete else "1"
                    stmt_l = LocalDetTable.select().where(
                        LocalDetTable.c.company_id == company_id,
                        LocalDetTable.c.estado == target_estado_l,"""

# 3. Update update stmt in Headers to reset to '1' if only_delete
target_upd_head = """                        if not only_delete and insert_list:
                            try:
                                final_db.execute(FinalHeadTable.insert(), insert_list)
                                migrated_cabeceras += len(insert_list)
                                db.execute(LocalHeadTable.update().where(
                                    LocalHeadTable.c.company_id == company_id,
                                    LocalHeadTable.c.estado == "1",
                                    LocalHeadTable.c.subcategoria_id == sub.id
                                ).values(estado="MIGRADO"))
                            except Exception as e:
                                print(f"Error bulk inserting headers: {e}")"""

fixed_upd_head = """                        if not only_delete and insert_list:
                            try:
                                final_db.execute(FinalHeadTable.insert(), insert_list)
                                migrated_cabeceras += len(insert_list)
                                db.execute(LocalHeadTable.update().where(
                                    LocalHeadTable.c.company_id == company_id,
                                    LocalHeadTable.c.estado == "1",
                                    LocalHeadTable.c.subcategoria_id == sub.id
                                ).values(estado="MIGRADO"))
                            except Exception as e:
                                print(f"Error bulk inserting headers: {e}")
                        elif only_delete and delete_keys:
                            try:
                                # Restablecer a pendiente para re-generación/re-migración
                                db.execute(LocalHeadTable.update().where(
                                    LocalHeadTable.c.company_id == company_id,
                                    LocalHeadTable.c.estado == "MIGRADO",
                                    LocalHeadTable.c.subcategoria_id == sub.id
                                ).values(estado="1"))
                            except Exception as e:
                                print(f"Error actualizando estado cabeceras en only_delete: {e}")"""

if target_upd_head in content:
    content = content.replace(target_upd_head, fixed_upd_head)
    print("Replaced Headers update block successfully")
else:
    print("Headers update block missing")
    # Let's write another script that just reads lines from 1634 to 1710 to inspect exact syntax
    sys.exit(1)

content = content.replace("LocalHeadTable.c.estado == \"1\",", "LocalHeadTable.c.estado == target_estado,")
content = content.replace("LocalDetTable.c.estado == \"1\",", "LocalDetTable.c.estado == target_estado_l,")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Replaced all successfully!")
 soccer_val = """if LocalHeadTable is not None and FinalHeadTable is not None:
                    stmt_c = LocalHeadTable.select().where(
                        LocalHeadTable.c.company_id == company_id,
                        LocalHeadTable.c.estado == "1","""
