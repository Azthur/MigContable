from sqlalchemy import create_engine, text
import os

def search_contasis_utf8():
    """Busca el carácter 0xe2 0x94 0x9c (├) en bases de datos de Contasis."""
    print("=== BUSCANDO CARÁCTER 0xe2 0x94 0x9c (├) EN CONTASIS ===\n")
    
    # Configuración de conexión a Contasis
    contasis_dbs = [
        'contasis_002',
        'contasis_004', 
        'contasis_005'
    ]
    
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', 'postgres')
    
    for db_name in contasis_dbs:
        try:
            print(f"\n--- Revisando base de datos: {db_name} ---")
            
            # Crear conexión
            engine = create_engine(f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}')
            
            with engine.connect() as conn:
                # Buscar en tabla principal de entidades
                tables_to_check = ['cgentitri', 'cgbmauxi']
                
                for table in tables_to_check:
                    try:
                        # Verificar si la tabla existe
                        check_table = f"""
                            SELECT EXISTS (
                                SELECT FROM information_schema.tables 
                                WHERE table_name = '{table}'
                            )
                        """
                        exists = conn.execute(text(check_table)).fetchone()[0]
                        
                        if not exists:
                            continue
                            
                        # Obtener columnas de texto
                        columns_query = f"""
                            SELECT column_name
                            FROM information_schema.columns
                            WHERE table_name = '{table}'
                            AND table_schema = 'public'
                            AND (data_type LIKE 'character%%' OR data_type LIKE 'text%%')
                        """
                        columns_result = conn.execute(text(columns_query)).fetchall()
                        
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
                                
                                result = conn.execute(text(query)).fetchone()
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
                                    examples = conn.execute(text(examples_query)).fetchall()
                                    for ex in examples:
                                        print(f"    Ejemplo: {ex[0]}")
                            except Exception as e:
                                # Si hay error de encoding, reportarlo
                                if "WIN1252" in str(e) or "UTF8" in str(e):
                                    print(f"  ERROR DE ENCODING en {table}.{column}: {str(e)[:100]}")
                                pass
                                    
                    except Exception as e:
                        print(f"  Error en tabla {table}: {str(e)[:100]}")
                        
        except Exception as e:
            print(f"Error conectando a {db_name}: {str(e)[:100]}")
            
if __name__ == "__main__":
    search_contasis_utf8()
