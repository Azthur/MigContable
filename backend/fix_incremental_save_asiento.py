import sys

filepath = r"c:\SistemaMigConta\backend\app\api\endpoints\mapeo.py"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

target_block = """    # ─── Actualizar Control Incremental ───
    if 'ctrl_col' in locals() and ctrl_col and not df.empty:
        try:
            actual_col = next((c for c in df.columns if c.lower() == ctrl_col.lower()), ctrl_col)
            # Solo actualizar si hubo registros insertados exitosamente
            valid_entries = [e for e in diariol_entries if e.get("estado") != "0"]
            if valid_entries or not error_nasientos:
                max_val = df[actual_col].max()
                if max_val is not None and str(max_val).strip() != "":
                    print(f"ACTUALIZANDO CONTROL INCREMENTAL [subcat={sub.id}]: {sub.last_generated_control_value} -> {max_val}")
                    # Update without committing fully into Session if attached, or use merge
                    db.execute(
                        text("UPDATE mapeo_subcategorias SET last_generated_control_value = :val WHERE id = :id"),
                        {"val": str(max_val), "id": sub.id}
                    )
                    db.commit()
        except Exception as e:
            print(f"Error actualizando control incremental: {e}")"""

fixed_block = """    # ─── Actualizar Control Incremental y Asiento Inicial ───
    try:
        max_nasiento = 0
        if diariol_entries:
            max_nasiento = max(int(e.get("nasiento", 0)) for e in diariol_entries if e.get("nasiento"))
        elif diario_entries:
            max_nasiento = max(int(e.get("nasiento", 0)) for e in diario_entries if e.get("nasiento"))

        # Actualizamos el asiento inicial para visualización en el front
        if max_nasiento > 0:
            db.execute(
                text("UPDATE mapeo_subcategorias SET asiento_inicial = :nas WHERE id = :id"),
                {"nas": max_nasiento, "id": sub.id}
            )
            db.commit()

        if 'ctrl_col' in locals() and ctrl_col and not df.empty:
            actual_col = next((c for c in df.columns if c.lower() == ctrl_col.lower()), ctrl_col)
            valid_entries = [e for e in diariol_entries if e.get("estado") != "0"]
            if valid_entries or not error_nasientos:
                max_val = df[actual_col].max()
                if max_val is not None and str(max_val).strip() != "":
                    db.execute(
                        text("UPDATE mapeo_subcategorias SET last_generated_control_value = :val WHERE id = :id"),
                        {"val": str(max_val), "id": sub.id}
                    )
                    db.commit()
    except Exception as e:
        print(f"Error actualizando control incremental o asiento inicial: {e}")"""

if target_block in content:
    content = content.replace(target_block, fixed_block)
    print("Replaced Incremental & Asiento successfully!")
else:
    print("Incremental Block not found!")
    sys.exit(1)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
