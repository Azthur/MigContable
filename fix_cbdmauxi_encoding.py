from backend.app.core.database import DestSessionLocal
from sqlalchemy import text

def fix_encoding(value):
    """Corrige el encoding de un valor."""
    if value is None or not isinstance(value, str):
        return value
    try:
        # Corrección específica para caracteres corruptos comunes
        # Solo patrones específicos probados para evitar efectos secundarios
        replacements = [
            # Patrones complejos (más largos primero)
            ('├â┬▒', 'ñ'),
            ('├â┬í', 'á'),
            ('├âí', 'á'),
            # Patrones simples específicos
            ('├æ', 'Ñ'),
            ('├ü', 'ú'),
            ('├ë', 'é'),
            ('├ô', 'ó'),
            ('├á', 'á'),
            ('├▒', 'ñ'),
            ('├¡', 'í'),
            ('├Ü', 'ú'),
            ('├í', 'í'),
            ('├ì', 'í'),
            ('Dé', "D'"),
        ]
        for corrupt, correct in replacements:
            value = value.replace(corrupt, correct)
        # Re-encode as UTF-8 to ensure proper encoding
        return value.encode('utf-8', errors='replace').decode('utf-8')
    except Exception:
        return str(value)

def fix_cbdmauxi_encoding():
    """Corrige encoding de datos en cbdmauxi."""
    print("=== CORRECCION DE ENCODING EN cbdmauxi ===\n")
    
    db = DestSessionLocal()
    
    try:
        # Obtener todos los registros de cbdmauxi con campos afectados
        result = db.execute(text('SELECT "rucaux", "nomaux", "diraux", "tlfaux", "email", "contacto", "contacto2" FROM cbdmauxi WHERE "rucaux" IS NOT NULL')).fetchall()
        print(f"Registros a procesar: {len(result)}")
        
        fixed_count = 0
        for row in result:
            rucaux = row[0]
            nomaux = row[1]
            diraux = row[2]
            tlfaux = row[3]
            email = row[4]
            contacto = row[5]
            contacto2 = row[6]
            
            # Corregir encoding
            nomaux_fixed = fix_encoding(nomaux)
            diraux_fixed = fix_encoding(diraux)
            tlfaux_fixed = fix_encoding(tlfaux)
            email_fixed = fix_encoding(email)
            contacto_fixed = fix_encoding(contacto)
            contacto2_fixed = fix_encoding(contacto2)
            
            # Actualizar si hay cambios
            if (nomaux_fixed != nomaux or diraux_fixed != diraux or tlfaux_fixed != tlfaux or 
                email_fixed != email or contacto_fixed != contacto or contacto2_fixed != contacto2):
                db.execute(text("""
                    UPDATE cbdmauxi 
                    SET "nomaux" = :nomaux, "diraux" = :diraux, "tlfaux" = :tlfaux, 
                        "email" = :email, "contacto" = :contacto, "contacto2" = :contacto2
                    WHERE "rucaux" = :rucaux
                """), {
                    'nomaux': nomaux_fixed, 'diraux': diraux_fixed, 'tlfaux': tlfaux_fixed,
                    'email': email_fixed, 'contacto': contacto_fixed, 'contacto2': contacto2_fixed, 'rucaux': rucaux
                })
                fixed_count += 1
        
        db.commit()
        
        print(f"Registros corregidos: {fixed_count}")
        print("Encoding corregido en cbdmauxi")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()

def fix_staging_encoding():
    """Corrige encoding de datos en cg_entitrib (staging local)."""
    print("\n=== CORRECCION DE ENCODING EN cg_entitrib (STAGING) ===\n")
    
    db = DestSessionLocal()
    
    try:
        # Obtener todos los registros de cg_entitrib
        result = db.execute(text('SELECT ccodruc, crazsoc, cdirec, capepat, capemat, cnom1 FROM cg_entitrib WHERE ccodruc IS NOT NULL')).fetchall()
        print(f"Registros a procesar: {len(result)}")
        
        fixed_count = 0
        for row in result:
            ccodruc = row[0]
            crazsoc = row[1]
            cdirec = row[2]
            capepat = row[3]
            capemat = row[4]
            cnom1 = row[5]
            
            # Corregir encoding
            crazsoc_fixed = fix_encoding(crazsoc)
            cdirec_fixed = fix_encoding(cdirec)
            capepat_fixed = fix_encoding(capepat)
            capemat_fixed = fix_encoding(capemat)
            cnom1_fixed = fix_encoding(cnom1)
            
            # Actualizar si hay cambios
            if crazsoc_fixed != crazsoc or cdirec_fixed != cdirec or capepat_fixed != capepat or capemat_fixed != capemat or cnom1_fixed != cnom1:
                db.execute(text("""
                    UPDATE cg_entitrib 
                    SET crazsoc = :crazsoc, cdirec = :cdirec, capepat = :capepat, capemat = :capemat, cnom1 = :cnom1
                    WHERE ccodruc = :ccodruc
                """), {
                    'crazsoc': crazsoc_fixed, 'cdirec': cdirec_fixed, 'capepat': capepat_fixed,
                    'capemat': capemat_fixed, 'cnom1': cnom1_fixed, 'ccodruc': ccodruc
                })
                fixed_count += 1
        
        db.commit()
        
        print(f"Registros corregidos: {fixed_count}")
        print("Encoding corregido en cg_entitrib (staging)")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    fix_cbdmauxi_encoding()
    fix_staging_encoding()
