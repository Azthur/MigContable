#!/usr/bin/env python3
"""
Script de migración independiente para el Libro 209.
No tiene dependencias del sistema MigConta.
Lee configuración desde PostgreSQL (MigConta), extrae de SQL Server, e inyecta a Contasis.
Diseñado para ejecución como cron job.
"""

import sys
import os
import logging
from datetime import datetime
from decimal import Decimal
import pyodbc
import psycopg2
from psycopg2 import sql, extras
import json

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/libro209_migrator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class Libro209MigratorStandalone:
    def __init__(self, codcia, postgres_config, sql_server_config):
        """
        Inicializa el migrador del Libro 209.
        
        Args:
            codcia: Código de empresa en SQL Server
            postgres_config: Dict con configuración de PostgreSQL (MigConta)
            sql_server_config: Dict con configuración de SQL Server
        """
        self.codcia = codcia
        self.postgres_config = postgres_config
        self.sql_server_config = sql_server_config
        self.contasis_config = None
        self.empresa_id = None
        self.postgres_conn = None
        self.sql_server_conn = None
        self.contasis_conn = None
        
    def connect_postgres(self):
        """Conecta a PostgreSQL (MigConta) y carga configuración de Contasis."""
        try:
            # Usar DSN con opciones de encoding
            dsn = f"host={self.postgres_config['host']} port={self.postgres_config['port']} dbname={self.postgres_config['database']} user={self.postgres_config['username']} password={self.postgres_config['password']}"
            self.postgres_conn = psycopg2.connect(dsn)
            logger.info(f"Conectado a PostgreSQL (MigConta): {self.postgres_config['host']}")
            
            # Cargar configuración de Contasis desde PostgreSQL
            self.load_contasis_config()
            
            return True
        except Exception as e:
            logger.error(f"Error conectando a PostgreSQL: {e}")
            return False
    
    def load_contasis_config(self):
        """Carga configuración de Contasis desde tabla libro209_empresacontasis."""
        try:
            cursor = self.postgres_conn.cursor()
            query = """
                SELECT empresa_id, contasis_host, contasis_port, contasis_database, contasis_username, contasis_password
                FROM libro209_empresacontasis
                WHERE codcia = %s AND activo = true
            """
            cursor.execute(query, (self.codcia,))
            result = cursor.fetchone()
            
            if result:
                self.empresa_id = result[0]
                self.contasis_config = {
                    'host': result[1],
                    'port': result[2],
                    'database': result[3],
                    'username': result[4],
                    'password': result[5]
                }
                logger.info(f"Configuración de Contasis cargada para empresa {self.empresa_id} (codcia: {self.codcia})")
            else:
                logger.error(f"No se encontró configuración de Contasis para codcia: {self.codcia}")
                raise Exception(f"Configuración de Contasis no encontrada para codcia: {self.codcia}")
            
            cursor.close()
        except Exception as e:
            logger.error(f"Error cargando configuración de Contasis: {e}")
            raise
    
    def connect_contasis(self):
        """Conecta a Contasis (PostgreSQL)."""
        try:
            conn_str = f"postgresql://{self.contasis_config['username']}:{self.contasis_config['password']}@{self.contasis_config['host']}:{self.contasis_config['port']}/{self.contasis_config['database']}"
            self.contasis_conn = psycopg2.connect(conn_str)
            logger.info(f"Conectado a Contasis: {self.contasis_config['host']}")
            return True
        except Exception as e:
            logger.error(f"Error conectando a Contasis: {e}")
            return False
    
    def close_connections(self):
        """Cierra todas las conexiones."""
        if self.postgres_conn:
            self.postgres_conn.close()
        if self.sql_server_conn:
            self.sql_server_conn.close()
        if self.contasis_conn:
            self.contasis_conn.close()
        logger.info("Conexiones cerradas")
    
    def get_subcategorias(self):
        """Obtiene las subcategorías del libro 209 para la empresa."""
        try:
            cursor = self.postgres_conn.cursor()
            query = """
                SELECT DISTINCT subcategoria_id 
                FROM libro209_configcuentas 
                WHERE empresa_id = %s AND activo = true
            """
            cursor.execute(query, (self.empresa_id,))
            subcategorias = [row[0] for row in cursor.fetchall()]
            cursor.close()
            logger.info(f"Subcategorías encontradas: {subcategorias}")
            return subcategorias
        except Exception as e:
            logger.error(f"Error obteniendo subcategorías: {e}")
            return []
    
    def get_config_cuentas(self, subcategoria_id):
        """Obtiene configuración de cuentas para una subcategoría."""
        try:
            cursor = self.postgres_conn.cursor()
            query = """
                SELECT tipo_linea, cuenta_contable 
                FROM libro209_configcuentas 
                WHERE empresa_id = %s AND subcategoria_id = %s AND activo = true
                ORDER BY orden
            """
            cursor.execute(query, (self.empresa_id, subcategoria_id))
            cuentas = {row[0]: row[1] for row in cursor.fetchall()}
            cursor.close()
            return cuentas
        except Exception as e:
            logger.error(f"Error obteniendo configuración de cuentas: {e}")
            return {}
    
    def get_config_campos(self, subcategoria_id):
        """Obtiene configuración de campos para una subcategoría."""
        try:
            cursor = self.postgres_conn.cursor()
            query = """
                SELECT campo_origen, campo_destino, tipo_dato, valor_fijo, formula_transformacion, es_requerido, orden
                FROM libro209_configcampos 
                WHERE empresa_id = %s AND subcategoria_id = %s AND activo = true
                ORDER BY orden
            """
            cursor.execute(query, (self.empresa_id, subcategoria_id))
            campos = []
            for row in cursor.fetchall():
                campos.append({
                    'campo_origen': row[0],
                    'campo_destino': row[1],
                    'tipo_dato': row[2],
                    'valor_fijo': row[3],
                    'formula_transformacion': row[4],
                    'es_requerido': row[5],
                    'orden': row[6]
                })
            cursor.close()
            return campos
        except Exception as e:
            logger.error(f"Error obteniendo configuración de campos: {e}")
            return []
    
    def connect_sql_server(self):
        """Conecta a SQL Server para datos origen."""
        try:
            conn_str = (
                f"DRIVER={self.sql_server_config['driver']};"
                f"SERVER={self.sql_server_config['server']};"
                f"DATABASE={self.sql_server_config['database']};"
                f"UID={self.sql_server_config['username']};"
                f"PWD={self.sql_server_config['password']}"
            )
            self.sql_server_conn = pyodbc.connect(conn_str)
            logger.info(f"Conectado a SQL Server: {self.sql_server_config['server']}")
            return True
        except Exception as e:
            logger.error(f"Error conectando a SQL Server: {e}")
            return False
    
    def get_tabla_origen(self, subcategoria_id):
        """Obtiene el nombre de la tabla origen según la subcategoría."""
        # Mapeo de subcategorías a tablas origen
        tabla_mapping = {
            80: 'Libro209_YLVMensual',
            81: 'Libro209_YLVMensual',
            82: 'Libro209_YLVMensual',
            83: 'Libro209_YLVMensual',
            116: 'Libro209_YLVGrupo'
        }
        return tabla_mapping.get(subcategoria_id)
    
    def get_pending_records(self, subcategoria_id, limit=100):
        """
        Obtiene registros pendientes de migración desde SQL Server.
        Usa la tabla de control en PostgreSQL para filtrar ya migrados.
        """
        try:
            # Primero obtener IDs ya migrados desde PostgreSQL
            cursor_pg = self.postgres_conn.cursor()
            query_migrados = """
                SELECT idcontrol_origen 
                FROM libro209_controlmigracion 
                WHERE empresa_id = %s AND subcategoria_id = %s AND estado = 'MIGRADO'
            """
            cursor_pg.execute(query_migrados, (self.empresa_id, subcategoria_id))
            ids_migrados = {row[0] for row in cursor_pg.fetchall()}
            cursor_pg.close()
            
            # Conectar a SQL Server para obtener datos origen
            if not self.sql_server_conn:
                self.connect_sql_server()
            
            cursor = self.sql_server_conn.cursor()
            
            # Obtener nombre de tabla origen según subcategoría
            tabla_origen = self.get_tabla_origen(subcategoria_id)
            if not tabla_origen:
                logger.error(f"No se encontró tabla origen para subcategoría {subcategoria_id}")
                return []
            
            # Obtener registros pendientes
            if ids_migrados:
                placeholders = ','.join(['?' for _ in ids_migrados])
                query_pendientes = f"""
                    SELECT TOP {limit} * 
                    FROM {tabla_origen}
                    WHERE idcontrol NOT IN ({placeholders})
                """
                cursor.execute(query_pendientes, list(ids_migrados))
            else:
                query_pendientes = f"SELECT TOP {limit} * FROM {tabla_origen}"
                cursor.execute(query_pendientes)
            
            # Obtener columnas
            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()
            
            # Convertir a diccionarios
            records = []
            for row in rows:
                record = dict(zip(columns, row))
                records.append(record)
            
            cursor.close()
            logger.info(f"Registros pendientes encontrados: {len(records)}")
            return records
        except Exception as e:
            logger.error(f"Error obteniendo registros pendientes: {e}")
            return []
    
    def transform_record(self, source_record, config_campos, config_cuentas):
        """Transforma un registro origen según configuración."""
        try:
            transformed = {}
            
            # Aplicar mapeo de campos
            for campo in config_campos:
                campo_origen = campo['campo_origen']
                campo_destino = campo['campo_destino']
                tipo_dato = campo['tipo_dato']
                valor_fijo = campo['valor_fijo']
                
                if valor_fijo:
                    # Usar valor fijo
                    transformed[campo_destino] = self.convert_value(valor_fijo, tipo_dato)
                elif campo_origen in source_record:
                    # Usar valor del origen
                    valor_origen = source_record[campo_origen]
                    transformed[campo_destino] = self.convert_value(valor_origen, tipo_dato)
                elif campo['es_requerido']:
                    logger.warning(f"Campo requerido {campo_origen} no encontrado en registro origen")
            
            # Agregar cuentas contables
            transformed['ccodcue_debito'] = config_cuentas.get('DEBITO')
            transformed['ccodcue_credito'] = config_cuentas.get('CREDITO')
            
            return transformed
        except Exception as e:
            logger.error(f"Error transformando registro: {e}")
            return None
    
    def convert_value(self, value, tipo_dato):
        """Convierte un valor al tipo de dato especificado."""
        try:
            if value is None:
                return None
            elif tipo_dato == 'STRING':
                return str(value)
            elif tipo_dato == 'NUMERIC':
                return Decimal(str(value))
            elif tipo_dato == 'DATE':
                if isinstance(value, str):
                    return datetime.strptime(value, '%Y-%m-%d')
                return value
            elif tipo_dato == 'BOOLEAN':
                return bool(value)
            else:
                return str(value)
        except Exception as e:
            logger.warning(f"Error convirtiendo valor {value} a {tipo_dato}: {e}")
            return None
    
    def insert_control_record(self, idcontrol_origen, subcategoria_id, estado='PENDIENTE', error_msg=None):
        """Inserta o actualiza un registro en la tabla de control en PostgreSQL."""
        try:
            cursor = self.postgres_conn.cursor()
            
            # Verificar si ya existe
            query_check = """
                SELECT id FROM libro209_controlmigracion 
                WHERE empresa_id = %s AND subcategoria_id = %s AND idcontrol_origen = %s
            """
            cursor.execute(query_check, (self.empresa_id, subcategoria_id, idcontrol_origen))
            existing = cursor.fetchone()
            
            if existing:
                # Actualizar
                query_update = """
                    UPDATE libro209_controlmigracion 
                    SET estado = %s, error_mensaje = %s, intentos = intentos + 1, fecha_ultimo_intento = CURRENT_TIMESTAMP
                    WHERE id = %s
                """
                cursor.execute(query_update, (estado, error_msg, existing[0]))
            else:
                # Insertar
                query_insert = """
                    INSERT INTO libro209_controlmigracion 
                    (empresa_id, subcategoria_id, idcontrol_origen, estado, error_mensaje, fecha_ultimo_intento)
                    VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                """
                cursor.execute(query_insert, (self.empresa_id, subcategoria_id, idcontrol_origen, estado, error_msg))
            
            self.postgres_conn.commit()
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Error insertando registro de control: {e}")
            self.postgres_conn.rollback()
            return False
    
    def migrate_to_contasis(self, transformed_record, subcategoria_id):
        """Migra un registro transformado a Contasis."""
        try:
            cursor = self.contasis_conn.cursor()
            
            # Generar número de asiento
            nasiento = self.generate_nasiento(cursor, subcategoria_id)
            
            # Insertar cabecera (cf_diario)
            cabecera = {
                'nasiento': nasiento,
                'cper': transformed_record.get('cper', 'GLOBAL'),
                'cmes': transformed_record.get('cmes', '01'),
                'ffechadoc': transformed_record.get('ffechadoc', datetime.now()),
                'ntc': transformed_record.get('ntc', 1.0),
                'ccodmon': transformed_record.get('ccodmon', 'PEN'),
                'cglosa': transformed_record.get('cglosa', 'Migración Libro 209'),
                'ccoddoc': transformed_record.get('ccoddoc', '00'),
                'cserie': transformed_record.get('cserie', ''),
                'cnumero': transformed_record.get('cnumero', ''),
                'ccodruc': transformed_record.get('ccodruc', ''),
                'cdes': transformed_record.get('cdes', ''),
                'ccodori': transformed_record.get('ccodori', '209')
            }
            
            query_cabecera = """
                INSERT INTO cf_diario 
                (nasiento, cper, cmes, ffechadoc, ntc, ccodmon, cglosa, ccoddoc, cserie, cnumero, ccodruc, cdes, ccodori)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query_cabecera, (
                cabecera['nasiento'], cabecera['cper'], cabecera['cmes'], cabecera['ffechadoc'],
                cabecera['ntc'], cabecera['ccodmon'], cabecera['cglosa'], cabecera['ccoddoc'],
                cabecera['cserie'], cabecera['cnumero'], cabecera['ccodruc'], cabecera['cdes'], cabecera['ccodori']
            ))
            
            # Insertar líneas de detalle (cf_diariol)
            # Línea débito
            linea_debito = {
                'nasiento': nasiento,
                'nidlin': 1,
                'ccodcue': transformed_record.get('ccodcue_debito'),
                'ndebe': transformed_record.get('ndebe', 0),
                'nhaber': 0,
                'cglosa': transformed_record.get('cglosa', 'Migración Libro 209'),
                'clecvmes': transformed_record.get('clecvmes', '07'),
                'clecvper': transformed_record.get('clecvper', '07'),
                'cledmcmes': transformed_record.get('cledmcmes', '07'),
                'cledmcper': transformed_record.get('cledmcper', '07'),
                'clecvesta': transformed_record.get('clecvesta', '1'),
                'cledmcesta': transformed_record.get('cledmcesta', '1')
            }
            
            query_detalle = """
                INSERT INTO cf_diariol 
                (nasiento, nidlin, ccodcue, ndebe, nhaber, cglosa, clecvmes, clecvper, cledmcmes, cledmcper, clecvesta, cledmcesta)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query_detalle, (
                linea_debito['nasiento'], linea_debito['nidlin'], linea_debito['ccodcue'],
                linea_debito['ndebe'], linea_debito['nhaber'], linea_debito['cglosa'],
                linea_debito['clecvmes'], linea_debito['clecvper'], linea_debito['cledmcmes'],
                linea_debito['cledmcper'], linea_debito['clecvesta'], linea_debito['cledmcesta']
            ))
            
            # Línea crédito
            linea_credito = {
                'nasiento': nasiento,
                'nidlin': 2,
                'ccodcue': transformed_record.get('ccodcue_credito'),
                'ndebe': 0,
                'nhaber': transformed_record.get('nhaber', 0),
                'cglosa': transformed_record.get('cglosa', 'Migración Libro 209'),
                'clecvmes': transformed_record.get('clecvmes', '07'),
                'clecvper': transformed_record.get('clecvper', '07'),
                'cledmcmes': transformed_record.get('cledmcmes', '07'),
                'cledmcper': transformed_record.get('cledmcper', '07'),
                'clecvesta': transformed_record.get('clecvesta', '1'),
                'cledmcesta': transformed_record.get('cledmcesta', '1')
            }
            
            cursor.execute(query_detalle, (
                linea_credito['nasiento'], linea_credito['nidlin'], linea_credito['ccodcue'],
                linea_credito['ndebe'], linea_credito['nhaber'], linea_credito['cglosa'],
                linea_credito['clecvmes'], linea_credito['clecvper'], linea_credito['cledmcmes'],
                linea_credito['cledmcper'], linea_credito['clecvesta'], linea_credito['cledmcesta']
            ))
            
            self.contasis_conn.commit()
            cursor.close()
            
            return nasiento
        except Exception as e:
            logger.error(f"Error migrando a Contasis: {e}")
            self.contasis_conn.rollback()
            raise
    
    def generate_nasiento(self, cursor, subcategoria_id):
        """Genera un número de asiento único."""
        try:
            # Obtener el último nasiento para el periodo
            query = """
                SELECT COALESCE(MAX(nasiento), 0) + 1 
                FROM cf_diario 
                WHERE cper = 'GLOBAL'
            """
            cursor.execute(query)
            nasiento = cursor.fetchone()[0]
            return nasiento
        except Exception as e:
            logger.error(f"Error generando nasiento: {e}")
            raise
    
    def process_subcategoria(self, subcategoria_id):
        """Procesa una subcategoría completa."""
        try:
            logger.info(f"Procesando subcategoría {subcategoria_id}")
            
            # Obtener configuración
            config_cuentas = self.get_config_cuentas(subcategoria_id)
            config_campos = self.get_config_campos(subcategoria_id)
            
            if not config_cuentas:
                logger.warning(f"No hay configuración de cuentas para subcategoría {subcategoria_id}")
                return
            
            if not config_campos:
                logger.warning(f"No hay configuración de campos para subcategoría {subcategoria_id}")
                return
            
            # Obtener registros pendientes
            records = self.get_pending_records(subcategoria_id)
            
            if not records:
                logger.info(f"No hay registros pendientes para subcategoría {subcategoria_id}")
                return
            
            # Procesar cada registro
            for record in records:
                idcontrol = record.get('idcontrol')
                
                try:
                    # Transformar registro
                    transformed = self.transform_record(record, config_campos, config_cuentas)
                    
                    if not transformed:
                        self.insert_control_record(idcontrol, subcategoria_id, 'ERROR', 'Error en transformación')
                        continue
                    
                    # Migrar a Contasis
                    nasiento = self.migrate_to_contasis(transformed, subcategoria_id)
                    
                    # Actualizar control
                    self.insert_control_record(idcontrol, subcategoria_id, 'MIGRADO')
                    
                    logger.info(f"Registro {idcontrol} migrado exitosamente como asiento {nasiento}")
                    
                except Exception as e:
                    error_msg = str(e)
                    self.insert_control_record(idcontrol, subcategoria_id, 'ERROR', error_msg)
                    logger.error(f"Error migrando registro {idcontrol}: {error_msg}")
            
        except Exception as e:
            logger.error(f"Error procesando subcategoría {subcategoria_id}: {e}")
    
    def run(self):
        """Ejecuta el proceso completo de migración."""
        logger.info(f"Iniciando migración para codcia {self.codcia}")
        
        # Conectar a bases de datos
        if not self.connect_postgres():
            return False
        if not self.connect_contasis():
            return False
        
        try:
            # Obtener subcategorías
            subcategorias = self.get_subcategorias()
            
            if not subcategorias:
                logger.warning("No se encontraron subcategorías configuradas")
                return False
            
            # Procesar cada subcategoría
            for subcategoria_id in subcategorias:
                self.process_subcategoria(subcategoria_id)
            
            logger.info("Migración completada exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"Error en proceso de migración: {e}")
            return False
        finally:
            self.close_connections()


def main():
    """Función principal para ejecución como script."""
    # Configuración de PostgreSQL (MigConta)
    postgres_config = {
        'host': os.getenv('POSTGRES_HOST', 'host.docker.internal'),
        'port': int(os.getenv('POSTGRES_PORT', '5432')),
        'database': os.getenv('POSTGRES_DATABASE', 'migconta_db'),
        'username': os.getenv('POSTGRES_USER', 'postgres'),
        'password': os.getenv('POSTGRES_PASSWORD', 'postgres')
    }
    
    # Configuración de SQL Server
    sql_server_config = {
        'driver': 'ODBC Driver 17 for SQL Server',
        'server': os.getenv('SQL_SERVER_HOST', 'localhost'),
        'database': os.getenv('SQL_SERVER_DATABASE', 'YLV'),
        'username': os.getenv('SQL_SERVER_USER', 'sa'),
        'password': os.getenv('SQL_SERVER_PASSWORD', 'password')
    }
    
    # Código de empresa en SQL Server
    codcia = os.getenv('CODCIA', '05')
    
    # Crear migrador y ejecutar
    migrator = Libro209MigratorStandalone(codcia, postgres_config, sql_server_config)
    success = migrator.run()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
