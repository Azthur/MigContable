from backend.app.core.database import DestSessionLocal
from sqlalchemy import text

def analyze_cbdmauxi_patterns():
    """Analiza los patrones de corrupción en cbdmauxi."""
    print("=== ANÁLISIS DE PATRONES DE CORRUPCIÓN EN cbdmauxi ===\n")
    
    db = DestSessionLocal()
    
    try:
        # Campos con corrupción encontrados
        fields = ['nomaux', 'diraux', 'tlfaux', 'email', 'contacto', 'contacto2']
        
        for field in fields:
            print(f"\n--- Campo: {field} ---")
            
            # Obtener ejemplos de registros corruptos
            query = f"""
                SELECT {field}
                FROM cbdmauxi
                WHERE {field} IS NOT NULL
                AND (
                    {field} LIKE '%┬%' OR 
                    {field} LIKE '%┤%' OR 
                    {field} LIKE '%á%' OR 
                    {field} LIKE '%íÁ%' OR 
                    {field} LIKE '%éS%' OR 
                    {field} LIKE '%éP%' OR
                    {field} LIKE '%Dé%'
                )
                LIMIT 10
            """
            
            results = db.execute(text(query)).fetchall()
            
            if results:
                print(f"  Ejemplos de registros corruptos ({len(results)} encontrados):")
                for i, row in enumerate(results, 1):
                    value = row[0]
                    print(f"    {i}. '{value}'")
            else:
                print(f"  No se encontraron registros corruptos")
        
        # Análisis de caracteres especiales únicos
        print("\n\n=== ANÁLISIS DE CARACTERES ESPECIALES ÚNICOS ===\n")
        
        for field in fields:
            print(f"\n--- Campo: {field} ---")
            
            # Obtener todos los valores únicos que contienen caracteres especiales
            query = f"""
                SELECT DISTINCT {field}
                FROM cbdmauxi
                WHERE {field} IS NOT NULL
                AND (
                    {field} LIKE '%┬%' OR 
                    {field} LIKE '%┤%' OR 
                    {field} LIKE '%á%' OR 
                    {field} LIKE '%íÁ%' OR 
                    {field} LIKE '%éS%' OR 
                    {field} LIKE '%éP%' OR
                    {field} LIKE '%Dé%'
                )
                LIMIT 20
            """
            
            results = db.execute(text(query)).fetchall()
            
            if results:
                print(f"  Valores únicos con caracteres especiales ({len(results)}):")
                for i, row in enumerate(results, 1):
                    value = row[0]
                    print(f"    {i}. '{value}'")
            else:
                print(f"  No se encontraron registros corruptos")
    
    except Exception as e:
        print(f"Error analizando cbdmauxi: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    analyze_cbdmauxi_patterns()
