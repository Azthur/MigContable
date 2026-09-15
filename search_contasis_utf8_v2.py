from backend.app.core.database import DestSessionLocal
from backend.app.models.models import FinalDestConnection
from backend.app.services.connection_manager import ConnectionManager
from sqlalchemy import text

def search_contasis_utf8():
    """Busca el carácter 0xe2 0x94 0x9c (├) en bases de datos de Contasis usando conexiones configuradas."""
    print("=== BUSCANDO CARÁCTER 0xe2 0x94 0x9c (├) EN CONTASIS ===\n")
    
    db = DestSessionLocal()
    
    try:
        # Obtener todas las conexiones de Contasis configuradas
        connections = db.query(FinalDestConnection).all()
        
        for conn in connections:
            try:
                print(f"\n--- Revisando conexión: {conn.database_name} ---")
                
                conn_data = {
                    "host": conn.host,
                    "port": conn.port,
                    "database_name": conn.database_name,
                    "username": conn.username,
                    "password": conn.password
                }
                
                # Crear engine usando ConnectionManager
                engine = ConnectionManager.get_dest_engine(conn_data)
                
                print(f"  Conexión establecida exitosamente")
                
                with engine.connect() as connection:
                    # Primero listar todas las tablas disponibles
                    list_tables_query = """
                        SELECT table_name
                        FROM information_schema.tables
                        WHERE table_schema = 'public'
                        AND table_type = 'BASE TABLE'
                        ORDER BY table_name
                    """
                    tables_result = connection.execute(text(list_tables_query)).fetchall()
                    available_tables = [row[0] for row in tables_result]
                    
                    print(f"  Tablas disponibles: {len(available_tables)}")
                    
                    # Buscar en todas las tablas
                    for table in available_tables:
                        try:
                            # Obtener columnas de texto
                            columns_query = f"""
                                SELECT column_name
                                FROM information_schema.columns
                                WHERE table_name = '{table}'
                                AND table_schema = 'public'
                                AND (data_type LIKE 'character%%' OR data_type LIKE 'text%%')
                            """
                            columns_result = connection.execute(text(columns_query)).fetchall()
                            
                            if not columns_result:
                                continue
                            
                            columns = [row[0] for row in columns_result]
                            
                            # Buscar el carácter en cada columna
                            for column in columns:
                                try:
                                    query = f"""
                                        SELECT COUNT(*)
                                        FROM {table}
                                        WHERE {column} IS NOT NULL
                                        AND {column} LIKE '%├%'
                                    """
                                    
                                    result = connection.execute(text(query)).fetchone()
                                    count = result[0] if result else 0
                                    
                                    if count > 0:
                                        print(f"  Tabla: {table}, Columna: {column}, Registros: {count}")
                                        
                                        # Mostrar algunos ejemplos
                                        examples_query = f"""
                                            SELECT {column}
                                            FROM {table}
                                            WHERE {column} IS NOT NULL
                                            AND {column} LIKE '%├%'
                                            LIMIT 3
                                        """
                                        examples = connection.execute(text(examples_query)).fetchall()
                                        for ex in examples:
                                            print(f"    Ejemplo: {ex[0]}")
                                except Exception as e:
                                    # Si hay error de encoding, reportarlo
                                    if "WIN1252" in str(e) or "UTF8" in str(e):
                                        print(f"  ERROR DE ENCODING en {table}.{column}: {str(e)[:100]}")
                                    pass
                                        
                        except Exception as e:
                            pass
                
                engine.dispose()
                        
            except Exception as e:
                print(f"Error conectando a {conn.database_name}: {str(e)[:100]}")
                
    except Exception as e:
        print(f"Error general: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    search_contasis_utf8()
