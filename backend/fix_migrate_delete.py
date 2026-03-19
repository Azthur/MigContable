import sys

filepath = r"c:\SistemaMigConta\backend\app\api\endpoints\mapeo.py"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update endpoint definition
target_def = """@router.post("/migrate-to-final/{company_id}")
def migrate_to_final(
    company_id: int,
    lote_id: Optional[str] = None,
    db: Session = Depends(get_dest_db)
):"""

fixed_def = """@router.post("/migrate-to-final/{company_id}")
def migrate_to_final(
    company_id: int,
    lote_id: Optional[str] = None,
    only_delete: bool = False,
    db: Session = Depends(get_dest_db)
):"""

# 2. Update Headers Insert Block
target_headers_ins = """                        if insert_list:
                            try:
                                final_db.execute(FinalHeadTable.insert(), insert_list)"""

fixed_headers_ins = """                        if not only_delete and insert_list:
                            try:
                                final_db.execute(FinalHeadTable.insert(), insert_list)"""

# 3. Update Details Insert Block
target_details_ins = """                        if insert_list:
                            try:
                                final_db.execute(FinalDetTable.insert(), insert_list)"""

fixed_details_ins = """                        if not only_delete and insert_list:
                            try:
                                final_db.execute(FinalDetTable.insert(), insert_list)"""

if target_def in content:
    content = content.replace(target_def, fixed_def)
    print("Replaced Def successfully")
else:
    print("Def block missing")
    sys.exit(1)

content = content.replace(target_headers_ins, fixed_headers_ins)
content = content.replace(target_details_ins, fixed_details_ins)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Replaced all successfully!")
