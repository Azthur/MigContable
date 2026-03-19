import sys

filepath = r"c:\SistemaMigConta\backend\app\api\endpoints\mapeo.py"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update Headers Block
target_head = """                # Fetch Headers
                    target_estado = "MIGRADO" if only_delete else "1"
                    if LocalHeadTable is not None and FinalHeadTable is not None:
                        stmt_c = LocalHeadTable.select().where(
                            LocalHeadTable.c.company_id == company_id,
                            LocalHeadTable.c.estado == target_estado,
                        LocalHeadTable.c.subcategoria_id == sub.id
                    )"""

fixed_head = """                # Fetch Headers
                target_estado = "MIGRADO" if only_delete else "1"
                if LocalHeadTable is not None and FinalHeadTable is not None:
                    stmt_c = LocalHeadTable.select().where(
                        LocalHeadTable.c.company_id == company_id,
                        LocalHeadTable.c.estado == target_estado,
                        LocalHeadTable.c.subcategoria_id == sub.id
                    )"""

# 2. Update Details Block
target_det = """                # Fetch details
                    target_estado_l = "MIGRADO" if only_delete else "1"
                    if LocalDetTable is not None and FinalDetTable is not None:
                        stmt_l = LocalDetTable.select().where(
                            LocalDetTable.c.company_id == company_id,
                            LocalDetTable.c.estado == target_estado_l,
                        LocalDetTable.c.subcategoria_id == sub.id
                    )"""

fixed_det = """                # Fetch details
                target_estado_l = "MIGRADO" if only_delete else "1"
                if LocalDetTable is not None and FinalDetTable is not None:
                    stmt_l = LocalDetTable.select().where(
                        LocalDetTable.c.company_id == company_id,
                        LocalDetTable.c.estado == target_estado_l,
                        LocalDetTable.c.subcategoria_id == sub.id
                    )"""

if target_head in content:
    content = content.replace(target_head, fixed_head)
    print("Replaced Headers Indent")
else:
    print("Headers block not found for replacement!")
    sys.exit(1)

content = content.replace(target_det, fixed_det)
print("Details indent replaced too.")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Saved fixed file.")
