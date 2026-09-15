from backend.app.core.database import DestSessionLocal
from sqlalchemy import text

def show_pattern_examples():
    """Muestra ejemplos específicos del patrón ├á."""
    print("=== EJEMPLOS DEL PATRÓN ├á ===\n")
    
    db = DestSessionLocal()
    
    try:
        # Buscar ejemplos de ├á en todos los campos
        fields = ['nomaux', 'diraux', 'tlfaux', 'email', 'contacto', 'contacto2']
        
        for field in fields:
            query = f"""
                SELECT rucaux, {field}
                FROM cbdmauxi
                WHERE {field} IS NOT NULL
                AND {field} LIKE '%├á%'
                LIMIT 10
            """
            
            results = db.execute(text(query)).fetchall()
            
            if results:
                print(f"\n--- Campo: {field} ---")
                for row in results:
                    rucaux = row[0].strip() if row[0] else "NULL"
                    value = row[1]
                    print(f"RUC: {rucaux}")
                    print(f"Valor: {value}")
                    print()
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    show_pattern_examples()
