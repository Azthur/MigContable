import psycopg2

# Configuración PostgreSQL (Contasis)
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

def check_table_structure(db_name):
    """Verifica la estructura de cg_entitrib en una base de datos."""
    config = POSTGRES_CONFIGS.get(db_name)
    if not config:
        print(f"Configuracion no encontrada para {db_name}")
        return None
    
    try:
        conn = psycopg2.connect(
            host=config['host'],
            port=config['port'],
            database=config['database'],
            user=config['user'],
            password=config['password']
        )
        cursor = conn.cursor()
        
        # Verificar si existe la tabla
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'cg_entitrib'
            )
        """)
        exists = cursor.fetchone()[0]
        
        if not exists:
            print(f"{db_name}: Tabla cg_entitrib no existe")
            conn.close()
            return None
        
        # Obtener estructura
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'cg_entitrib' 
            ORDER BY ordinal_position
        """)
        columns = cursor.fetchall()
        
        print(f"\n=== ESTRUCTURA cg_entitrib en {db_name} ===")
        for col_name, col_type in columns:
            print(f"  {col_name}: {col_type}")
        
        # Obtener primary key
        cursor.execute("""
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
            WHERE tc.table_name = 'cg_entitrib'
            AND tc.constraint_type = 'PRIMARY KEY'
        """)
        pk = cursor.fetchone()
        if pk:
            print(f"Primary Key: {pk[0]}")
        else:
            print("Primary Key: None")
        
        # Contar registros
        cursor.execute("SELECT COUNT(*) FROM cg_entitrib")
        count = cursor.fetchone()[0]
        print(f"Total registros: {count}")
        
        cursor.close()
        conn.close()
        
        return columns
        
    except Exception as e:
        print(f"Error verificando {db_name}: {e}")
        return None

if __name__ == "__main__":
    print("=== VERIFICANDO ESTRUCTURA DE cg_entitrib EN CONTASIS ===\n")
    
    for db_name in POSTGRES_CONFIGS.keys():
        check_table_structure(db_name)
