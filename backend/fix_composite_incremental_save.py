import sys

filepath = r"c:\SistemaMigConta\backend\app\api\endpoints\mapeo.py"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

target_block = """        if 'ctrl_col' in locals() and ctrl_col and not df.empty:
            actual_col = next((c for c in df.columns if c.lower() == ctrl_col.lower()), ctrl_col)
            valid_entries = [e for e in diariol_entries if e.get("estado") != "0"]
            if valid_entries or not error_nasientos:
                max_val = df[actual_col].max()
                if max_val is not None and str(max_val).strip() != "":
                    db.execute(
                        text("UPDATE mapeo_subcategorias SET last_generated_control_value = :val WHERE id = :id"),
                        {"val": str(max_val), "id": sub.id}
                    )
                    db.commit()"""

fixed_block = """        if 'ctrl_col' in locals() and ctrl_col and not df.empty:
            try:
                cols_split = [c.strip() for c in ctrl_col.split(",")]
                actual_cols = []
                for c in cols_split:
                    match = next((col for col in df.columns if col.lower() == c.lower()), None)
                    if match: actual_cols.append(match)

                if len(actual_cols) > 0:
                    valid_entries = [e for e in diariol_entries if e.get("estado") != "0"]
                    if valid_entries or not error_nasientos:
                        if len(actual_cols) > 1 and '_incremental_key' in df.columns:
                            # Use composite key
                            max_val = df['_incremental_key'].max()
                        else:
                            # Single key
                            actual_col = actual_cols[0]
                            max_val = df[actual_col].max()

                        if max_val is not None and str(max_val).strip() != "":
                            db.execute(
                                text("UPDATE mapeo_subcategorias SET last_generated_control_value = :val WHERE id = :id"),
                                {"val": str(max_val), "id": sub.id}
                            )
                            db.commit()
            except Exception as e:
                print(f"Error actualizando control incremental compuesto: {e}")"""

if target_block in content:
    content = content.replace(target_block, fixed_block)
    print("Replaced Composite Incremental Save successfully!")
else:
    print("Composite Incremental Save Block not found in file!")
    sys.exit(1)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
