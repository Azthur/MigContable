from backend.app.core.database import DestSessionLocal
from backend.app.models.models import FinalDestConnection
from backend.app.services.connection_manager import ConnectionManager
from sqlalchemy import text

def fix_all_contasis_corruption():
    """Corrige todos los caracteres corruptos en todas las bases de datos Contasis."""
    print("=== CORRIGIENDO TODOS LOS CARACTERES CORRUPTOS EN CONTASIS ===\n")
    
    db = DestSessionLocal()
    
    # Patrones de corrección
    replacements = [
        ('├®', 'é'),
        ('├æ', 'Ñ'),
        ('├é┬á', 'á'),
        ('├éí', 'í'),
        ('├ÂÍ', 'Á'),
        ('├ÌA', 'ÍA'),
        ('├ü', 'ú'),
        ('├Ü', 'ú'),
        ('├ì', 'í'),
        ('├í', 'í'),
        ('├¡', 'í'),
        ('├ô', 'ó'),
        ('├ë', 'é'),
    ]
    
    try:
        # Obtener todas las conexiones activas
        connections = db.query(FinalDestConnection).filter_by(is_active=True).all()
        
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
                    # Tablas y columnas a corregir
                    corrections = [
                        ('au_cfdiario', 'cglosa_2'),
                        ('cf_diario', 'cglosa_2'),
                        ('cg_entitrib', 'ctelef'),
                        ('cg_entitrib', 'capemat'),
                        ('cg_entitrib', 'crazsoc'),
                        ('cg_entitrib', 'cdirec'),
                    ]
                    
                    total_fixed = 0
                    
                    for table, column in corrections:
                        try:
                            # Verificar si la tabla y columna existen
                            check_exists = f"""
                                SELECT EXISTS (
                                    SELECT FROM information_schema.columns 
                                    WHERE table_name = '{table}' 
                                    AND column_name = '{column}'
                                )
                            """
                            exists = connection.execute(text(check_exists)).fetchone()[0]
                            
                            if not exists:
                                continue
                            
                            # Verificar registros corruptos
                            check_query = f"""
                                SELECT COUNT(*)
                                FROM {table}
                                WHERE {column} IS NOT NULL
                                AND {column} LIKE '%├%'
                            """
                            count = connection.execute(text(check_query)).fetchone()[0]
                            
                            if count == 0:
                                continue
                            
                            print(f"  {table}.{column}: {count} registros corruptos")
                            
                            # Corregir cada patrón
                            for corrupt, correct in replacements:
                                update_query = f"""
                                    UPDATE {table}
                                    SET {column} = REPLACE({column}, '{corrupt}', '{correct}')
                                    WHERE {column} LIKE '%{corrupt}%'
                                """
                                result = connection.execute(text(update_query))
                                if result.rowcount > 0:
                                    print(f"    Corregidos {result.rowcount} registros: '{corrupt}' → '{correct}'")
                                    total_fixed += result.rowcount
                            
                            connection.commit()
                            
                        except Exception as e:
                            pass
                    
                    if total_fixed > 0:
                        print(f"  Total corregidos en {conn.database_name}: {total_fixed}")
                    else:
                        print(f"  No se encontraron registros corruptos")
                
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
    fix_all_contasis_corruption()
