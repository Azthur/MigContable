#!/usr/bin/env python3
"""
Script para configuración masiva de empresas en el sistema de migración del Libro 209.
Inserta configuración de cuentas y campos para múltiples empresas automáticamente.
"""

import sys
import os
sys.path.insert(0, '/app')

import logging
logging.disable(logging.CRITICAL)

from backend.app.core.database import get_dest_db
from sqlalchemy import text

def get_empresas(db):
    """Obtiene todas las empresas activas del sistema con sus conexiones Contasis."""
    try:
        result = db.execute(text("""
            SELECT c.id, c.name, fc.host, fc.port, fc.database_name, fc.username, fc.password
            FROM companies c
            LEFT JOIN final_dest_connections fc ON c.id = fc.company_id AND fc.is_active = true
            WHERE c.is_active = true
            ORDER BY c.id
        """))
        empresas = result.fetchall()
        return empresas
    except Exception as e:
        print(f"Error obteniendo empresas: {e}")
        return []

def get_subcategorias_209(db):
    """Obtiene las subcategorías del libro 209."""
    try:
        # Obtener subcategorías con IDs específicos del libro 209 (80, 81, 82, 83, 116)
        result = db.execute(text("""
            SELECT id, nombre 
            FROM mapeo_subcategorias 
            WHERE id IN (80, 81, 82, 83, 116)
            ORDER BY id
        """))
        subcategorias = result.fetchall()
        return subcategorias
    except Exception as e:
        print(f"Error obteniendo subcategorías: {e}")
        return []

def bulk_insert_config_cuentas(db, empresas, subcategorias):
    """Inserta configuración de cuentas para todas las empresas y subcategorías."""
    try:
        print("=== INSERTANDO CONFIGURACIÓN DE CUENTAS MASIVA ===")
        
        # Cuentas contables que funcionan (validadas en cf_plan)
        cuenta_debito = '6599004'  # GASTOS DE MOVILIDAD DEL PERSONAL
        cuenta_credito = '469901'   # CUENTA CREDITO
        
        inserted_count = 0
        
        for empresa in empresas:
            empresa_id = empresa[0]
            empresa_nombre = empresa[1]
            contasis_host = empresa[2]
            contasis_port = empresa[3]
            contasis_database = empresa[4]
            contasis_username = empresa[5]
            contasis_password = empresa[6]
            
            # Generar codcia basado en empresa_id (formato: 05 para empresa 5)
            codcia = str(empresa_id).zfill(2)
            
            # Verificar si existe conexión Contasis
            if not contasis_host:
                print(f"  Saltando: Empresa {empresa_id} ({empresa_nombre}) - Sin conexión Contasis configurada")
                continue
            
            for subcat in subcategorias:
                subcat_id = subcat[0]
                subcat_nombre = subcat[1]
                
                # Verificar si ya existe
                check = db.execute(text("""
                    SELECT COUNT(*) FROM Libro209_ConfigCuentas
                    WHERE empresa_id = :empresa_id AND subcategoria_id = :subcat_id
                """), {"empresa_id": empresa_id, "subcat_id": subcat_id})
                
                if check.scalar() > 0:
                    print(f"  Saltando: Empresa {empresa_id} ({empresa_nombre}) - Subcategoría {subcat_id} ({subcat_nombre}) - Ya existe")
                    continue
                
                # Insertar configuración de cuentas
                db.execute(text("""
                    INSERT INTO Libro209_ConfigCuentas 
                    (empresa_id, subcategoria_id, tipo_linea, cuenta_contable, descripcion, orden)
                    VALUES 
                    (:empresa_id, :subcat_id, 'DEBITO', :cuenta_debito, 'GASTOS DE MOVILIDAD DEL PERSONAL', 1),
                    (:empresa_id, :subcat_id, 'CREDITO', :cuenta_credito, 'CUENTA CREDITO', 2)
                """), {
                    "empresa_id": empresa_id,
                    "subcat_id": subcat_id,
                    "cuenta_debito": cuenta_debito,
                    "cuenta_credito": cuenta_credito
                })
                
                inserted_count += 2
                print(f"  Insertado: Empresa {empresa_id} ({empresa_nombre}) - Subcategoría {subcat_id} ({subcat_nombre})")
        
        db.commit()
        print(f"\nTotal de registros de cuentas insertados: {inserted_count}")
        return True
        
    except Exception as e:
        print(f"Error insertando configuración de cuentas: {e}")
        db.rollback()
        return False

def bulk_insert_config_campos(db, empresas, subcategorias):
    """Inserta configuración de campos para todas las empresas y subcategorías."""
    try:
        print("\n=== INSERTANDO CONFIGURACIÓN DE CAMPOS MASIVA ===")
        
        # Configuración de campos base (misma para todas las subcategorías)
        campos_config = [
            ('Fecha', 'cper', 'STRING', None, True, 1),
            ('Fecha', 'cmes', 'STRING', None, True, 2),
            ('Fecha', 'ffechadoc', 'DATE', None, True, 3),
            ('C_tipocambiosunat', 'ntc', 'NUMERIC', None, True, 4),
            ('C_tipomoneda', 'ccodmon', 'STRING', None, True, 5),
            ('Importe', 'ndebe', 'NUMERIC', None, True, 6),
            ('Importe', 'nhaber', 'NUMERIC', None, True, 7),
            ('C_descripcion', 'cglosa', 'STRING', None, True, 8),
            ('C_tipodoc', 'ccoddoc', 'STRING', None, True, 9),
            ('C_serie', 'cserie', 'STRING', None, False, 10),
            ('C_numero', 'cnumero', 'STRING', None, False, 11),
            ('C_ruc', 'ccodruc', 'STRING', None, False, 12),
            ('C_razon_social', 'cdes', 'STRING', None, False, 13),
            ('FIXED', 'ccodori', 'STRING', '209', True, 14),
            ('FIXED', 'cdoc_dc', 'STRING', '00', True, 15),
            ('FIXED', 'ccodenti', 'STRING', '01', True, 16),
            ('FIXED', 'clecvmes', 'STRING', '07', True, 17),
            ('FIXED', 'cledmcmes', 'STRING', '07', True, 18),
            ('FIXED', 'clecvesta', 'STRING', '1', True, 19),
            ('FIXED', 'cledmcesta', 'STRING', '1', True, 20)
        ]
        
        inserted_count = 0
        
        for empresa in empresas:
            empresa_id = empresa[0]
            empresa_nombre = empresa[1]
            contasis_host = empresa[2]
            
            # Verificar si existe conexión Contasis
            if not contasis_host:
                continue
            
            for subcat in subcategorias:
                subcat_id = subcat[0]
                subcat_nombre = subcat[1]
                
                # Verificar si ya existe configuración
                check = db.execute(text("""
                    SELECT COUNT(*) FROM Libro209_ConfigCampos
                    WHERE empresa_id = :empresa_id AND subcategoria_id = :subcat_id
                """), {"empresa_id": empresa_id, "subcat_id": subcat_id})
                
                if check.scalar() > 0:
                    print(f"  Saltando: Empresa {empresa_id} ({empresa_nombre}) - Subcategoría {subcat_id} ({subcat_nombre}) - Ya existe")
                    continue
                
                # Insertar configuración de campos
                for campo_origen, campo_destino, tipo_dato, valor_fijo, es_requerido, orden in campos_config:
                    db.execute(text("""
                        INSERT INTO Libro209_ConfigCampos 
                        (empresa_id, subcategoria_id, campo_origen, campo_destino, tipo_dato, valor_fijo, es_requerido, orden)
                        VALUES 
                        (:empresa_id, :subcat_id, :campo_origen, :campo_destino, :tipo_dato, :valor_fijo, :es_requerido, :orden)
                    """), {
                        "empresa_id": empresa_id,
                        "subcat_id": subcat_id,
                        "campo_origen": campo_origen,
                        "campo_destino": campo_destino,
                        "tipo_dato": tipo_dato,
                        "valor_fijo": valor_fijo,
                        "es_requerido": es_requerido,
                        "orden": orden
                    })
                    inserted_count += 1
                
                print(f"  Insertado: Empresa {empresa_id} ({empresa_nombre}) - Subcategoría {subcat_id} ({subcat_nombre}) - {len(campos_config)} campos")
        
        db.commit()
        print(f"\nTotal de registros de campos insertados: {inserted_count}")
        return True
        
    except Exception as e:
        print(f"Error insertando configuración de campos: {e}")
        db.rollback()
        return False

def bulk_insert_empresas_contasis(db, empresas):
    """Inserta relaciones empresa - Contasis para todas las empresas."""
    try:
        print("\n=== INSERTANDO RELACIONES EMPRESA - CONTASIS ===")
        
        inserted_count = 0
        
        for empresa in empresas:
            empresa_id = empresa[0]
            empresa_nombre = empresa[1]
            contasis_host = empresa[2]
            contasis_port = empresa[3]
            contasis_database = empresa[4]
            contasis_username = empresa[5]
            contasis_password = empresa[6]
            
            # Generar codcia basado en empresa_id (formato: 05 para empresa 5)
            codcia = str(empresa_id).zfill(2)
            
            # Verificar si existe conexión Contasis
            if not contasis_host:
                print(f"  Saltando: Empresa {empresa_id} ({empresa_nombre}) - Sin conexión Contasis configurada")
                continue
            
            # Verificar si ya existe
            check = db.execute(text("""
                SELECT COUNT(*) FROM Libro209_EmpresaContasis
                WHERE codcia = :codcia AND empresa_id = :empresa_id
            """), {"codcia": codcia, "empresa_id": empresa_id})
            
            if check.scalar() > 0:
                print(f"  Saltando: Empresa {empresa_id} ({empresa_nombre}) - Relación ya existe")
                continue
            
            # Insertar relación empresa - Contasis
            db.execute(text("""
                INSERT INTO Libro209_EmpresaContasis 
                (codcia, empresa_id, contasis_host, contasis_port, contasis_database, contasis_username, contasis_password)
                VALUES 
                (:codcia, :empresa_id, :contasis_host, :contasis_port, :contasis_database, :contasis_username, :contasis_password)
            """), {
                "codcia": codcia,
                "empresa_id": empresa_id,
                "contasis_host": contasis_host,
                "contasis_port": contasis_port,
                "contasis_database": contasis_database,
                "contasis_username": contasis_username,
                "contasis_password": contasis_password
            })
            
            inserted_count += 1
            print(f"  Insertado: Empresa {empresa_id} ({empresa_nombre}) - codcia: {codcia} - Contasis: {contasis_host}/{contasis_database}")
        
        db.commit()
        print(f"\nTotal de relaciones empresa - Contasis insertadas: {inserted_count}")
        return True
        
    except Exception as e:
        print(f"Error insertando relaciones empresa - Contasis: {e}")
        db.rollback()
        return False

def verify_configuration(db, empresas, subcategorias):
    """Verifica la configuración insertada."""
    try:
        print("\n=== VERIFICANDO CONFIGURACIÓN ===")
        
        # Verificar cuentas
        result = db.execute(text("""
            SELECT empresa_id, subcategoria_id, tipo_linea, cuenta_contable
            FROM Libro209_ConfigCuentas
            ORDER BY empresa_id, subcategoria_id, tipo_linea
        """))
        
        cuentas = result.fetchall()
        print(f"Total de registros de cuentas: {len(cuentas)}")
        
        # Verificar campos
        result = db.execute(text("""
            SELECT empresa_id, subcategoria_id, COUNT(*) as num_campos
            FROM Libro209_ConfigCampos
            GROUP BY empresa_id, subcategoria_id
            ORDER BY empresa_id, subcategoria_id
        """))
        
        campos_por_empresa = result.fetchall()
        print(f"Configuración de campos por empresa/subcategoría:")
        for row in campos_por_empresa:
            print(f"  Empresa {row[0]} - Subcategoría {row[1]}: {row[2]} campos")
        
        return True
        
    except Exception as e:
        print(f"Error verificando configuración: {e}")
        return False

def main():
    """Función principal."""
    db = next(get_dest_db())
    
    try:
        print("=== CONFIGURACIÓN MASIVA DE EMPRESAS PARA LIBRO 209 ===\n")
        
        # Obtener empresas y subcategorías
        empresas = get_empresas(db)
        subcategorias = get_subcategorias_209(db)
        
        if not empresas:
            print("No se encontraron empresas activas")
            return False
        
        if not subcategorias:
            print("No se encontraron subcategorías del libro 209")
            return False
        
        print(f"Empresas encontradas: {len(empresas)}")
        for emp in empresas:
            print(f"  - ID: {emp[0]}, Nombre: {emp[1]}")
        
        print(f"\nSubcategorías del libro 209 encontradas: {len(subcategorias)}")
        for sub in subcategorias:
            print(f"  - ID: {sub[0]}, Nombre: {sub[1]}")
        
        # Insertar configuración masiva
        success_empresas_contasis = bulk_insert_empresas_contasis(db, empresas)
        success_cuentas = bulk_insert_config_cuentas(db, empresas, subcategorias)
        success_campos = bulk_insert_config_campos(db, empresas, subcategorias)
        
        if success_empresas_contasis and success_cuentas and success_campos:
            # Verificar configuración
            verify_configuration(db, empresas, subcategorias)
            print("\n=== CONFIGURACIÓN MASIVA COMPLETADA EXITOSAMENTE ===")
            return True
        else:
            print("\n=== ERROR EN CONFIGURACIÓN MASIVA ===")
            return False
            
    except Exception as e:
        print(f"Error en proceso de configuración masiva: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
