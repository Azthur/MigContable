import urllib.request
import urllib.error
import json
import time
from backend.app.core.database import DestSessionLocal
from sqlalchemy import text

API_BASE_URL = "https://api.org.pe/v1"
API_TOKEN = "5a4200335e5311f1b268e6bad9a0bacc"

def clean_document_number(doc_num):
    """Limpia el número de documento eliminando espacios y caracteres especiales."""
    if not doc_num:
        return None
    return doc_num.strip()

def determine_doc_type(doc_num):
    """Determina el tipo de documento basándose en la longitud."""
    if not doc_num:
        return None
    clean_num = clean_document_number(doc_num)
    if len(clean_num) == 8:
        return "DNI"
    elif len(clean_num) == 11:
        return "RUC"
    return None

def query_dni(dni):
    """Consulta la API de DNI."""
    try:
        url = f"{API_BASE_URL}/dni/{dni}"
        req = urllib.request.Request(url)
        req.add_header("Authorization", f"Bearer {API_TOKEN}")
        req.add_header("User-Agent", "curl/7.68.0")
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data.get("success"):
                return data.get("data")
        return None
    except Exception as e:
        print(f"Error consultando DNI {dni}: {e}")
        return None

def query_ruc(ruc):
    """Consulta la API de RUC."""
    try:
        url = f"{API_BASE_URL}/ruc2/{ruc}"
        req = urllib.request.Request(url)
        req.add_header("Authorization", f"Bearer {API_TOKEN}")
        req.add_header("User-Agent", "curl/7.68.0")
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data.get("success"):
                return data.get("data")
        return None
    except Exception as e:
        print(f"Error consultando RUC {ruc}: {e}")
        return None

def fix_corrupted_entities():
    """Corrige entidades con caracteres corruptos usando las APIs en staging local."""
    print("=== CORRECCIÓN DE ENTIDADES CON CARACTERES CORRUPTOS EN STAGING LOCAL ===\n")
    
    db = DestSessionLocal()
    total_fixed = 0
    total_processed = 0
    
    try:
        # Obtener registros con caracteres corruptos en crazsoc
        query = """
            SELECT ccodruc, crazsoc, capepat, capemat, cnom1, cnom2, cdirec, cdepfin, cprovfin, cdistfin
            FROM cg_entitrib 
            WHERE ccodruc IS NOT NULL 
            AND (
                crazsoc LIKE '%┬%' OR 
                capepat LIKE '%┬%' OR 
                capemat LIKE '%┬%' OR 
                cnom1 LIKE '%┬%' OR 
                cnom2 LIKE '%┬%' OR
                cdirec LIKE '%┬%' OR
                crazsoc LIKE '%éS%' OR
                crazsoc LIKE '%éP%' OR
                crazsoc LIKE '%Dé%' OR
                ccodruc = '20608103652'
            )
            LIMIT 200
        """
        
        result = db.execute(text(query)).fetchall()
        print(f"Registros con caracteres corruptos encontrados: {len(result)}")
        
        for row in result:
            ccodruc = clean_document_number(row[0])
            crazsoc = row[1]
            capepat = row[2]
            capemat = row[3]
            cnom1 = row[4]
            cnom2 = row[5]
            cdirec = row[6]
            cdepfin = row[7]
            cprovfin = row[8]
            cdistfin = row[9]
            
            print(f"\nProcesando RUC/DNI: {ccodruc}")
            print(f"  Estado actual: crazsoc='{crazsoc[:50]}...' (corrupto)")
            
            # Determinar tipo de documento
            doc_type = determine_doc_type(ccodruc)
            if not doc_type:
                print(f"  WARNING: No se pudo determinar tipo de documento para {ccodruc}")
                continue
            
            print(f"  Tipo de documento: {doc_type}")
            
            # Consultar API correspondiente
            api_data = None
            if doc_type == "DNI":
                api_data = query_dni(ccodruc)
            elif doc_type == "RUC":
                api_data = query_ruc(ccodruc)
            
            if not api_data:
                print(f"  ERROR: No se encontraron datos en la API para {ccodruc}")
                continue
            
            print(f"  OK: Datos encontrados en API")
            
            # Preparar campos a actualizar
            update_fields = {}
            
            if doc_type == "DNI":
                # Mapeo para DNI
                if api_data.get("nombre_completo"):
                    update_fields["crazsoc"] = api_data["nombre_completo"]
                if api_data.get("apellidos"):
                    # Intentar separar apellidos
                    apellidos = api_data["apellidos"].split()
                    if len(apellidos) >= 1:
                        update_fields["capepat"] = apellidos[0]
                    if len(apellidos) >= 2:
                        update_fields["capemat"] = apellidos[1]
                if api_data.get("nombres"):
                    nombres = api_data["nombres"].split()
                    if len(nombres) >= 1:
                        update_fields["cnom1"] = nombres[0]
                    if len(nombres) >= 2:
                        update_fields["cnom2"] = nombres[1]
            
            elif doc_type == "RUC":
                # Mapeo para RUC
                if api_data.get("nombre_o_razon_social"):
                    update_fields["crazsoc"] = api_data["nombre_o_razon_social"]
                if api_data.get("direccion"):
                    update_fields["cdirec"] = api_data["direccion"]
                if api_data.get("departamento"):
                    update_fields["cdepfin"] = api_data["departamento"]
                if api_data.get("provincia"):
                    update_fields["cprovfin"] = api_data["provincia"]
                if api_data.get("distrito"):
                    update_fields["cdistfin"] = api_data["distrito"]
            
            # Ejecutar UPDATE
            if update_fields:
                set_clauses = []
                params = []
                for field, value in update_fields.items():
                    set_clauses.append(f"{field} = :{field}")
                    params.append(value)
                params.append(ccodruc)
                
                update_query = f"""
                    UPDATE cg_entitrib 
                    SET {', '.join(set_clauses)}
                    WHERE ccodruc = :ccodruc
                """
                
                # Build parameter dict
                param_dict = {field: value for field, value in zip(update_fields.keys(), update_fields.values())}
                param_dict['ccodruc'] = ccodruc
                
                db.execute(text(update_query), param_dict)
                db.commit()
                
                print(f"  OK: Actualizado: {update_fields}")
                total_fixed += 1
            else:
                print(f"  WARNING: No hay campos para actualizar")
            
            total_processed += 1
            
            # Rate limiting
            time.sleep(0.5)
    
    except Exception as e:
        print(f"Error procesando: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()
    
    print(f"\n=== RESUMEN TOTAL ===")
    print(f"Registros procesados: {total_processed}")
    print(f"Registros corregidos: {total_fixed}")
    print(f"Registros no corregidos: {total_processed - total_fixed}")

if __name__ == "__main__":
    fix_corrupted_entities()
