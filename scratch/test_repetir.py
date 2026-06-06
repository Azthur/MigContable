import sys
import pandas as pd

# Add project root to path
sys.path.append("c:\\SistemaMigConta")

from backend.app.core.formula_parser import evaluate_formula_on_df

def main():
    df = pd.DataFrame({
        'C_Numero': ['123', '12345678', '1234567890'],
    })
    
    print("DataFrame:")
    print(df)
    
    # Test LARGO
    print("\nTesting LARGO(C_Numero):")
    largo = evaluate_formula_on_df(df, "LARGO(C_Numero)", None, 1)
    print(largo)
    
    # Test RESTA
    print("\nTesting RESTA(20, LARGO(C_Numero)):")
    resta = evaluate_formula_on_df(df, "RESTA(20, LARGO(C_Numero))", None, 1)
    print(resta)
    
    # Test REPETIR row-by-row
    print("\nTesting REPETIR('0', RESTA(20, LARGO(C_Numero))):")
    repetir = evaluate_formula_on_df(df, "REPETIR('0', RESTA(20, LARGO(C_Numero)))", None, 1)
    print(repetir)
    
    # Test CONCAT row-by-row
    formula_str = "CONCAT(REPETIR('0', RESTA(20, LARGO(C_Numero))), C_Numero)"
    print(f"\nTesting full formula: {formula_str}")
    result = evaluate_formula_on_df(df, formula_str, None, 1)
    print(result)
    
    print("\nChecking resulting lengths (should all be 20):")
    print(result.str.len())
    
    # Test LEFT dynamic
    print("\nTesting LEFT(C_Numero, RESTA(5, LARGO(C_Numero))) dynamic slicing:")
    df_left = pd.DataFrame({'C_Numero': ['ABC', 'A', 'ABCDE']})
    left_res = evaluate_formula_on_df(df_left, "LEFT(C_Numero, RESTA(4, LARGO(C_Numero)))", None, 1)
    print("Source:", df_left['C_Numero'].tolist())
    print("Result:", left_res.tolist())

if __name__ == "__main__":
    main()
