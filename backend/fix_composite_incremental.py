import sys

filepath = r"c:\SistemaMigConta\backend\app\api\endpoints\mapeo.py"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

target_block = """    if ctrl_col and ctrl_val:

        ctrl_col_lower = ctrl_col.lower()
        if ctrl_col_lower in [c.lower() for c in columns]:
            # Find the actual column name (case-sensitive match)
            actual_col = next((c for c in columns if c.lower() == ctrl_col_lower), ctrl_col)
            before_count = len(df)
            try:
                # Try numeric comparison first, then string
                df_ctrl = pd.to_numeric(df[actual_col], errors='coerce')
                ctrl_numeric = pd.to_numeric(pd.Series([ctrl_val]), errors='coerce').iloc[0]
                if pd.notna(ctrl_numeric):
                    df = df[df_ctrl > ctrl_numeric]
                else:
                    df = df[df[actual_col].astype(str) > ctrl_val]
            except Exception:
                df = df[df[actual_col].astype(str) > ctrl_val]
            after_count = len(df)
            if before_count != after_count:
                print(f"CONTROL INCREMENTAL: Filtradas {before_count - after_count} filas ya migradas (col={actual_col}, last_val={ctrl_val})")
            if df.empty:
                return 0, 0, []"""

fixed_block = """    if ctrl_col and ctrl_val:
        cols_split = [c.strip() for c in ctrl_col.split(",")]
        actual_cols = []
        for c in cols_split:
            match = next((col for col in columns if col.lower() == c.lower()), None)
            if match: actual_cols.append(match)

        if len(actual_cols) == len(cols_split):
            # Composite Key incremental tracking
            before_count = len(df)
            try:
                # Build compound string index
                df['_incremental_key'] = df[actual_cols].astype(str).agg('-'.join, axis=1)
                df = df[df['_incremental_key'] > str(ctrl_val)]
            except Exception as e:
                print(f"Error en filtro incremental compuesto: {e}")
            after_count = len(df)
            if before_count != after_count:
                print(f"CONTROL INCREMENTAL: Filtradas {before_count - after_count} filas ya migradas (cols={ctrl_col}, last_val={ctrl_val})")
            if df.empty:
                return 0, 0, []
        elif len(actual_cols) == 1:
            # Single key fallback
            actual_col = actual_cols[0]
            before_count = len(df)
            try:
                df_ctrl = pd.to_numeric(df[actual_col], errors='coerce')
                ctrl_numeric = pd.to_numeric(pd.Series([ctrl_val]), errors='coerce').iloc[0]
                if pd.notna(ctrl_numeric):
                    df = df[df_ctrl > ctrl_numeric]
                else:
                    df = df[df[actual_col].astype(str) > ctrl_val]
            except Exception:
                df = df[df[actual_col].astype(str) > ctrl_val]
            after_count = len(df)
            if before_count != after_count:
                print(f"CONTROL INCREMENTAL: Filtradas {before_count - after_count} filas de fallback (col={actual_col}, last_val={ctrl_val})")
            if df.empty:
                return 0, 0, []"""

if target_block in content:
    content = content.replace(target_block, fixed_block)
    print("Replaced Composite Incremental successfully!")
else:
    print("Composite Incremental Block not found in file!")
    # Let's write another script that just reads lines from 920 to 945 to see spacing
    sys.exit(1)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
