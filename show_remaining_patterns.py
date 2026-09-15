from backend.app.core.database import DestSessionLocal
from sqlalchemy import text

def show_remaining_patterns():
    """Muestra ejemplos de patrones restantes."""
    db = DestSessionLocal()
    
    patterns = ['┬á', '┬', '├â┬▒', '├â┬í', '├â┬▒']
    
    try:
        for pattern in patterns:
            print(f"\n=== EJEMPLOS DEL PATRÓN {pattern} ===\n")
            
            fields = ['nomaux', 'diraux', 'tlfaux', 'email', 'contacto', 'contacto2']
            found = False
            
            for field in fields:
                query = f"""
                    SELECT rucaux, {field}
                    FROM cbdmauxi
                    WHERE {field} IS NOT NULL
                    AND {field} LIKE '%{pattern}%'
                    LIMIT 5
                """
                
                results = db.execute(text(query)).fetchall()
                
                if results:
                    found = True
                    print(f"--- Campo: {field} ---")
                    for row in results:
                        rucaux = row[0].strip() if row[0] else "NULL"
                        value = row[1]
                        print(f"RUC: {rucaux}")
                        print(f"Valor: {value}")
                        print()
            
            if not found:
                print(f"No se encontraron ejemplos del patrón {pattern}")
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    show_remaining_patterns()
