#!/usr/bin/env python3
"""
Script de migración independiente para el Libro 209.
Lee configuración desde archivo JSON, extrae de SQL Server, e inyecta a Contasis.
Sin dependencias del sistema MigConta.
Diseñado para ejecución como cron job.
"""

import sys
import os
import logging
from datetime import datetime
from decimal import Decimal
import pyodbc
import psycopg2
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

class Libro209MigratorJSON:
    def __init__(self, config_file, codcia, sql_server_config):
        """
        Inicializa el migrador del Libro 209.
        
        Args:
            config_file: Ruta al archivo JSON de configuración
            codcia: Código de empresa en SQL Server
            sql_server_config: Dict con configuración de SQL Server
        """
        self.config_file = config_file
        self.codcia = codcia
        self.sql_server_config = sql_server_config
        self.contasis_config = None
        self.empresa_id = None
        self.config_data = None
        self.sql_server_conn = None
        self.contasis_conn = None
        self.current_nasiento = None
        
    def load_config(self):
        """Carga configuración desde archivo JSON."""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config_data = json.load(f)
            
            # Buscar empresa por codcia
            for empresa in self.config_data['empresas']:
                if empresa['codcia'] == self.codcia:
                    self.empresa_id = empresa['empresa_id']
                    self.contasis_config = empresa['contasis']
                    logger.info(f"Configuración cargada para empresa {empresa['nombre']} (codcia: {self.codcia})")
                    return True
            
            logger.error(f"No se encontró configuración para codcia: {self.codcia}")
            return False
        except Exception as e:
            logger.error(f"Error cargando configuración: {e}")
            return False
    
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
        if self.sql_server_conn:
            self.sql_server_conn.close()
        if self.contasis_conn:
            self.contasis_conn.close()
        logger.info("Conexiones cerradas")
    
    def get_empresa_config(self):
        """Obtiene la configuración de la empresa actual."""
        for empresa in self.config_data['empresas']:
            if empresa['codcia'] == self.codcia:
                return empresa
        return None
    
    def get_subcategorias(self):
        """Obtiene las subcategorías del libro 209 para la empresa."""
        empresa = self.get_empresa_config()
        if empresa:
            return [sub['id'] for sub in empresa['subcategorias']]
        return []
    
    def get_subcategoria_config(self, subcategoria_id):
        """Obtiene configuración de una subcategoría específica."""
        empresa = self.get_empresa_config()
        if empresa:
            for sub in empresa['subcategorias']:
                if sub['id'] == subcategoria_id:
                    return sub
        return None
    
    def connect_sql_server(self):
        """Conecta a SQL Server para datos origen."""
        try:
            conn_str = (
                f"DRIVER={self.sql_server_config['driver']};"
                f"SERVER={self.sql_server_config['server']};"
                f"DATABASE={self.sql_server_config['database']};"
                f"UID={self.sql_server_config['username']};"
                f"PWD={self.sql_server_config['password']};"
                f"Timeout=10"
            )
            logger.info(f"Intentando conectar a SQL Server: {self.sql_server_config['server']}")
            self.sql_server_conn = pyodbc.connect(conn_str)
            logger.info(f"Conectado a SQL Server: {self.sql_server_config['server']}")
            return True
        except Exception as e:
            logger.error(f"Error conectando a SQL Server: {e}")
            return False
    
    def get_pending_records(self, subcategoria_id, limit=10):
        """
        Obtiene cabeceras pendientes de migración desde SQL Server.
        Excluye cabeceras que ya fueron migradas exitosamente según tabla de control.
        """
        try:
            # Conectar a SQL Server para obtener datos origen
            if not self.sql_server_conn:
                self.connect_sql_server()
            
            cursor = self.sql_server_conn.cursor()
            
            # Obtener configuración de subcategoría
            sub_config = self.get_subcategoria_config(subcategoria_id)
            if not sub_config:
                logger.error(f"No se encontró configuración para subcategoría {subcategoria_id}")
                return []
            
            tabla_origen = sub_config['tabla_origen']
            
            # Obtener cabeceras pendientes (no migradas exitosamente)
            query_pendientes = f"""
                SELECT TOP {limit} c.*
                FROM {tabla_origen} c
                WHERE c.Id NOT IN (
                    SELECT idcontrol_origen 
                    FROM Libro209_ControlMigracion 
                    WHERE subcategoria_id = {subcategoria_id} 
                    AND estado = 'MIGRADO'
                )
            """
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
            logger.info(f"Cabeceras pendientes de migración: {len(records)}")
            return records
        except Exception as e:
            logger.error(f"Error obteniendo registros: {e}")
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
            
            # Extraer cserie y cnumero de NroPlanilla (ahora viene de la cabecera)
            if 'NroPlanilla' in source_record and source_record['NroPlanilla']:
                nro_planilla = str(source_record['NroPlanilla'])
                # cserie: 17 ceros + primeros 3 caracteres (total 20 caracteres)
                serie = nro_planilla[:3] if len(nro_planilla) >= 3 else nro_planilla
                transformed['cserie'] = '00000000000000000' + serie
                
                # cnumero: 10 ceros + año-numero (formato: 000000000002026-0027)
                # NroPlanilla formato: PGM-71941916-2026-0001
                parts = nro_planilla.split('-')
                if len(parts) >= 3:
                    year = parts[2]  # 2026
                    num = parts[3] if len(parts) >= 4 else '0000'  # 0001
                    # Asegurar que el número tenga 4 dígitos
                    num = num.zfill(4)
                    transformed['cnumero'] = '0000000000' + year + '-' + num
                else:
                    transformed['cnumero'] = '000000000002026-0000'
                
                # glosa: NroPlanilla completo + ": " + motivo (usar TotalGastado como referencia)
                # Truncar a 80 caracteres para evitar error en cf_diario.cglosa_2
                glosa_completa = f"{nro_planilla}: GASTOS DE PLANILLA DE MOVILIDAD"
                transformed['cglosa_2'] = glosa_completa[:80] if len(glosa_completa) > 80 else glosa_completa
            else:
                # Valores por defecto si no hay NroPlanilla
                transformed['cserie'] = '00000000000000000PGM'
                transformed['cnumero'] = '00000000002026-0000'
                transformed['cglosa_2'] = 'PGM-00000000-0000-0000: GASTOS DE PLANILLA DE MOVILIDAD'
            
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
    
    def get_planilla_detalles(self, planilla_id):
        """Obtiene los detalles de una planilla específica."""
        try:
            if not self.sql_server_conn:
                self.connect_sql_server()
            
            cursor = self.sql_server_conn.cursor()
            
            query = """
                SELECT Id, Fecha, Motivo, Desde, Hasta, Monto
                FROM FinPlanillaMovilidadDet
                WHERE PlanillaId = ?
                ORDER BY Id
            """
            cursor.execute(query, (planilla_id,))
            
            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()
            
            detalles = []
            for row in rows:
                detalle = dict(zip(columns, row))
                detalles.append(detalle)
            
            cursor.close()
            return detalles
        except Exception as e:
            logger.error(f"Error obteniendo detalles de planilla {planilla_id}: {e}")
            return []
    
    def migrate_to_contasis(self, transformed_record, subcategoria_id, planilla_id):
        """Migra una planilla completa con sus detalles a Contasis."""
        try:
            if not self.contasis_conn:
                self.connect_contasis()
            
            cursor = self.contasis_conn.cursor()
            
            # Generar nasiento único
            nasiento = self.generate_nasiento(cursor, subcategoria_id)
            
            # Preparar cabecera del asiento (cf_diario)
            cabecera = {
                'nasiento': nasiento,
                'cper': transformed_record.get('cper', '2026'),
                'cmes': transformed_record.get('cmes', '01'),
                'ccodori': transformed_record.get('ccodori', '209'),
                'cmoneda': transformed_record.get('cmoneda', 'PEN'),
                'cglosa_2': transformed_record.get('cglosa_2', 'Migración Libro 209'),
                'ccodusu': '1',
                'ccodsu': '1',
                'ntcblo': 1.0,
                'ccodbas': '1',
                'nidreg': 1,
                'nidlin': 1,
                'chknotc': 0
            }
            
            query_cabecera = """
                INSERT INTO cf_diario 
                (nasiento, cper, cmes, ccodori, cmoneda, cglosa_2, ccodusu, ccodsu, ntcblo, ccodbas, nidreg, nidlin, chknotc)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query_cabecera, (
                cabecera['nasiento'], cabecera['cper'], cabecera['cmes'], cabecera['ccodori'],
                cabecera['cmoneda'], cabecera['cglosa_2'], cabecera['ccodusu'],
                cabecera['ccodsu'], cabecera['ntcblo'], cabecera['ccodbas'], cabecera['nidreg'],
                cabecera['nidlin'], cabecera['chknotc']
            ))
            
            # Obtener detalles de la planilla
            detalles = self.get_planilla_detalles(planilla_id)
            
            if not detalles:
                logger.warning(f"No se encontraron detalles para planilla {planilla_id}")
                # Usar el total de la cabecera como fallback
                total_debito = transformed_record.get('ndebe', 0)
                total_credito = transformed_record.get('nhaber', 0)
                
                # Insertar líneas de detalle simples
                self._insert_detalle_line(cursor, nasiento, 1, transformed_record.get('ccodcue_debito'), total_debito, 0, transformed_record)
                self._insert_detalle_line(cursor, nasiento, 2, transformed_record.get('ccodcue_credito'), 0, total_credito, transformed_record)
            else:
                # Insertar líneas de detalle por cada detalle de la planilla
                nidlin = 1
                total_debito = 0
                total_credito = 0
                
                for detalle in detalles:
                    monto = detalle.get('Monto', 0)
                    motivo = detalle.get('Motivo', 'GASTOS DE PLANILLA DE MOVILIDAD')
                    
                    # Línea débito para este detalle
                    glosa_detalle = f"{transformed_record.get('cglosa_2', '')}: {motivo}"
                    self._insert_detalle_line(cursor, nasiento, nidlin, transformed_record.get('ccodcue_debito'), monto, 0, transformed_record, glosa_detalle)
                    total_debito += monto
                    nidlin += 1
                    
                    # Línea crédito para este detalle
                    self._insert_detalle_line(cursor, nasiento, nidlin, transformed_record.get('ccodcue_credito'), 0, monto, transformed_record, glosa_detalle)
                    total_credito += monto
                    nidlin += 1
                
                logger.info(f"Insertadas {len(detalles)} detalles (total {nidlin-1} líneas) para asiento {nasiento}")
            
            self.contasis_conn.commit()
            cursor.close()
            
            return nasiento
        except Exception as e:
            logger.error(f"Error migrando a Contasis: {e}")
            self.contasis_conn.rollback()
            raise
    
    def _insert_detalle_line(self, cursor, nasiento, nidlin, ccodcue, ndebe, nhaber, transformed_record, cglosa=None):
        """Inserta una línea de detalle en cf_diariol."""
        if cglosa is None:
            cglosa = transformed_record.get('cglosa_2', 'Migración Libro 209')
        
        query_detalle = """
            INSERT INTO cf_diariol 
            (nasiento, nidlin, ccodcue, ndebe, nhaber, cglosa, cper, cmes, ccodori, ntc, ccodsu, ccodmon, cserie, cnumero)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query_detalle, (
            nasiento, nidlin, ccodcue, ndebe, nhaber, cglosa,
            transformed_record.get('cper', '2026'), transformed_record.get('cmes', '01'),
            transformed_record.get('ccodori', '209'), 1.0, '1', '1',
            transformed_record.get('cserie', 'PGM'), transformed_record.get('cnumero', 'PGM-00000000-0000-0000')
        ))
    
    def register_migration_attempt(self, subcategoria_id, idcontrol_origen):
        """Registra un intento de migración en la tabla de control."""
        try:
            if not self.sql_server_conn:
                self.connect_sql_server()
            
            cursor = self.sql_server_conn.cursor()
            
            # Verificar si ya existe un registro para este idcontrol_origen
            query_check = """
                SELECT id, intentos FROM Libro209_ControlMigracion 
                WHERE subcategoria_id = ? AND idcontrol_origen = ?
            """
            cursor.execute(query_check, (subcategoria_id, str(idcontrol_origen)))
            existing = cursor.fetchone()
            
            if existing:
                # Actualizar registro existente
                query_update = """
                    UPDATE Libro209_ControlMigracion 
                    SET intentos = intentos + 1,
                        fecha_ultimo_intento = GETDATE(),
                        estado = 'EN_PROCESO'
                    WHERE id = ?
                """
                cursor.execute(query_update, (existing[0],))
                logger.info(f"Actualizando registro de control ID {existing[0]}")
            else:
                # Insertar nuevo registro
                query_insert = """
                    INSERT INTO Libro209_ControlMigracion 
                    (empresa_id, subcategoria_id, idcontrol_origen, fecha_registro, estado, intentos, fecha_ultimo_intento)
                    VALUES (?, ?, ?, GETDATE(), 'EN_PROCESO', 1, GETDATE())
                """
                cursor.execute(query_insert, (self.empresa_id, subcategoria_id, str(idcontrol_origen)))
                logger.info(f"Insertando nuevo registro de control para idcontrol_origen {idcontrol_origen}")
            
            self.sql_server_conn.commit()
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Error registrando intento de migración: {e}")
            return False
    
    def update_migration_success(self, subcategoria_id, idcontrol_origen, asiento_generado):
        """Actualiza el registro de control como migrado exitosamente."""
        try:
            if not self.sql_server_conn:
                self.connect_sql_server()
            
            cursor = self.sql_server_conn.cursor()
            
            query_update = """
                UPDATE Libro209_ControlMigracion 
                SET estado = 'MIGRADO',
                    fecha_migracion = GETDATE(),
                    asiento_generado = ?,
                    error_mensaje = NULL
                WHERE subcategoria_id = ? AND idcontrol_origen = ?
            """
            cursor.execute(query_update, (str(asiento_generado), subcategoria_id, str(idcontrol_origen)))
            
            self.sql_server_conn.commit()
            cursor.close()
            logger.info(f"Registro de control actualizado como MIGRADO para asiento {asiento_generado}")
            return True
        except Exception as e:
            logger.error(f"Error actualizando registro de control como MIGRADO: {e}")
            return False
    
    def update_migration_error(self, subcategoria_id, idcontrol_origen, error_mensaje):
        """Actualiza el registro de control con error."""
        try:
            if not self.sql_server_conn:
                self.connect_sql_server()
            
            cursor = self.sql_server_conn.cursor()
            
            query_update = """
                UPDATE Libro209_ControlMigracion 
                SET estado = 'ERROR',
                    error_mensaje = ?,
                    fecha_ultimo_intento = GETDATE()
                WHERE subcategoria_id = ? AND idcontrol_origen = ?
            """
            cursor.execute(query_update, (str(error_mensaje)[:500], subcategoria_id, str(idcontrol_origen)))
            
            self.sql_server_conn.commit()
            cursor.close()
            logger.info(f"Registro de control actualizado como ERROR: {error_mensaje}")
            return True
        except Exception as e:
            logger.error(f"Error actualizando registro de control como ERROR: {e}")
            return False
    
    def generate_nasiento(self, cursor, subcategoria_id):
        """Genera un número de asiento único para la subcategoría."""
        try:
            # Usar el contador actual y luego incrementarlo
            if self.current_nasiento is None:
                # Fallback si no se inicializó el contador
                query = "SELECT COALESCE(MAX(nasiento), 0) + 1 FROM cf_diario WHERE cper = '2026' AND cmes = '01' AND ccodori = '209'"
                cursor.execute(query)
                result = cursor.fetchone()
                self.current_nasiento = result[0] if result else 1
            
            nasiento = self.current_nasiento
            self.current_nasiento += 1
            logger.info(f"Generando nasiento: {nasiento}")
            return nasiento
        except Exception as e:
            logger.error(f"Error generando nasiento: {e}")
            return 1   
    def process_subcategoria(self, subcategoria_id):
        """Procesa una subcategoría completa."""
        try:
            logger.info(f"Procesando subcategoría {subcategoria_id}")
            
            # Obtener configuración de subcategoría
            sub_config = self.get_subcategoria_config(subcategoria_id)
            if not sub_config:
                logger.warning(f"No hay configuración para subcategoría {subcategoria_id}")
                return
            
            # Obtener el siguiente nasiento al inicio
            if not self.contasis_conn:
                self.connect_contasis()
            
            cursor = self.contasis_conn.cursor()
            query = "SELECT COALESCE(MAX(nasiento), 0) + 1 FROM cf_diario WHERE cper = '2026' AND cmes = '01' AND ccodori = '209'"
            cursor.execute(query)
            result = cursor.fetchone()
            self.current_nasiento = result[0] if result else 1
            logger.info(f"Primer nasiento para este lote: {self.current_nasiento}")
            cursor.close()
            
            config_cuentas = sub_config['cuentas']
            config_campos = sub_config['campos']
            
            # Obtener registros
            records = self.get_pending_records(subcategoria_id)
            
            if not records:
                logger.info(f"No hay registros para subcategoría {subcategoria_id}")
                return
            
            # Procesar cada registro
            for record in records:
                idcontrol = record.get('Id')  # Usar 'Id' en lugar de 'idcontrol' según esquema SQL Server
                
                try:
                    # Registrar intento de migración
                    self.register_migration_attempt(subcategoria_id, idcontrol)
                    
                    # Transformar registro
                    transformed = self.transform_record(record, config_campos, config_cuentas)
                    
                    if not transformed:
                        logger.warning(f"Error transformando registro {idcontrol}")
                        self.update_migration_error(subcategoria_id, idcontrol, "Error en transformación")
                        continue
                    
                    # Migrar a Contasis
                    nasiento = self.migrate_to_contasis(transformed, subcategoria_id, idcontrol)
                    
                    # Actualizar registro de control como exitoso
                    self.update_migration_success(subcategoria_id, idcontrol, nasiento)
                    
                    logger.info(f"Registro {idcontrol} migrado exitosamente como asiento {nasiento}")
                    
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"Error migrando registro {idcontrol}: {error_msg}")
                    self.update_migration_error(subcategoria_id, idcontrol, error_msg)
            
        except Exception as e:
            logger.error(f"Error procesando subcategoría {subcategoria_id}: {e}")
    
    def run(self):
        """Ejecuta el proceso completo de migración."""
        logger.info(f"Iniciando migración para codcia {self.codcia}")
        
        # Cargar configuración
        if not self.load_config():
            return False
        
        # Conectar a SQL Server primero
        if not self.connect_sql_server():
            return False
        
        # Conectar a Contasis
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


def load_env_file(env_file):
    """Carga variables de entorno desde archivo."""
    env_vars = {}
    try:
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    # Remover 'export' si existe
                    line = line.replace('export ', '')
                    key, value = line.split('=', 1)
                    # Remover comillas si existen
                    value = value.strip('"').strip("'")
                    env_vars[key.strip()] = value
        return env_vars
    except Exception as e:
        print(f"Error cargando archivo .env: {e}")
        return {}

def main():
    """Función principal para ejecución como script."""
    # Cargar variables de entorno desde archivo
    env_file = '/app/MCon/209/libro209_config.env'
    env_vars = load_env_file(env_file)
    
    # Configuración de SQL Server
    sql_server_config = {
        'driver': 'ODBC Driver 17 for SQL Server',
        'server': os.getenv('SQL_SERVER_HOST', '192.168.1.17'),
        'database': os.getenv('SQL_SERVER_DATABASE', 'YELAVE22'),
        'username': os.getenv('SQL_SERVER_USER', 'sa'),
        'password': os.getenv('SQL_SERVER_PASSWORD', 'Pa$$word')
    }
    
    # Ruta al archivo de configuración JSON
    config_file = env_vars.get('CONFIG_FILE', '/app/MCon/209/libro209_config.json')
    
    # Código de empresa en SQL Server
    codcia = env_vars.get('CODCIA', '05')
    
    # Crear migrador y ejecutar
    migrator = Libro209MigratorJSON(config_file, codcia, sql_server_config)
    success = migrator.run()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
