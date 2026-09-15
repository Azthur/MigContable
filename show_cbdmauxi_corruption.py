from backend.app.core.database import DestSessionLocal
from sqlalchemy import text

def show_cbdmauxi_corruption():
    """Muestra los registros corruptos en cbdmauxi para revisión manual."""
    print("=== REGISTROS CORRUPTOS EN cbdmauxi PARA REVISIÓN ===\n")
    
    db = DestSessionLocal()
    
    try:
        # Campos con corrupción
        fields = ['nomaux', 'diraux', 'tlfaux', 'email', 'contacto', 'contacto2']
        
        for field in fields:
            print(f"\n{'='*80}")
            print(f"CAMPO: {field}")
            print(f"{'='*80}\n")
            
            # Obtener todos los registros corruptos de este campo
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
                LIMIT 50
            """
            
            results = db.execute(text(query)).fetchall()
            
            if results:
                print(f"Total registros corruptos en {field}: {len(results)}\n")
                print(f"{'RUC/AUX':<15} | {field:<60}")
                print("-" * 80)
                
                for i, row in enumerate(results, 1):
                    rucaux = row[0].strip() if row[0] else "NULL"
                    value = row[1] if row[1] else "NULL"
                    print(f"{str(rucaux):<15} | {str(value)[:60]}")
            else:
                print(f"No se encontraron registros corruptos en {field}")
        
        # Resumen total
        print(f"\n\n{'='*80}")
        print("RESUMEN TOTAL")
        print(f"{'='*80}\n")
        
        total_corrupt = 0
        for field in fields:
            query = f"""
                SELECT COUNT(*)
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
            """
            count = db.execute(text(query)).fetchone()[0]
            total_corrupt += count
            print(f"{field}: {count} registros corruptos")
        
        print(f"\nTOTAL: {total_corrupt} registros corruptos en cbdmauxi")
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    show_cbdmauxi_corruption()
