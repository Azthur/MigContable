from backend.app.core.database import SourceSessionLocal, DestSessionLocal
from sqlalchemy import text

def fix_encoding(value):
    """Corrige el encoding de un valor."""
    if value is None or not isinstance(value, str):
        return value
    try:
        # Re-encode as UTF-8 to ensure proper encoding
        return value.encode('utf-8', errors='replace').decode('utf-8')
    except Exception:
        return str(value)

def fix_migconta_data():
    """Corrige datos en cbdmauxi en migconta_db usando datos de SQL Server."""
    print("=== CORRECCION DE DATOS EN MIGCONTA_DB ===\n")
    
    # Conectar a SQL Server (origen)
    source_db = SourceSessionLocal()
    
    # Conectar a migconta_db (destino)
    dest_db = DestSessionLocal()
    
    try:
        # Extraer datos de SQL Server
        print("Extrayendo datos de SQL Server...")
        query = """
            SELECT codcia, codaux, nomaux, diraux, rucaux, tlfaux, email, contacto, 
                   tpodoc, ApePat, ApeMat, NomBres, fax, codven, codest, codret
            FROM CbdMAuxi
            WHERE rucaux IS NOT NULL AND rucaux <> ''
        """
        result = source_db.execute(text(query)).fetchall()
        
        # Agrupar por codcia
        data_by_codcia = {}
        for row in result:
            codcia = str(row[0]).strip()
            if codcia not in data_by_codcia:
                data_by_codcia[codcia] = []
            data_by_codcia[codcia].append(row)
        
        print(f"Extraidos {sum(len(v) for v in data_by_codcia.values())} registros de SQL Server")
        for codcia, records in data_by_codcia.items():
            print(f"  codcia {codcia}: {len(records)} registros")
        
        # Omitir codcia 001 (dado de baja)
        if '001' in data_by_codcia:
            print("Omitiendo codcia 001 (dado de baja)")
            del data_by_codcia['001']
        
        # Actualizar cbdmauxi en migconta_db
        print("\nActualizando cbdmauxi en migconta_db...")
        
        # Borrar datos existentes en cbdmauxi
        dest_db.execute(text("DELETE FROM cbdmauxi"))
        print("Borrados datos existentes en cbdmauxi")
        
        # Insertar datos corregidos
        total_inserted = 0
        for codcia, records in data_by_codcia.items():
            print(f"Insertando registros para codcia {codcia}...")
            
            for row in records:
                (codcia_val, codaux, nomaux, diraux, rucaux, tlfaux, email, contacto,
                 tpodoc, ApePat, ApeMat, NomBres, fax, codven, codest, codret) = row
                
                # Limpiar y corregir encoding
                codcia_clean = fix_encoding(str(codcia_val).strip()) if codcia_val else None
                codaux_clean = fix_encoding(str(codaux).strip()) if codaux else None
                nomaux_fixed = fix_encoding(str(nomaux).strip()) if nomaux else None
                diraux_fixed = fix_encoding(str(diraux).strip()) if diraux else None
                rucaux_clean = fix_encoding(str(rucaux).strip()) if rucaux else None
                tlfaux_fixed = fix_encoding(str(tlfaux).strip()) if tlfaux else None
                email_fixed = fix_encoding(str(email).strip()) if email else None
                contacto_fixed = fix_encoding(str(contacto).strip()) if contacto else None
                tpodoc_clean = fix_encoding(str(tpodoc).strip()) if tpodoc else None
                ApePat_fixed = fix_encoding(str(ApePat).strip()) if ApePat else None
                ApeMat_fixed = fix_encoding(str(ApeMat).strip()) if ApeMat else None
                NomBres_fixed = fix_encoding(str(NomBres).strip()) if NomBres else None
                fax_fixed = fix_encoding(str(fax).strip()) if fax else None
                codven_clean = fix_encoding(str(codven).strip()) if codven else None
                codest_clean = fix_encoding(str(codest).strip()) if codest else None
                codret_clean = fix_encoding(str(codret).strip()) if codret else None
                
                if not rucaux_clean:
                    continue
                
                # Insertar en cbdmauxi
                insert_query = """
                    INSERT INTO cbdmauxi 
                    (codcia, clfaux, codaux, nomaux, diraux, rucaux, tlfaux, email, contacto, 
                     email2, contacto2, tpodoc, ApePat, ApeMat, NomBres, fax, dueño, codnac, 
                     codzon, coddep, codpro, coddis, codven, codest, codret, ptopar, ptolle, 
                     crenac, creusa, creeur, fchalt, email0, tpovta, pais, _migration_id, 
                     company_id, idcontrol, T_Ventasruc, C_TRUC, T_filtro, C_cnatjur, 
                     C_crazsoc, C_crazsoc_1, C_ApePat, C_ApeMat, C_NomBres, CC_ApePat, 
                     CC_ApeMat, CC_NomBres, C_tipoauxiliar, C_tipoauxiliar_f)
                    VALUES (:codcia, '', :codaux, :nomaux, :diraux, :rucaux, :tlfaux, :email, :contacto, 
                            '', '', :tpodoc, :ApePat, :ApeMat, :NomBres, :fax, '', '', 
                            '', '', '', '', :codven, :codest, :codret, '', '', 
                            0, 0, 0, NULL, '', '', '', NULL, 
                            NULL, NULL, NULL, NULL, '', 
                            '', '', '', '', '', '', 
                            '', '', '', '', '', '')
                """
                dest_db.execute(text(insert_query), {
                    'codcia': codcia_clean, 'codaux': codaux_clean, 'nomaux': nomaux_fixed, 
                    'diraux': diraux_fixed, 'rucaux': rucaux_clean, 'tlfaux': tlfaux_fixed, 
                    'email': email_fixed, 'contacto': contacto_fixed, 'tpodoc': tpodoc_clean, 
                    'ApePat': ApePat_fixed, 'ApeMat': ApeMat_fixed, 'NomBres': NomBres_fixed, 
                    'fax': fax_fixed, 'codven': codven_clean, 'codest': codest_clean, 'codret': codret_clean
                })
                total_inserted += 1
        
        dest_db.commit()
        
        print(f"\n=== RESUMEN ===")
        print(f"Registros insertados en cbdmauxi: {total_inserted}")
        print("Datos corregidos con encoding UTF-8")
        print("Ahora puedes re-ejecutar el ETL para migrar a Contasis")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        dest_db.rollback()
        return False
    finally:
        source_db.close()
        dest_db.close()

if __name__ == "__main__":
    fix_migconta_data()
