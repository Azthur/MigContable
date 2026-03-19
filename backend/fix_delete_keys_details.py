import sys

filepath = r"c:\SistemaMigConta\backend\app\api\endpoints\mapeo.py"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Initialize delete_keys early (around line 1618)
early_init_target = """                head_table_name = sub.tabla_destino_cabecera or "cf_diario"
                det_table_name = sub.tabla_destino_detalle or "cf_diariol"

                # Reflect local staging tables"""

early_init_fixed = """                head_table_name = sub.tabla_destino_cabecera or "cf_diario"
                det_table_name = sub.tabla_destino_detalle or "cf_diariol"
                
                delete_keys = set()
                nasiento_col = sub.col_destino_nasiento or "nasiento"

                # Reflect local staging tables"""

# 2. Add keys from details set if detail rows exist (We need to find the detail_rows append)
details_read_target = """                    if detalle_rows:
                        remote_det_cols = [c.name for c in FinalDetTable.columns]"""

details_read_fixed = """                    if detalle_rows:
                        has_cper_d = "cper" in FinalDetTable.columns if FinalDetTable is not None else False
                        has_cmes_d = "cmes" in FinalDetTable.columns if FinalDetTable is not None else False
                        has_ccodori_d = "ccodori" in FinalDetTable.columns if FinalDetTable is not None else False
                        has_nasiento_d = nasiento_col in FinalDetTable.columns if FinalDetTable is not None else False

                        for row in detalle_rows:
                            r_d = row._mapping
                            cper = r_d.get('cper') if has_cper_d else None
                            cmes = r_d.get('cmes') if has_cmes_d else None
                            ccodori = r_d.get('ccodori') if has_ccodori else None
                            nasiento = r_d.get(nasiento_col) if has_nasiento_d else None
                            if cper and cmes and ccodori and nasiento is not None:
                                delete_keys.add((cper, cmes, str(ccodori).strip(), nasiento))

                        remote_det_cols = [c.name for c in FinalDetTable.columns]"""

# 3. Add explicit delete execution at the end of both fetches or inside details if not done yet.
# Actually, let's just use replace_file_content or a simpler script to just REPLICATE the delete loop inside details!
# Replicating is safer on multi-files and easier to trace.

if early_init_target in content:
    content = content.replace(early_init_target, early_init_fixed)
else:
    print("Early init not found")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Saved part 1.")
