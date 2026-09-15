from backend.app.core.database import DestSessionLocal
from sqlalchemy import text
from collections import defaultdict

# Patrones de caracteres corruptos a buscar
CORRUPTED_PATTERNS = [
    '┬á', '┬é', '┬í', '┬ó', '┬ú', '┬ñ', '┬¿',
    '┬', 'í┤', '┤', 'á', 'íÁ', 'Á',
    'éP', 'éS', 'é', 'Dé'
]

def analyze_staging():
    """Analiza la base de datos de staging local buscando caracteres corruptos."""
    print("=== ANÁLISIS DE CARACTERES CORRUPTOS EN STAGING LOCAL ===\n")
    
    db = DestSessionLocal()
    results = defaultdict(lambda: defaultdict(int))
    
    try:
        # Obtener todas las tablas
        query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """
        tables = [row[0] for row in db.execute(text(query)).fetchall()]
        
        print(f"Tablas encontradas: {len(tables)}\n")
        
        for table in tables:
            try:
                # Obtener columnas de texto
                query = """
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_name = :table_name
                    AND table_schema = 'public'
                    AND (data_type LIKE 'character%' OR data_type LIKE 'text%')
                """
                text_columns = db.execute(text(query), {"table_name": table}).fetchall()
                
                if not text_columns:
                    continue
                
                for column_data in text_columns:
                    try:
                        if len(column_data) >= 2:
                            column_name = column_data[0]
                            data_type = column_data[1]
                        else:
                            continue
                        
                        # Buscar caracteres corruptos en esta columna
                        conditions = []
                        for pattern in CORRUPTED_PATTERNS:
                            conditions.append(f"{column_name} LIKE '%{pattern}%'")
                        
                        if conditions:
                            query = f"""
                                SELECT COUNT(*)
                                FROM {table}
                                WHERE {' OR '.join(conditions)}
                            """
                            
                            try:
                                count = db.execute(text(query)).fetchone()[0]
                                if count > 0:
                                    results[table][column_name] = count
                                    print(f"  - {table}.{column_name}: {count} registros corruptos")
                            except Exception as e:
                                # Ignorar errores
                                pass
                    except Exception as e:
                        continue
            except Exception as e:
                continue
        
        # Resumen
        print("\n=== RESUMEN ===\n")
        if results:
            for table, columns in results.items():
                for column, count in columns.items():
                    print(f"{table}.{column}: {count}")
        else:
            print("No se encontraron caracteres corruptos en staging local")
        
        # Guardar en archivo
        with open('staging_corruption_report.txt', 'w', encoding='utf-8') as f:
            f.write("=== REPORTE DE CARACTERES CORRUPTOS EN STAGING LOCAL ===\n\n")
            f.write("Patrones buscados:\n")
            for pattern in CORRUPTED_PATTERNS:
                f.write(f"  - {pattern}\n")
            f.write("\n")
            
            if results:
                for table, columns in results.items():
                    for column, count in columns.items():
                        f.write(f"{table}.{column}: {count}\n")
            else:
                f.write("No se encontraron caracteres corruptos\n")
        
        print("\nReporte guardado en staging_corruption_report.txt")
        
    except Exception as e:
        print(f"Error analizando staging: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    analyze_staging()
