from backend.app.core.database import DestSessionLocal
from sqlalchemy import text

def search_utf8_issue():
    """Busca el carácter 0xe2 0x94 0x9c (├) en todas las tablas de Contasis."""
    print("=== BUSCANDO CARÁCTER 0xe2 0x94 0x9c (├) EN CONTASIS ===\n")
    
    db = DestSessionLocal()
    
    try:
        # Lista de tablas principales de Contasis a revisar
        tables = [
            'cg_entitrib',
            'cgentitri',
            'cbdmauxi',
            'cgbmauxi',
            'cg_asiento',
            'cg_asiedet',
            'cg_comprob',
        ]
        
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
                    query = f"""
                        SELECT COUNT(*)
                        FROM {table}
                        WHERE {column} IS NOT NULL
                        AND {column} LIKE '%├%'
                    """
                    
                    try:
                        result = db.execute(text(query)).fetchone()
                        count = result[0] if result else 0
                        
                        if count > 0:
                            print(f"Tabla: {table}, Columna: {column}, Registros: {count}")
                            
                            # Mostrar algunos ejemplos
                            examples_query = f"""
                                SELECT {column}
                                FROM {table}
                                WHERE {column} IS NOT NULL
                                AND {column} LIKE '%├%'
                                LIMIT 5
                            """
                            examples = db.execute(text(examples_query)).fetchall()
                            for ex in examples:
                                print(f"  Ejemplo: {ex[0]}")
                    except Exception as e:
                        pass
                        
            except Exception as e:
                print(f"Error en tabla {table}: {e}")
                
    except Exception as e:
        print(f"Error general: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    search_utf8_issue()
