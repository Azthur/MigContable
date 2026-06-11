import pandas as pd
import numpy as np
import ast
import re
from typing import Any
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.app.core.database import dest_engine

def get_real_column_names(table_name: str, db_engine) -> list:
    query = text("SELECT column_name FROM information_schema.columns WHERE table_name = :tname")
    try:
        with db_engine.connect() as conn:
            result = conn.execute(query, {"tname": table_name.lower()})
            return [row[0] for row in result.fetchall()]
    except Exception as e:
        print(f"Error fetching columns for {table_name}: {e}")
        return []

def evaluate_formula_on_df(df: pd.DataFrame, formula_str: str, db: Session, company_id: int, default: str = "", db_engine=None) -> pd.Series:
    """
    Evaluates an Excel-like formula string using Python AST on a pandas DataFrame.
    Supports operations like CONCAT, LEFT, RIGHT, SI.CONJUNTO, Math ops, and BUSCARX.
    """
    if not formula_str:
        return pd.Series([default] * len(df), index=df.index)

    # Convert simple column name directly if it just matches a column exactly
    # Ignore spaces and case
    clean_cols = {str(c).upper().strip(): c for c in df.columns}
    formula_clean = formula_str.upper().strip()
    if formula_clean in clean_cols:
        return df[clean_cols[formula_clean]]

    # If it's pure digits (like '002' or '121201'), return it as string to avoid AST SyntaxError
    if re.fullmatch(r'\d+', formula_str):
        return pd.Series([formula_str] * len(df), index=df.index)

    # Handle quoted literal strings directly: 'value' or "value" (supports spaces like ' ' or " ")
    quoted_match = re.fullmatch(r'\s*"(.*)"\s*', formula_str) or re.fullmatch(r"\s*'(.*)'\s*", formula_str)
    if quoted_match is not None:
        return pd.Series([quoted_match.group(1)] * len(df), index=df.index)

    # Preprocess formula for Python AST compatibility
    formula_str = formula_str.strip()
    formula_str = re.sub(r'["\']([^"\']+)["\'][\'"]+', r"'\1'", formula_str)
    formula_str = re.sub(r'[\'"]+([^"\']+)["\']', r"'\1'", formula_str)
    # Safe replacement of single '=' with '==' only outside string literals
    pattern = r"'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"|(?<![=<>!])=(?![=])"
    def repl(match):
        val = match.group(0)
        if val == '=':
            return '=='
        return val
    formula_ast_str = re.sub(pattern, repl, formula_str)
    formula_ast_str = formula_ast_str.replace('<>', '!=')
    formula_ast_str = formula_ast_str.replace("SUMAR.SI.CONJUNTO", "SUMAR_SI_CONJUNTO")
    formula_ast_str = formula_ast_str.replace("SI.CONJUNTO", "SI_CONJUNTO")

    col_map = {str(c).upper().strip(): c for c in df.columns}

    def eval_ast(node: ast.AST) -> pd.Series:
        def _safe_str(s: pd.Series) -> pd.Series:
            if pd.api.types.is_datetime64_any_dtype(s):
                return s.dt.strftime('%Y-%m-%d %H:%M:%S').fillna('').astype(str)
            return s.apply(lambda x: "" if pd.isna(x) or x is None or str(x) in ['None', 'nan', 'NaT', '<NA>', ''] or str(x).strip() in ['None', 'nan', 'NaT', '<NA>'] else str(x)).astype(str)

        def get_string_arg(arg_node):
            if isinstance(arg_node, ast.Constant):
                return str(arg_node.value).strip()
            elif isinstance(arg_node, ast.Name):
                return str(arg_node.id).strip()
            else:
                return str(eval_ast(arg_node).iloc[0]).strip()

        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return pd.Series([node.value] * len(df), index=df.index)
            return pd.Series([node.value] * len(df), index=df.index)
        elif isinstance(node, ast.Name):
            col_name = node.id.upper()
            if col_name in col_map:
                return df[col_map[col_name]]
            return pd.Series([node.id] * len(df), index=df.index)
        elif isinstance(node, ast.Compare):
            left = eval_ast(node.left)
            right = eval_ast(node.comparators[0])
            op = type(node.ops[0])
            left_str = _safe_str(left).str.strip().str.upper().str.replace(r'\.0$', '', regex=True)
            right_str = _safe_str(right).str.strip().str.upper().str.replace(r'\.0$', '', regex=True)
            if op == ast.Eq: return left_str == right_str
            elif op == ast.NotEq: return left_str != right_str
            elif op == ast.Gt: return pd.to_numeric(left, errors='coerce') > pd.to_numeric(right, errors='coerce')
            elif op == ast.Lt: return pd.to_numeric(left, errors='coerce') < pd.to_numeric(right, errors='coerce')
            elif op == ast.GtE: return pd.to_numeric(left, errors='coerce') >= pd.to_numeric(right, errors='coerce')
            elif op == ast.LtE: return pd.to_numeric(left, errors='coerce') <= pd.to_numeric(right, errors='coerce')
            return pd.Series([False] * len(df), index=df.index)
        elif isinstance(node, ast.BinOp):
            left = eval_ast(node.left)
            right = eval_ast(node.right)
            op = type(node.op)
            ln = pd.to_numeric(left, errors='coerce').fillna(0)
            rn = pd.to_numeric(right, errors='coerce').fillna(0)
            if op == ast.Add: return ln + rn
            elif op == ast.Sub: return ln - rn
            elif op == ast.Mult: return ln * rn
            elif op == ast.Div: return np.where(rn != 0, ln / rn, 0)
            return pd.Series([0] * len(df), index=df.index)
        elif isinstance(node, ast.Call):
            def _get_name(n):
                if isinstance(n, ast.Name): return n.id.upper()
                elif isinstance(n, ast.Attribute): return _get_name(n.value) + "." + n.attr.upper()
                return ""
            func_id = _get_name(node.func)
            
            if func_id in ("SI_CONJUNTO", "SI.CONJUNTO"):
                masks = []
                choices = []
                for i in range(0, len(node.args)-1, 2):
                    cond_series = eval_ast(node.args[i])
                    res_series = eval_ast(node.args[i+1])
                    masks.append(cond_series)
                    choices.append(res_series)
                if masks:
                    if len(node.args) % 2 == 1:
                        default_val = eval_ast(node.args[-1])
                    else:
                        default_val = default if default else ""
                    arr = np.select(masks, choices, default=default_val)
                    res_series = pd.Series(arr, index=df.index)
                    return res_series
                return pd.Series([""] * len(df), index=df.index)

            elif func_id in ("SI", "IF") and len(node.args) >= 2:
                cond = eval_ast(node.args[0])
                true_val = eval_ast(node.args[1])
                if len(node.args) >= 3:
                    false_val = eval_ast(node.args[2])
                else:
                    false_val = pd.Series([default if default else ""] * len(df), index=df.index)
                
                arr = np.where(cond, true_val, false_val)
                return pd.Series(arr, index=df.index)
                
            elif func_id == "CONCAT":
                res = pd.Series([""] * len(df), index=df.index)
                for arg in node.args:
                    val = eval_ast(arg)
                    if isinstance(arg, ast.Name):
                        res = res + _safe_str(val).str.strip()
                    else:
                        res = res + _safe_str(val)
                return res

            elif func_id == "CONCAT_EXACTO":
                res = pd.Series([""] * len(df), index=df.index)
                for arg in node.args:
                    val = eval_ast(arg)
                    res = res + _safe_str(val)
                return res

            elif func_id in ("CHR", "CARACTER") and len(node.args) >= 1:
                try: 
                    n = int(eval_ast(node.args[0]).iloc[0])
                except: 
                    n = 0
                char_val = chr(n) if n > 0 else ""
                return pd.Series([char_val] * len(df), index=df.index)
                
            elif func_id == "LEFT" and len(node.args) >= 2:
                src = _safe_str(eval_ast(node.args[0])).str.strip()
                n_series = pd.to_numeric(eval_ast(node.args[1]), errors='coerce').fillna(0).astype(int)
                return pd.Series(
                    [s[:max(0, n)] for s, n in zip(src, n_series)],
                    index=df.index
                )
                
            elif func_id == "RIGHT" and len(node.args) >= 2:
                src = _safe_str(eval_ast(node.args[0])).str.strip()
                n_series = pd.to_numeric(eval_ast(node.args[1]), errors='coerce').fillna(0).astype(int)
                return pd.Series(
                    [s[-n:] if n > 0 else "" for s, n in zip(src, n_series)],
                    index=df.index
                )
                
            elif func_id == "Y" and len(node.args) >= 1:
                res = pd.Series([True] * len(df), index=df.index)
                for arg in node.args:
                    val = eval_ast(arg)
                    mask = pd.to_numeric(val, errors='coerce').fillna(0).astype(bool) | (_safe_str(val).str.strip().str.upper() == 'TRUE')
                    res = res & mask
                return res

            elif func_id == "O" and len(node.args) >= 1:
                res = pd.Series([False] * len(df), index=df.index)
                for arg in node.args:
                    val = eval_ast(arg)
                    mask = pd.to_numeric(val, errors='coerce').fillna(0).astype(bool) | (_safe_str(val).str.strip().str.upper() == 'TRUE')
                    res = res | mask
                return res

            elif func_id in ("SUMAR.SI.CONJUNTO", "SUMAR_SI_CONJUNTO") and len(node.args) >= 3 and len(node.args) % 2 == 1:
                sum_range = pd.to_numeric(eval_ast(node.args[0]), errors='coerce').fillna(0)
                tmp_df = pd.DataFrame({'_sum': sum_range.values})
                lookup_keys = []
                merge_keys = []
                for i in range(1, len(node.args), 2):
                    c_range = eval_ast(node.args[i]) # hand replaced.str.strip().str.upper()
                    c_val = _safe_str(eval_ast(node.args[i+1])).str.strip().str.upper()
                    range_col = f'_range_{i}'
                    val_col = f'_val_{i}'
                    tmp_df[range_col] = c_range.values
                    tmp_df[val_col] = c_val.values
                    lookup_keys.append(range_col)
                    merge_keys.append(val_col)
                
                grouped = tmp_df.groupby(lookup_keys)['_sum'].sum().reset_index()
                tmp_df['_row_idx'] = np.arange(len(tmp_df))
                merged = pd.merge(
                    tmp_df,
                    grouped,
                    left_on=merge_keys,
                    right_on=lookup_keys,
                    how='left',
                    suffixes=('', '_grouped')
                )
                merged = merged.sort_values('_row_idx')
                return pd.Series(merged['_sum_grouped'].fillna(0).values, index=df.index)

            elif func_id == "SUMA":
                res = pd.Series([0.0] * len(df), index=df.index)
                for arg in node.args:
                    val = eval_ast(arg)
                    res = res + pd.to_numeric(val, errors='coerce').fillna(0)
                return res
            
            elif func_id == "RESTA" and len(node.args) >= 2:
                left = pd.to_numeric(eval_ast(node.args[0]), errors='coerce').fillna(0)
                right = pd.to_numeric(eval_ast(node.args[1]), errors='coerce').fillna(0)
                return left - right
                
            elif func_id == "MULTIPLICA" and len(node.args) >= 2:
                left = pd.to_numeric(eval_ast(node.args[0]), errors='coerce').fillna(0)
                right = pd.to_numeric(eval_ast(node.args[1]), errors='coerce').fillna(0)
                return left * right
                
            elif func_id == "DIVIDE" and len(node.args) >= 2:
                left = pd.to_numeric(eval_ast(node.args[0]), errors='coerce').fillna(0)
                right = pd.to_numeric(eval_ast(node.args[1]), errors='coerce').fillna(0)
                return pd.Series(np.where(right != 0, left / right, 0), index=df.index)
                
            elif func_id == "REDONDEAR" and len(node.args) >= 2:
                src = pd.to_numeric(eval_ast(node.args[0]), errors='coerce').fillna(0)
                try: digits = int(eval_ast(node.args[1]).iloc[0])
                except: digits = 2
                return src.round(digits)

            elif func_id == "ABS" and len(node.args) >= 1:
                src = pd.to_numeric(eval_ast(node.args[0]), errors='coerce').fillna(0)
                return src.abs()
                
            elif func_id == "LARGO" and len(node.args) >= 1:
                src = eval_ast(node.args[0])
                return src.fillna('').astype(str).str.len()
                
            elif func_id == "ESPACIOS" and len(node.args) >= 1:
                src = eval_ast(node.args[0])
                return src.fillna('').astype(str).str.strip()
                
            elif func_id == "MAYUSC" and len(node.args) >= 1:
                src = eval_ast(node.args[0])
                return src.fillna('').astype(str).str.upper()

            elif func_id == "ENCONTRAR" and len(node.args) >= 2:
                # ENCONTRAR(TextoBuscado, TextoDestino) → 1-based position, 0 if not found
                search = eval_ast(node.args[0])
                source = eval_ast(node.args[1])
                search_str = _safe_str(search).str.strip()
                source_str = _safe_str(source).str.strip()
                # Use pandas str.find (0-based, -1 if not found), convert to 1-based
                pos = source_str.combine(search_str, lambda s, srch: s.find(srch))
                return pos.apply(lambda x: x + 1 if x >= 0 else 0)

            elif func_id == "EXTRAER" and len(node.args) >= 3:
                # EXTRAER(Texto, PosicionInicio, NumCaracteres) → substring (1-based start)
                src = _safe_str(eval_ast(node.args[0])).str.strip()
                start_pos = pd.to_numeric(eval_ast(node.args[1]), errors='coerce').fillna(1).astype(int)
                num_chars = pd.to_numeric(eval_ast(node.args[2]), errors='coerce').fillna(0).astype(int)
                # Convert 1-based to 0-based and extract
                return pd.Series(
                    [s[max(0, p-1):max(0, p-1)+n] for s, p, n in zip(src, start_pos, num_chars)],
                    index=df.index
                )
                
            elif func_id == "REPETIR" and len(node.args) >= 2:
                src = eval_ast(node.args[0])
                times = pd.to_numeric(eval_ast(node.args[1]), errors='coerce').fillna(0).astype(int)
                return pd.Series(
                    [s * max(0, t) for s, t in zip(_safe_str(src), times)],
                    index=df.index
                )
                
            elif func_id == "TEXTO" and len(node.args) >= 1:
                src = eval_ast(node.args[0])
                if len(node.args) >= 2:
                    fmt = get_string_arg(node.args[1])
                    if fmt and all(c == '0' for c in fmt):
                        # Handle padding like "00", "000"
                        return pd.to_numeric(src, errors='coerce').fillna(0).astype(int).astype(str).str.zfill(len(fmt))
                return _safe_str(src)
                
            elif func_id == "AÑO" and len(node.args) >= 1:
                src = pd.to_datetime(eval_ast(node.args[0]), errors='coerce')
                return src.dt.year.fillna(0).astype(int).astype(str).replace('0', '')
                
            elif func_id == "MES" and len(node.args) >= 1:
                src = pd.to_datetime(eval_ast(node.args[0]), errors='coerce')
                return src.dt.month.fillna(0).astype(int).astype(str).str.zfill(2).replace('00', '')
            
            elif func_id == "BUSCARX" and len(node.args) >= 4:
                src = eval_ast(node.args[0])
                cat_name = get_string_arg(node.args[1])
                match_col = get_string_arg(node.args[2])
                ret_col = get_string_arg(node.args[3])
                
                from backend.app.models.models import UserCatalog, UserCatalogItem
                cat = db.query(UserCatalog).filter(UserCatalog.name == cat_name, UserCatalog.company_id == company_id).first()
                if cat:
                    items = db.query(UserCatalogItem).filter(UserCatalogItem.catalog_id == cat.id).all()
                    lookup = {}
                    for item in items:
                        # Case-insensitive lookup in item.data dictionary
                        data_keys_lower = {str(k).lower(): k for k in item.data.keys()}
                        match_key = data_keys_lower.get(match_col.lower())
                        ret_key = data_keys_lower.get(ret_col.lower())
                        
                        k_val = item.data.get(match_key, "") if match_key else ""
                        v_val = item.data.get(ret_key, "") if ret_key else ""
                        
                        k = str(k_val).strip().upper()
                        k = re.sub(r'\.0$', '', k)
                        lookup[k] = v_val
                        
                    src_str = _safe_str(src).str.strip().str.upper().str.replace(r'\.0$', '', regex=True)
                    return src_str.map(lookup).fillna(default if default else "")
                return pd.Series([default if default else ""] * len(df), index=df.index)

            elif func_id == "BUSCARX_EXT" and len(node.args) >= 4:
                src = eval_ast(node.args[0])
                ext_table = get_string_arg(node.args[1]).lower().replace(" ", "_").replace("'", "").replace('"', "")
                match_col = get_string_arg(node.args[2]).replace("'", "").replace('"', "")
                ret_col = get_string_arg(node.args[3]).replace("'", "").replace('"', "")
                
                # Fetch actual columns from PG to resolve casing case-insensitively
                engine_to_use = db_engine if db_engine is not None else (db.bind if db else dest_engine)
                real_cols = get_real_column_names(ext_table, engine_to_use)
                if real_cols:
                    match_col_lower = match_col.lower()
                    ret_col_lower = ret_col.lower()
                    real_match_col = next((c for c in real_cols if c.lower() == match_col_lower), match_col)
                    real_ret_col = next((c for c in real_cols if c.lower() == ret_col_lower), ret_col)
                else:
                    real_match_col = match_col
                    real_ret_col = ret_col
                
                query = f'SELECT "{real_match_col}", "{real_ret_col}" FROM "{ext_table}" WHERE "company_id" = {company_id}'
                try:
                    ext_df = pd.read_sql(query, engine_to_use)
                    ext_df[real_match_col] = ext_df[real_match_col].astype(str).str.strip().str.upper().str.replace(r'\.0$', '', regex=True)
                    lookup = ext_df.set_index(real_match_col)[real_ret_col].to_dict()
                    src_str = _safe_str(src).str.strip().str.upper().str.replace(r'\.0$', '', regex=True)
                    return src_str.map(lookup).fillna(default if default else "")
                except Exception as e:
                    print(f"Error in BUSCARX_EXT querying {ext_table}: {e}")
                    return pd.Series([default if default else ""] * len(df), index=df.index)

            elif func_id == "BUSCARX_LOCAL" and len(node.args) >= 3:
                src = eval_ast(node.args[0])
                match_col = get_string_arg(node.args[1]).replace("'", "").replace('"', "")
                ret_col = get_string_arg(node.args[2]).replace("'", "").replace('"', "")
                
                # Case-insensitive check and retrieval of actual column names in DataFrame
                df_cols_lower = {str(c).lower(): c for c in df.columns}
                if match_col.lower() in df_cols_lower and ret_col.lower() in df_cols_lower:
                    actual_match_col = df_cols_lower[match_col.lower()]
                    actual_ret_col = df_cols_lower[ret_col.lower()]
                    
                    # Create a lookup dictionary from the current dataframe
                    # Drop duplicates so that the mapping is 1-to-1 based on the first occurrence
                    lookup_df = df[[actual_match_col, actual_ret_col]].dropna(subset=[actual_match_col]).drop_duplicates(subset=[actual_match_col])
                    lookup = lookup_df.set_index(actual_match_col)[actual_ret_col].to_dict()
                    
                    # Convert map keys (match_col values) to string upper and strip .0 for loose matching
                    str_lookup = {}
                    for k, v in lookup.items():
                        k_str = str(k).strip().upper()
                        k_str = re.sub(r'\.0$', '', k_str)
                        str_lookup[k_str] = v
                    
                    src_str = _safe_str(src).str.strip().str.upper().str.replace(r'\.0$', '', regex=True)
                    return src_str.map(str_lookup).fillna(default if default else "")
                else:
                    print(f"Error in BUSCARX_LOCAL: Columns {match_col} or {ret_col} not in DataFrame")
                    return pd.Series([default if default else ""] * len(df), index=df.index)

        return pd.Series([""] * len(df), index=df.index)

    try:
        tree = ast.parse(formula_ast_str, mode='eval')
        return eval_ast(tree.body)
    except Exception as e:
        print(f"Error executing formula {formula_ast_str}: {e}")
        return pd.Series([default if default else ""] * len(df), index=df.index)
