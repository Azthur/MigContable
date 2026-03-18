import sys

filepath = r"c:\SistemaMigConta\backend\app\api\endpoints\mapeo.py"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Target block
broken_block = """                head_dest_constraints = _get_dest_constraints_from_final(
                    company_id, tabla_head_name,
                    sub.schema_destino or "public", db
                # Autofill required text fields with spaces to match DB insert defaults
                for entry in diario_entries:
                    for field, constraints in (head_dest_constraints or {}).items():
                        if field in entry and entry[field] is None and constraints.get("required") and "CHAR" in str(constraints.get("type", "")).upper():
                            entry[field] = " "
                            
                # Validar registros de cabecera

                 validation_errors = _validate_records_against_schema("""

fixed_block = """                head_dest_constraints = _get_dest_constraints_from_final(
                    company_id, tabla_head_name,
                    sub.schema_destino or "public", db
                )
                
                # Autofill required text fields with spaces to match DB insert defaults
                for entry in diario_entries:
                    for field, constraints in (head_dest_constraints or {}).items():
                        if field in entry and entry[field] is None and constraints.get("required") and "CHAR" in str(constraints.get("type", "")).upper():
                            entry[field] = " "
                            
                # Validar registros de cabecera
                validation_errors = _validate_records_against_schema("""

if broken_block in content:
    content = content.replace(broken_block, fixed_block)
    print("Replaced successfully!")
else:
    # Try with single spacing for validation_errors
    broken_block_alt = broken_block.replace("\n                 validation_errors", "\n                validation_errors")
    if broken_block_alt in content:
        content = content.replace(broken_block_alt, fixed_block)
        print("Replaced alt successfully!")
    else:
        print("Block not found!")
        sys.exit(1)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
