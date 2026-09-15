from backend.app.core.database import DestSessionLocal
from backend.app.models.models import FinalDestConnection
from backend.app.services.connection_manager import ConnectionManager
from sqlalchemy import text

def fix_contasis_corrupted_e():
    """Corrige el carácter ├® → é en contasis_002.au_cfdiario.cglosa_2"""
    print("=== CORRIGIENDO CARÁCTER ├® → é EN contasis_002 ===\n")
    
    db = DestSessionLocal()
    
    try:
        # Obtener conexión a contasis_002
        conn = db.query(FinalDestConnection).filter_by(database_name='contasis_002').first()
        
        if not conn:
            print("No se encontró conexión a contasis_002")
            return
        
        conn_data = {
            "host": conn.host,
            "port": conn.port,
            "database_name": conn.database_name,
            "username": conn.username,
            "password": conn.password
        }
        
        engine = ConnectionManager.get_dest_engine(conn_data)
        
        with engine.connect() as connection:
            # Primero ver qué columnas tiene la tabla
            columns_query = """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'au_cfdiario'
                AND table_schema = 'public'
                ORDER BY ordinal_position
            """
            columns = connection.execute(text(columns_query)).fetchall()
            print(f"Columnas de au_cfdiario: {[c[0] for c in columns]}")
            
            # Verificar registros antes de corregir (sin id)
            check_query = """
                SELECT cglosa_2
                FROM au_cfdiario
                WHERE cglosa_2 LIKE '%├®%'
            """
            results = connection.execute(text(check_query)).fetchall()
            
            print(f"Registros a corregir: {len(results)}")
            for row in results:
                print(f"  Valor: {row[0][:100]}...")
            
            # Corregir los registros
            update_query = """
                UPDATE au_cfdiario
                SET cglosa_2 = REPLACE(cglosa_2, '├®', 'é')
                WHERE cglosa_2 LIKE '%├®%'
            """
            result = connection.execute(text(update_query))
            connection.commit()
            
            print(f"\nRegistros corregidos: {result.rowcount}")
            
            # Verificar después de corregir
            check_after = connection.execute(text(check_query)).fetchall()
            print(f"Registros corruptos restantes: {len(check_after)}")
            
        engine.dispose()
        print("\nCorrección completada")
                        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    fix_contasis_corrupted_e()
