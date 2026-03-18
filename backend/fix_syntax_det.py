import sys

filepath = r"c:\SistemaMigConta\backend\app\api\endpoints\mapeo.py"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

target_block = """        det_dest_constraints = _get_dest_constraints_from_final(
            company_id, tabla_det_name,
            sub.schema_destino or "public", db
        )
        validation_errors = _validate_records_against_schema("""

fixed_block = """        det_dest_constraints = _get_dest_constraints_from_final(
            company_id, tabla_det_name,
            sub.schema_destino or "public", db
        )
        
        # Autofill required text fields with spaces to match DB insert defaults
        for entry in diariol_entries:
            for field, constraints in (det_dest_constraints or {}).items():
                if field in entry and entry[field] is None and constraints.get("required") and "CHAR" in str(constraints.get("type", "")).upper():
                    entry[field] = " "
                    
        validation_errors = _validate_records_against_schema("""

if target_block in content:
    content = content.replace(target_block, fixed_block)
    print("Replaced Details successfully!")
else:
    print("Details Block not found!")
    sys.exit(1)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
