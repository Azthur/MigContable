from backend.app.core.database import DestSessionLocal
from sqlalchemy import text

def show_remaining_corruption():
    """Muestra los 24 registros corruptos restantes."""
    print("=== REGISTROS CORRUPTOS RESTANTES ===\n")
    
    db = DestSessionLocal()
    
    try:
        fields = ['nomaux', 'diraux', 'email']
        
        for field in fields:
            query = f"""
                SELECT rucaux, {field}
                FROM cbdmauxi
                WHERE {field} IS NOT NULL
                AND (
                    {field} LIKE '%┬%' OR 
                    {field} LIKE '%┤%' OR 
                    {field} LIKE '%á%' OR 
                    {field} LIKE '%íÁ%' OR 
                    {field} LIKE '%éS%' OR 
                    {field} LIKE '%éP%' OR
                    {field} LIKE '%Dé%' OR
                    {field} LIKE '%├%' OR
                    {field} LIKE '%â%'
                )
                ORDER BY {field}
            """
            
            results = db.execute(text(query)).fetchall()
            
            if results:
                print(f"\n--- Campo: {field} ({len(results)} registros) ---")
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
    show_remaining_corruption()
