import sys

filepath = r"c:\SistemaMigConta\backend\app\api\endpoints\mapeo.py"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

target_block = """    # ─── Actualizar Control Incremental y Asiento Inicial ───
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
                print(f"Error actualizando control incremental compuesto: {e}")
    except Exception as e:
        print(f"Error actualizando control incremental o asiento inicial: {e}")"""

fixed_block = """    # ─── Actualizar Control Incremental y Asiento Inicial ───
    try:
        def _get_nas_safe(e):
            try: return int(e.get("nasiento", 0))
            except: return 0

        max_nasiento = 0
        if diariol_entries:
            max_nasiento = max((_get_nas_safe(e) for e in diariol_entries), default=0)
        elif diario_entries:
            max_nasiento = max((_get_nas_safe(e) for e in diario_entries), default=0)

        # Actualizamos el asiento inicial para visualización en el front
        if max_nasiento > 0:
            print(f"GUARDANDO ASIENTO INICIAL [subcat={sub.id}]: {max_nasiento}")
            db.execute(
                text("UPDATE mapeo_subcategorias SET asiento_inicial = :nas WHERE id = :id"),
                {"nas": int(max_nasiento), "id": sub.id}
            )
            db.commit()

        if 'ctrl_col' in locals() and ctrl_col and not df.empty:
            cols_split = [c.strip() for c in ctrl_col.split(",")]
            actual_cols = []
            for c in cols_split:
                match = next((col for col in df.columns if col.lower() == c.lower()), None)
                if match: actual_cols.append(match)

            if len(actual_cols) > 0:
                valid_entries = [e for e in diariol_entries if e.get("estado") != "0"]
                if valid_entries or not error_nasientos:
                    max_val = None
                    if len(actual_cols) > 1 and '_incremental_key' in df.columns:
                        max_val = df['_incremental_key'].max()
                    elif len(actual_cols) == 1:
                        max_val = df[actual_cols[0]].max()

                    if max_val is not None and str(max_val).strip() != "":
                        print(f"GUARDANDO CONTROL INCREMENTAL [subcat={sub.id}]: {max_val}")
                        db.execute(
                            text("UPDATE mapeo_subcategorias SET last_generated_control_value = :val WHERE id = :id"),
                            {"val": str(max_val), "id": sub.id}
                        )
                        db.commit()
    except Exception as e:
        print(f"Error actualizando control incremental o asiento inicial: {e}")"""

if target_block in content:
    content = content.replace(target_block, fixed_block)
    print("Replaced Bulletproof successfully!")
else:
    print("Bulletproof Block not found in file!")
    sys.exit(1)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
