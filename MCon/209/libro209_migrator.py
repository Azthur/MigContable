#!/usr/bin/env python3
"""
Script específico para migración del Libro 209.
Lee configuración desde PostgreSQL (MigConta), controla migración, e inyecta a Contasis.
Diseñado para ejecución como cron job.
"""

import sys
import os
sys.path.insert(0, '/app')

import logging
logging.disable(logging.CRITICAL)

from datetime import datetime
from decimal import Decimal
import pyodbc
import psycopg2
from psycopg2 import sql, extras
import json
from backend.app.core.database import get_dest_db
from sqlalchemy import text

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

class Libro209Migrator:
    def __init__(self, codcia, sql_server_config):
        """
        Inicializa el migrador del Libro 209.
        
        Args:
            codcia: Código de empresa en SQL Server
            sql_server_config: Dict con configuración de SQL Server
        """
        self.codcia = codcia
        self.sql_server_config = sql_server_config
        self.contasis_config = None
        self.empresa_id = None
        self.postgres_db = None
        self.sql_server_conn = None
        self.contasis_conn = None
        
    def connect_postgres(self):
        """Conecta a PostgreSQL (MigConta) usando la conexión existente de la aplicación."""
        try:
            self.postgres_db = next(get_dest_db())
            logger.info("Conectado a PostgreSQL (MigConta) usando conexión de aplicación")
            
            # Cargar configuración de Contasis desde PostgreSQL
            self.load_contasis_config()
            
            return True
        except Exception as e:
            logger.error(f"Error conectando a PostgreSQL: {e}")
            return False
    
    def load_contasis_config(self):
        """Carga configuración de Contasis desde tabla libro209_empresacontasis."""
        try:
            result = self.postgres_db.execute(text("""
                SELECT empresa_id, contasis_host, contasis_port, contasis_database, contasis_username, contasis_password
                FROM libro209_empresacontasis
                WHERE codcia = :codcia AND activo = true
            """), {"codcia": self.codcia}).fetchone()
            
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
        except Exception as e:
            logger.error(f"Error cargando configuración de Contasis: {e}")
            raise
    
    def connect_contasis(self):
        """Conecta a Contasis (PostgreSQL)."""
        try:
            self.contasis_conn = psycopg2.connect(
                host=self.contasis_config['host'],
                port=self.contasis_config['port'],
                database=self.contasis_config['database'],
                user=self.contasis_config['username'],
                password=self.contasis_config['password']
            )
            logger.info(f"Conectado a Contasis: {self.contasis_config['host']}")
            return True
        except Exception as e:
            logger.error(f"Error conectando a Contasis: {e}")
            return False
    
    def close_connections(self):
        """Cierra todas las conexiones."""
        if self.postgres_db:
            self.postgres_db.close()
        if self.sql_server_conn:
            self.sql_server_conn.close()
        if self.contasis_conn:
            self.contasis_conn.close()
        logger.info("Conexiones cerradas")
    
    def get_subcategorias(self):
        """Obtiene las subcategorías del libro 209 para la empresa."""
        try:
            result = self.postgres_db.execute(text("""
                SELECT DISTINCT subcategoria_id 
                FROM libro209_configcuentas 
                WHERE empresa_id = :empresa_id AND activo = true
            """), {"empresa_id": self.empresa_id})
            subcategorias = [row[0] for row in result.fetchall()]
            logger.info(f"Subcategorías encontradas: {subcategorias}")
            return subcategorias
        except Exception as e:
            logger.error(f"Error obteniendo subcategorías: {e}")
            return []
    
    def get_config_cuentas(self, subcategoria_id):
        """Obtiene configuración de cuentas para una subcategoría."""
        try:
            result = self.postgres_db.execute(text("""
                SELECT tipo_linea, cuenta_contable 
                FROM libro209_configcuentas 
                WHERE empresa_id = :empresa_id AND subcategoria_id = :subcategoria_id AND activo = true
                ORDER BY orden
            """), {"empresa_id": self.empresa_id, "subcategoria_id": subcategoria_id})
            cuentas = {row[0]: row[1] for row in result.fetchall()}
            return cuentas
        except Exception as e:
            logger.error(f"Error obteniendo configuración de cuentas: {e}")
            return {}
    
    def get_config_campos(self, subcategoria_id):
        """Obtiene configuración de campos para una subcategoría."""
        try:
            result = self.postgres_db.execute(text("""
                SELECT campo_origen, campo_destino, tipo_dato, valor_fijo, formula_transformacion, es_requerido, orden
                FROM libro209_configcampos 
                WHERE empresa_id = :empresa_id AND subcategoria_id = :subcategoria_id AND activo = true
                ORDER BY orden
            """), {"empresa_id": self.empresa_id, "subcategoria_id": subcategoria_id})
            campos = []
            for row in result.fetchall():
                campos.append({
                    'campo_origen': row[0],
                    'campo_destino': row[1],
                    'tipo_dato': row[2],
                    'valor_fijo': row[3],
                    'formula_transformacion': row[4],
                    'es_requerido': row[5],
                    'orden': row[6]
                })
            return campos
        except Exception as e:
            logger.error(f"Error obteniendo configuración de campos: {e}")
            return []
    
    def get_pending_records(self, subcategoria_id, limit=100):
        """
        Obtiene registros pendientes de migración desde SQL Server.
        Usa la tabla de control en PostgreSQL para filtrar ya migrados.
        """
        try:
            # Primero obtener IDs ya migrados desde PostgreSQL
            result = self.postgres_db.execute(text("""
                SELECT idcontrol_origen 
                FROM libro209_controlmigracion 
                WHERE empresa_id = :empresa_id AND subcategoria_id = :subcategoria_id AND estado = 'MIGRADO'
            """), {"empresa_id": self.empresa_id, "subcategoria_id": subcategoria_id})
            ids_migrados = {row[0] for row in result.fetchall()}
            
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
    
    def transform_record(self, record, config_campos, config_cuentas):
        """Transforma un registro origen al formato destino de Contasis."""
        transformed = {}
        
        # Aplicar mapeo de campos
        for campo_config in config_campos:
            campo_origen = campo_config['campo_origen']
            campo_destino = campo_config['campo_destino']
            tipo_dato = campo_config['tipo_dato']
            valor_fijo = campo_config['valor_fijo']
            
            if valor_fijo:
                # Usar valor fijo
                transformed[campo_destino] = self.convert_value(valor_fijo, tipo_dato)
            elif campo_origen in record:
                # Usar valor del registro origen
                valor_origen = record[campo_origen]
                transformed[campo_destino] = self.convert_value(valor_origen, tipo_dato)
            elif campo_config['es_requerido']:
                logger.warning(f"Campo requerido {campo_origen} no encontrado en registro")
        
        # Agregar cuentas contables
        if 'DEBITO' in config_cuentas:
            transformed['ccodcue_debito'] = config_cuentas['DEBITO']
        if 'CREDITO' in config_cuentas:
            transformed['ccodcue_credito'] = config_cuentas['CREDITO']
        
        # Calcular campos derivados
        if 'cper' in transformed and 'cmes' in transformed:
            # clecvper y cledmcper deben ser iguales a cper
            transformed['clecvper'] = transformed['cper']
            transformed['cledmcper'] = transformed['cper']
        
        return transformed
    
    def convert_value(self, value, tipo_dato):
        """Convierte un valor al tipo de dato especificado."""
        if value is None:
            return None
        
        try:
            if tipo_dato == 'STRING':
                return str(value).strip()
            elif tipo_dato == 'NUMERIC':
                return float(value) if value else 0.0
            elif tipo_dato == 'DATE':
                if isinstance(value, datetime):
                    return value
                return datetime.strptime(str(value), '%Y-%m-%d')
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
            # Verificar si ya existe
            result = self.postgres_db.execute(text("""
                SELECT id FROM libro209_controlmigracion 
                WHERE empresa_id = :empresa_id AND subcategoria_id = :subcategoria_id AND idcontrol_origen = :idcontrol_origen
            """), {"empresa_id": self.empresa_id, "subcategoria_id": subcategoria_id, "idcontrol_origen": idcontrol_origen})
            existing = result.fetchone()
            
            if existing:
                # Actualizar
                self.postgres_db.execute(text("""
                    UPDATE libro209_controlmigracion 
                    SET estado = :estado, error_mensaje = :error_msg, intentos = intentos + 1, fecha_ultimo_intento = CURRENT_TIMESTAMP
                    WHERE id = :id
                """), {"estado": estado, "error_msg": error_msg, "id": existing[0]})
            else:
                # Insertar
                self.postgres_db.execute(text("""
                    INSERT INTO libro209_controlmigracion 
                    (empresa_id, subcategoria_id, idcontrol_origen, estado, error_mensaje, fecha_ultimo_intento)
                    VALUES (:empresa_id, :subcategoria_id, :idcontrol_origen, :estado, :error_msg, CURRENT_TIMESTAMP)
                """), {"empresa_id": self.empresa_id, "subcategoria_id": subcategoria_id, "idcontrol_origen": idcontrol_origen, "estado": estado, "error_msg": error_msg})
            
            self.postgres_db.commit()
            return True
        except Exception as e:
            logger.error(f"Error insertando registro de control: {e}")
            self.postgres_db.rollback()
            return False
    
    def migrate_to_contasis(self, transformed_record, subcategoria_id):
        """Migra un registro transformado a Contasis."""
        try:
            cursor = self.contasis_conn.cursor()
            
            # Generar número de asiento
            nasiento = self.generate_nasiento(cursor, subcategoria_id)
            
            # Insertar cabecera (cf_diario)
            cabecera = {
                'cper': transformed_record.get('cper'),
                'cmes': transformed_record.get('cmes'),
                'nasiento': nasiento,
                'cglosa': transformed_record.get('cglosa', 'Libro 209'),
                'ccodori': transformed_record.get('ccodori', '209'),
                'estado': '1'
            }
            
            self.insert_cf_diario(cursor, cabecera)
            
            # Insertar líneas de detalle (cf_diariol)
            # Línea de débito
            linea_debito = transformed_record.copy()
            linea_debito['nasiento'] = nasiento
            linea_debito['nidlin'] = 1
            linea_debito['ccodcue'] = transformed_record.get('ccodcue_debito')
            linea_debito['ndebe'] = transformed_record.get('ndebe', 0)
            linea_debito['nhaber'] = 0
            self.insert_cf_diariol(cursor, linea_debito)
            
            # Línea de crédito
            linea_credito = transformed_record.copy()
            linea_credito['nasiento'] = nasiento
            linea_credito['nidlin'] = 2
            linea_credito['ccodcue'] = transformed_record.get('ccodcue_credito')
            linea_credito['ndebe'] = 0
            linea_credito['nhaber'] = transformed_record.get('nhaber', 0)
            self.insert_cf_diariol(cursor, linea_credito)
            
            self.contasis_conn.commit()
            cursor.close()
            
            return nasiento
        except Exception as e:
            logger.error(f"Error migrando a Contasis: {e}")
            self.contasis_conn.rollback()
            raise
    
    def generate_nasiento(self, cursor, subcategoria_id):
        """Genera el siguiente número de asiento."""
        try:
            query = """
                SELECT COALESCE(MAX(nasiento), 0) + 1 
                FROM cf_diariol 
                WHERE cper = %s AND cmes = %s
            """
            cursor.execute(query, ('2026', '07'))
            result = cursor.fetchone()
            return result[0] if result else 1
        except Exception as e:
            logger.error(f"Error generando nasiento: {e}")
            return 1
    
    def insert_cf_diario(self, cursor, cabecera):
        """Inserta registro en cf_diario."""
        query = """
            INSERT INTO cf_diario (cper, cmes, nasiento, cglosa, ccodori, estado)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            cabecera['cper'],
            cabecera['cmes'],
            cabecera['nasiento'],
            cabecera['cglosa'],
            cabecera['ccodori'],
            cabecera['estado']
        ))
    
    def insert_cf_diariol(self, cursor, linea):
        """Inserta registro en cf_diariol."""
        # Construir query dinámico basado en campos disponibles
        campos = ['cper', 'cmes', 'nasiento', 'nidlin', 'ccodcue', 'ndebe', 'nhaber']
        valores = []
        
        for campo in campos:
            if campo in linea:
                valores.append(linea[campo])
            else:
                valores.append(None)
        
        query = f"""
            INSERT INTO cf_diariol (cper, cmes, nasiento, nidlin, ccodcue, ndebe, nhaber)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, valores)
    
    def process_subcategoria(self, subcategoria_id):
        """Procesa una subcategoría completa."""
        logger.info(f"Procesando subcategoría {subcategoria_id}")
        
        # Obtener configuración
        config_cuentas = self.get_config_cuentas(subcategoria_id)
        config_campos = self.get_config_campos(subcategoria_id)
        
        if not config_cuentas or not config_campos:
            logger.error(f"Configuración incompleta para subcategoría {subcategoria_id}")
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
                
                # Migrar a Contasis
                nasiento = self.migrate_to_contasis(transformed, subcategoria_id)
                
                # Actualizar control
                self.insert_control_record(idcontrol, subcategoria_id, 'MIGRADO', asiento_generado=str(nasiento))
                
                logger.info(f"Registro {idcontrol} migrado exitosamente como asiento {nasiento}")
                
            except Exception as e:
                error_msg = str(e)
                self.insert_control_record(idcontrol, subcategoria_id, 'ERROR', error_msg)
                logger.error(f"Error migrando registro {idcontrol}: {error_msg}")
    
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
    # Configuración de SQL Server (debe venir de variables de entorno o archivo de config)
    sql_server_config = {
        'driver': 'ODBC Driver 17 for SQL Server',
        'server': os.getenv('SQL_SERVER_HOST', 'localhost'),
        'database': os.getenv('SQL_SERVER_DATABASE', 'YLV'),
        'username': os.getenv('SQL_SERVER_USER', 'sa'),
        'password': os.getenv('SQL_SERVER_PASSWORD', 'password')
    }
    
    # Código de empresa en SQL Server (debe venir de parámetro o variable de entorno)
    codcia = os.getenv('CODCIA', '05')
    
    # Crear migrador y ejecutar
    migrator = Libro209Migrator(codcia, sql_server_config)
    success = migrator.run()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
