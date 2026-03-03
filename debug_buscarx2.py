import os
import ast
import pandas as pd
from sqlalchemy import create_engine

# Engine config
engine = create_engine('postgresql://postgres:postgres@localhost:5433/migconta_db')

df = pd.read_sql('SELECT "C_car" FROM vtaritem LIMIT 10', engine)

formula_str = "BUSCARX_EXT(C_car, ccbrgdoc, C_car, C_tipocliente)"

def eval_formula(node):
    def get_string_arg(arg_node):
        if isinstance(arg_node, ast.Constant):
            return str(arg_node.value).strip()
        elif isinstance(arg_node, ast.Name):
            return str(arg_node.id).strip()
        else:
            return str(eval_formula(arg_node).iloc[0]).strip()

    if isinstance(node, ast.Name):
        return df['C_car'] if node.id.upper() == 'C_CAR' else pd.Series([node.id]*len(df), index=df.index)
        
    elif isinstance(node, ast.Call):
        func_id = node.func.id.upper()
        if func_id == "BUSCARX_EXT":
            src = eval_formula(node.args[0])
            ext_table = get_string_arg(node.args[1]).lower().replace(" ", "_").replace("'", "").replace('"', "")
            match_col = get_string_arg(node.args[2]).replace("'", "").replace('"', "")
            ret_col = get_string_arg(node.args[3]).replace("'", "").replace('"', "")
            
            print(f"Executing: SELECT \"{match_col}\", \"{ret_col}\" FROM \"{ext_table}\"")
            query = f'SELECT "{match_col}", "{ret_col}" FROM "{ext_table}"'
            try:
                ext_df = pd.read_sql(query, engine)
                ext_df[match_col] = ext_df[match_col].astype(str).str.strip().str.upper()
                lookup = ext_df.set_index(match_col)[ret_col].to_dict()
                
                print("First 5 lookup items:")
                print(list(lookup.items())[:5])
                print("\nSrc values before map:")
                print(src.head())
                
                result = src.astype(str).str.strip().str.upper().map(lookup).fillna("")
                return result
            except Exception as e:
                print(f"Exception caught in query: {e}")
                import traceback
                traceback.print_exc()
                return pd.Series([""] * len(df), index=df.index)

tree = ast.parse(formula_str, mode='eval')
res = eval_formula(tree.body)

print("\nResult:")
print(res.head())
