from backend.app.core.database import DestSessionLocal
from backend.app.models.models import FinalDestConnection
from backend.app.services.connection_manager import ConnectionManager
from sqlalchemy import text

def check_remaining_cf_diario():
    """Verifica qué caracteres corruptos quedan en cf_diario.cglosa_2"""
    print("=== VERIFICANDO CARACTERES CORRUPTOS RESTANTES EN cf_diario.cglosa_2 ===\n")
    
    db = DestSessionLocal()
    
    try:
        # Revisar contasis_002 y contasis_003
        for db_name in ['contasis_002', 'contasis_003']:
            try:
                print(f"\n--- Base de datos: {db_name} ---")
                
                conn = db.query(FinalDestConnection).filter_by(database_name=db_name).first()
                
                if not conn:
                    continue
                
                conn_data = {
                    "host": conn.host,
                    "port": conn.port,
                    "database_name": conn.database_name,
                    "username": conn.username,
                    "password": conn.password
                }
                
                engine = ConnectionManager.get_dest_engine(conn_data)
                
                with engine.connect() as connection:
                    query = """
                        SELECT cglosa_2
                        FROM cf_diario
                        WHERE cglosa_2 IS NOT NULL
                        AND cglosa_2 LIKE '%├%'
                    """
                    results = connection.execute(text(query)).fetchall()
                    
                    print(f"Registros corruptos: {len(results)}")
                    for row in results:
                        print(f"  Valor completo:\n{row[0]}\n")
                
                engine.dispose()
                        
            except Exception as e:
                print(f"Error en {db_name}: {str(e)[:100]}")
                
    except Exception as e:
        print(f"Error general: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_remaining_cf_diario()
