from backend.app.core.database import DestSessionLocal
from sqlalchemy import text

def search_corrupted_e():
    """Busca el carácter ├® (é corrupto) en todas las tablas de staging."""
    print("=== BUSCANDO CARÁCTER ├® (é CORRUPTO) EN STAGING ===\n")
    
    db = DestSessionLocal()
    
    try:
        # Obtener todas las tablas
        tables_query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """
        tables_result = db.execute(text(tables_query)).fetchall()
        tables = [row[0] for row in tables_result]
        
        print(f"Tablas a revisar: {len(tables)}\n")
        
        for table in tables:
            try:
                # Obtener columnas de texto
                columns_query = f"""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = '{table}'
                    AND table_schema = 'public'
                    AND (data_type LIKE 'character%%' OR data_type LIKE 'text%%')
                """
                columns_result = db.execute(text(columns_query)).fetchall()
                
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
                            AND {column} LIKE '%├®%'
                        """
                        
                        result = db.execute(text(query)).fetchone()
                        count = result[0] if result else 0
                        
                        if count > 0:
                            print(f"Tabla: {table}, Columna: {column}, Registros: {count}")
                            
                            # Mostrar algunos ejemplos
                            examples_query = f"""
                                SELECT {column}
                                FROM {table}
                                WHERE {column} IS NOT NULL
                                AND {column} LIKE '%├®%'
                                LIMIT 5
                            """
                            examples = db.execute(text(examples_query)).fetchall()
                            for ex in examples:
                                print(f"  Ejemplo: {ex[0]}")
                            print()
                    except Exception as e:
                        pass
                        
            except Exception as e:
                pass
                
    except Exception as e:
        print(f"Error general: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    search_corrupted_e()
