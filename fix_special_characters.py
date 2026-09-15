import psycopg2
from psycopg2 import sql

# Configuración de empresas y sus bases de datos Contasis
empresas = {
    '002': {'nombre': 'Botica Magistral', 'db': 'contasis_002'},
    '004': {'nombre': 'GRUPO YLV', 'db': 'contasis_004'},
    '005': {'nombre': 'INDUSTRIAS', 'db': 'contasis_005'},
    '007': {'nombre': 'YELAVE NATURE', 'db': 'contasis_002'},
}

# Columnas de texto en cg_entitrib que necesitan corrección
text_columns = [
    'ctipdoc', 'cnatjur', 'capepat', 'capemat', 'cnom1', 'cnom2', 'crazsoc',
    'cdirec', 'ctelef', 'cnomcom', 'ccodtipent', 'ccodpais', 'ccodconvdi',
    'cnroregdigem', 'ccatdigem', 'csitdigem', 'cempdigem', 'ccodpag',
    'ctipviafin', 'cnomviafin', 'cnumerofin', 'cinteriorfin', 'czonafin',
    'cdistfin', 'cprovfin', 'cdepfin', 'ccodubi', 'cemail', 'ccodvend',
    'ccodocon', 'ccodcos', 'ccodcos2', 'ccodcategoria', 'ccodubicacion'
]

def fix_encoding(value):
    """Corrige el encoding de un valor de texto."""
    if value is None or not isinstance(value, str):
        return value
    try:
        # Intentar corregir encoding común de Latin-1 a UTF-8
        if isinstance(value, bytes):
            return value.decode('utf-8', errors='replace')
        else:
            # Re-encode as UTF-8 to ensure proper encoding
            return value.encode('utf-8', errors='replace').decode('utf-8')
    except Exception as e:
        print(f"Error corrigiendo valor '{value}': {e}")
        return value

def fix_table(host, port, database, user, password):
    """Corrige caracteres especiales en una tabla cg_entitrib."""
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
        conn.autocommit = False
        cursor = conn.cursor()
        
        # Obtener todos los registros
        cursor.execute("SELECT id, company_id FROM cg_entitrib")
        rows = cursor.fetchall()
        
        print(f"Base de datos: {database}")
        print(f"Total registros a procesar: {len(rows)}")
        
        fixed_count = 0
        
        for row_id, company_id in rows:
            # Obtener valores actuales
            set_clauses = []
            params = []
            
            for col in text_columns:
                cursor.execute(sql.SQL("SELECT {} FROM cg_entitrib WHERE id = %s").format(
                    sql.Identifier(col)
                ), (row_id,))
                value = cursor.fetchone()[0]
                
                if value:
                    fixed_value = fix_encoding(value)
                    if fixed_value != value:
                        set_clauses.append(sql.SQL("{} = %s").format(sql.Identifier(col)))
                        params.append(fixed_value)
            
            if set_clauses:
                # Actualizar el registro
                query = sql.SQL("UPDATE cg_entitrib SET {} WHERE id = %s").format(
                    sql.SQL(', ').join(set_clauses)
                )
                params.append(row_id)
                cursor.execute(query, params)
                fixed_count += 1
                if fixed_count % 100 == 0:
                    print(f"  Procesados: {fixed_count}/{len(rows)}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"Registros corregidos: {fixed_count}")
        print(f"Registros sin cambios: {len(rows) - fixed_count}")
        print("-" * 50)
        
        return fixed_count
        
    except Exception as e:
        print(f"Error procesando base de datos {database}: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return 0

if __name__ == "__main__":
    # Configuración de conexión a Contasis
    host = "192.168.2.90"
    port = 5432
    user = "postgres"
    password = "postgres"
    
    print("=== CORRECCIÓN DE CARACTERES ESPECIALES EN cg_entitrib ===\n")
    
    total_fixed = 0
    for codcia, info in empresas.items():
        print(f"Empresa: {info['nombre']} (codcia: {codcia})")
        fixed = fix_table(host, port, info['db'], user, password)
        total_fixed += fixed
    
    print(f"\n=== RESUMEN TOTAL ===")
    print(f"Total registros corregidos: {total_fixed}")
