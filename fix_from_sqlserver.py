import pyodbc
import psycopg2

# Configuración SQL Server
SQL_SERVER_CONFIG = {
    'server': '192.168.1.17,1433',
    'database': 'YELAVE22',
    'uid': 'sa',
    'pwd': 'Pa$$word'
}

# Configuración PostgreSQL (Contasis) - múltiples bases de datos
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

# Mapeo de codcia a base de datos Contasis
CODCIA_TO_DB = {
    '002': 'contasis_002',
    '004': 'contasis_004',
    '005': 'contasis_005',
    '007': 'contasis_002'
}

def connect_sql_server():
    """Conecta a SQL Server."""
    try:
        conn_str = (
            f"DRIVER=ODBC Driver 18 for SQL Server;"
            f"SERVER={SQL_SERVER_CONFIG['server']};"
            f"DATABASE={SQL_SERVER_CONFIG['database']};"
            f"UID={SQL_SERVER_CONFIG['uid']};"
            f"PWD={SQL_SERVER_CONFIG['pwd']};"
            f"TrustServerCertificate=yes;"
            f"Timeout=30"
        )
        conn = pyodbc.connect(conn_str)
        return conn
    except Exception as e:
        print(f"Error conectando a SQL Server: {e}")
        return None

def connect_postgres(db_name):
    """Conecta a PostgreSQL."""
    config = POSTGRES_CONFIGS.get(db_name)
    if not config:
        print(f"Configuración no encontrada para {db_name}")
        return None
    
    try:
        conn = psycopg2.connect(
            host=config['host'],
            port=config['port'],
            database=config['database'],
            user=config['user'],
            password=config['password']
        )
        return conn
    except Exception as e:
        print(f"Error conectando a PostgreSQL ({db_name}): {e}")
        return None

def fix_encoding(value):
    """Corrige el encoding de un valor."""
    if value is None or not isinstance(value, str):
        return value
    try:
        # Re-encode as UTF-8 to ensure proper encoding
        return value.encode('utf-8', errors='replace').decode('utf-8')
    except Exception:
        return str(value)

def extract_from_sqlserver():
    """Extrae datos de CbdMAuxi de SQL Server."""
    conn = connect_sql_server()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        query = """
            SELECT codcia, codaux, nomaux, diraux, rucaux, tlfaux, email, contacto, 
                   tpodoc, ApePat, ApeMat, NomBres, fax, codven, codest, codret
            FROM CbdMAuxi
            WHERE rucaux IS NOT NULL AND rucaux <> ''
        """
        cursor.execute(query)
        
        # Agrupar por codcia
        data_by_codcia = {}
        for row in cursor.fetchall():
            codcia = str(row[0]).strip()
            if codcia not in data_by_codcia:
                data_by_codcia[codcia] = []
            data_by_codcia[codcia].append(row)
        
        cursor.close()
        conn.close()
        
        print(f"Extraídos {sum(len(v) for v in data_by_codcia.values())} registros de SQL Server")
        for codcia, records in data_by_codcia.items():
            print(f"  codcia {codcia}: {len(records)} registros")
        
        return data_by_codcia
    except Exception as e:
        print(f"Error extrayendo de SQL Server: {e}")
        conn.close()
        return None

def update_contasis(data_by_codcia):
    """Actualiza cg_entitrib en Contasis con datos corregidos usando UPDATE."""
    total_updated = 0
    total_errors = 0
    
    for codcia, records in data_by_codcia.items():
        # Omitir codcia 001 (dado de baja)
        if codcia == '001':
            print(f"Omitiendo codcia {codcia} (dado de baja)")
            continue
            
        db_name = CODCIA_TO_DB.get(codcia)
        if not db_name:
            print(f"WARNING: No hay mapeo de base de datos para codcia {codcia}")
            continue
        
        print(f"\n=== Procesando codcia {codcia} -> {db_name} ===")
        
        pg_conn = connect_postgres(db_name)
        if not pg_conn:
            continue
        
        try:
            pg_cursor = pg_conn.cursor()
            
            # Actualizar registros existentes con encoding corregido
            for row in records:
                (codcia_val, codaux, nomaux, diraux, rucaux, tlfaux, email, contacto,
                 tpodoc, ApePat, ApeMat, NomBres, fax, codven, codest, codret) = row
                
                # Limpiar y corregir encoding
                rucaux_clean = fix_encoding(str(rucaux).strip()) if rucaux else None
                nomaux_fixed = fix_encoding(str(nomaux).strip()) if nomaux else None
                diraux_fixed = fix_encoding(str(diraux).strip()) if diraux else None
                tlfaux_fixed = fix_encoding(str(tlfaux).strip()) if tlfaux else None
                email_fixed = fix_encoding(str(email).strip()) if email else None
                contacto_fixed = fix_encoding(str(contacto).strip()) if contacto else None
                ApePat_fixed = fix_encoding(str(ApePat).strip()) if ApePat else None
                ApeMat_fixed = fix_encoding(str(ApeMat).strip()) if ApeMat else None
                NomBres_fixed = fix_encoding(str(NomBres).strip()) if NomBres else None
                
                if not rucaux_clean:
                    continue
                
                # Verificar si existe registro
                pg_cursor.execute(
                    "SELECT ccodruc FROM cg_entitrib WHERE ccodruc = %s",
                    (rucaux_clean,)
                )
                existing = pg_cursor.fetchone()
                
                if existing:
                    # Actualizar registro existente - solo campos con datos
                    update_fields = []
                    update_values = []
                    
                    if nomaux_fixed:
                        update_fields.append("crazsoc = %s")
                        update_values.append(nomaux_fixed)
                    if diraux_fixed:
                        update_fields.append("cdirec = %s")
                        update_values.append(diraux_fixed)
                    if tlfaux_fixed:
                        update_fields.append("ctelef = %s")
                        update_values.append(tlfaux_fixed)
                    if email_fixed:
                        update_fields.append("cemail = %s")
                        update_values.append(email_fixed)
                    if ApePat_fixed:
                        update_fields.append("capepat = %s")
                        update_values.append(ApePat_fixed)
                    if ApeMat_fixed:
                        update_fields.append("capemat = %s")
                        update_values.append(ApeMat_fixed)
                    if NomBres_fixed:
                        update_fields.append("cnom1 = %s")
                        update_values.append(NomBres_fixed)
                    
                    if update_fields:
                        update_query = f"UPDATE cg_entitrib SET {', '.join(update_fields)} WHERE ccodruc = %s"
                        update_values.append(rucaux_clean)
                        pg_cursor.execute(update_query, update_values)
                        total_updated += 1
                else:
                    # Insertar nuevo registro - solo campos principales
                    insert_query = """
                        INSERT INTO cg_entitrib 
                        (ccodruc, crazsoc, cdirec, ctelef, cemail, capepat, capemat, cnom1, 
                         ctipdoc, cnatjur, cnom2, cnomcom, nbuencon, nagenper, nagenret, 
                         nutianu, nagepor, nagemonmin, ccodtipent, ncondi, ccodpais, 
                         ccodconvdi, cnroregdigem, ccatdigem, csitdigem, cempdigem, 
                         ccodpag, nbloruc, cestadoruc, ncreditos, ncreditod, ccodlprecio, 
                         nexpcon, ctipviafin, cnomviafin, cnumerofin, cinteriorfin, 
                         czonafin, cdistfin, cprovfin, cdepfin, ccodubi, ccodvend, 
                         nflgvend, ccodocon, ccodcos, ccodcos2, ccodcategoria, 
                         ccodubicacion, nflgclieinterno)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 
                                '1', '1', '', '', 0, 0, 0, 0, 0.00, 0.00, '', 0, '', 
                                '', '', '', '', '', '', 0, '', 0.00, 0.00, '', 0, '', 
                                '', '', '', '', '', '', '', '', 0, '', '', '', '', '', 
                                '', '', '', '', 0)
                    """
                    pg_cursor.execute(insert_query, (
                        rucaux_clean, nomaux_fixed or '', diraux_fixed or '', tlfaux_fixed or '', 
                        email_fixed or '', ApePat_fixed or '', ApeMat_fixed or '', NomBres_fixed or ''
                    ))
                    total_updated += 1
            
            pg_conn.commit()
            pg_cursor.close()
            pg_conn.close()
            
            print(f"OK: Actualizados {total_updated} registros en {db_name}")
            
        except Exception as e:
            print(f"ERROR: Error actualizando {db_name}: {e}")
            total_errors += 1
            if pg_conn:
                pg_conn.rollback()
                pg_conn.close()
    
    return total_updated, total_errors

if __name__ == "__main__":
    print("=== CORRECCION DE ENTIDADES DESDE SQL SERVER ===\n")
    
    # Extraer datos de SQL Server
    data_by_codcia = extract_from_sqlserver()
    
    if not data_by_codcia:
        print("ERROR: No se pudieron extraer datos de SQL Server")
        exit(1)
    
    # Actualizar Contasis
    updated, errors = update_contasis(data_by_codcia)
    
    print(f"\n=== RESUMEN ===")
    print(f"Registros actualizados: {updated}")
    print(f"Errores: {errors}")
