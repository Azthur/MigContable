from backend.app.core.database import DestSessionLocal
from backend.app.models.models import FinalDestConnection
from backend.app.services.connection_manager import ConnectionManager
from sqlalchemy import text

def check_contasis_encoding():
    """Verifica el encoding de las bases de datos de Contasis."""
    print("=== VERIFICANDO ENCODING DE BASES DE DATOS CONTASIS ===\n")
    
    db = DestSessionLocal()
    
    try:
        connections = db.query(FinalDestConnection).all()
        
        for conn in connections:
            try:
                print(f"\n--- Base de datos: {conn.database_name} ---")
                
                conn_data = {
                    "host": conn.host,
                    "port": conn.port,
                    "database_name": conn.database_name,
                    "username": conn.username,
                    "password": conn.password
                }
                
                engine = ConnectionManager.get_dest_engine(conn_data)
                
                with engine.connect() as connection:
                    # Verificar encoding de la base de datos
                    encoding_query = """
                        SELECT pg_database.datname, pg_encoding_to_char(pg_database.encoding) 
                        FROM pg_database 
                        WHERE pg_database.datname = current_database()
                    """
                    result = connection.execute(text(encoding_query)).fetchone()
                    if result:
                        print(f"  Encoding: {result[1]}")
                    
                    # Verificar encoding del cliente
                    client_encoding_query = "SHOW client_encoding"
                    client_result = connection.execute(text(client_encoding_query)).fetchone()
                    if client_result:
                        print(f"  Client encoding: {client_result[0]}")
                    
                    # Verificar si hay tablas con datos
                    tables_query = """
                        SELECT COUNT(*) 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_type = 'BASE TABLE'
                    """
                    tables_count = connection.execute(text(tables_query)).fetchone()[0]
                    print(f"  Tablas: {tables_count}")
                
                engine.dispose()
                        
            except Exception as e:
                print(f"Error en {conn.database_name}: {str(e)[:100]}")
                
    except Exception as e:
        print(f"Error general: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_contasis_encoding()
