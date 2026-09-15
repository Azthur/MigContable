import psycopg2
from collections import defaultdict

POSTGRES_CONFIGS = {
    'contasis_002': {
        'host': '192.168.2.90',
        'port': 5432,
        'database': 'contasis_002',
        'user': 'postgres',
        'password': 'postgres'
    },
    'contasis_004': {
        'host': '192.168.2.90',
        'port': 5432,
        'database': 'contasis_004',
        'user': 'postgres',
        'password': 'postgres'
    },
    'contasis_005': {
        'host': '192.168.2.90',
        'port': 5432,
        'database': 'contasis_005',
        'user': 'postgres',
        'password': 'postgres'
    }
}

# Patrones de caracteres corruptos a buscar
CORRUPTED_PATTERNS = [
    '┬á', '┬é', '┬í', '┬ó', '┬ú', '┬ñ', '┬¿',
    '┬', 'í┤', '┤', 'á', 'íÁ', 'Á',
    'éP', 'éS', 'é', 'Dé'
]

def analyze_database(db_name, config):
    """Analiza una base de datos de Contasis buscando caracteres corruptos."""
    print(f"\n=== Analizando {db_name} ===")
    
    conn = None
    results = defaultdict(lambda: defaultdict(int))
    
    try:
        conn = psycopg2.connect(
            host=config['host'],
            port=config['port'],
            database=config['database'],
            user=config['user'],
            password=config['password']
        )
        cursor = conn.cursor()
        
        # Obtener todas las tablas
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"Tablas encontradas: {len(tables)}")
        
        for table in tables:
            try:
                # Obtener columnas de texto
                cursor.execute("""
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_name = %s
                    AND table_schema = 'public'
                    AND (data_type LIKE 'character%' OR data_type LIKE 'text%')
                """, (table,))
                text_columns = cursor.fetchall()
                
                if not text_columns:
                    continue
            except Exception as e:
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
                            cursor.execute(query)
                            row = cursor.fetchone()
                            if row:
                                count = row[0]
                                if count > 0:
                                    results[table][column_name] = count
                                    print(f"  - {table}.{column_name}: {count} registros corruptos")
                        except Exception as e:
                            # Ignorar errores en tablas que no existen o no tienen permisos
                            pass
                except Exception as e:
                    continue
        
        cursor.close()
        return results
        
    except Exception as e:
        print(f"Error analizando {db_name}: {e}")
        return {}
    finally:
        if conn:
            conn.close()

def main():
    print("=== ANÁLISIS DE CARACTERES CORRUPTOS EN CONTASIS ===\n")
    
    all_results = {}
    
    for db_name, config in POSTGRES_CONFIGS.items():
        results = analyze_database(db_name, config)
        all_results[db_name] = results
    
    # Resumen consolidado
    print("\n=== RESUMEN CONSOLIDADO ===\n")
    
    for db_name, results in all_results.items():
        if results:
            print(f"\n{db_name}:")
            for table, columns in results.items():
                for column, count in columns.items():
                    print(f"  {table}.{column}: {count}")
    
    # Guardar en archivo
    with open('corruption_report.txt', 'w', encoding='utf-8') as f:
        f.write("=== REPORTE DE CARACTERES CORRUPTOS EN CONTASIS ===\n\n")
        f.write("Patrones buscados:\n")
        for pattern in CORRUPTED_PATTERNS:
            f.write(f"  - {pattern}\n")
        f.write("\n")
        
        for db_name, results in all_results.items():
            f.write(f"\n{db_name}:\n")
            if results:
                for table, columns in results.items():
                    for column, count in columns.items():
                        f.write(f"  {table}.{column}: {count}\n")
            else:
                f.write("  No se encontraron caracteres corruptos\n")
    
    print("\nReporte guardado en corruption_report.txt")

if __name__ == "__main__":
    main()
