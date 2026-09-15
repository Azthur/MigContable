#!/usr/bin/env python3
"""
Script de migración para el Subdiario 209.
Lee configuración desde archivo JSON simplificado, extrae de SQL Server, e inyecta a Contasis.
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
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class Subdiario209Migrator:
    def __init__(self, config_file):
        """Inicializa el migrador del Subdiario 209."""
        self.config_file = config_file
        self.config_data = None
        self.sql_server_conn = None
        self.contasis_conn = None
        self.current_nasiento = None
        self.control_table = None
        
    def load_config(self):
        """Carga configuración desde archivo JSON."""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config_data = json.load(f)
            self.control_table = self.config_data.get('control', {}).get('tabla', 'Subdiario209_ControlMigracion')
            logger.info("Configuración cargada exitosamente")
            return True
        except Exception as e:
            logger.error(f"Error cargando configuración: {e}")
            return False
    
    def connect_sql_server(self):
        """Conecta a SQL Server."""
        try:
            sql_config = self.config_data['sql_server']
            logger.info(f"Conectando a SQL Server: {sql_config['server']}")
            conn_str = (
                f"DRIVER=ODBC Driver 18 for SQL Server;"
                f"SERVER={sql_config['server']},1433;"
                f"DATABASE={sql_config['database']};"
                f"UID={sql_config['uid']};"
                f"PWD={sql_config['pwd']};"
                f"TrustServerCertificate=yes;"
                f"Timeout=30"
            )
            self.sql_server_conn = pyodbc.connect(conn_str)
            logger.info(f"Conectado a SQL Server: {sql_config['server']}")
            return True
        except Exception as e:
            logger.error(f"Error conectando a SQL Server: {e}")
            return False
    
    def connect_contasis(self, codcia):
        """Conecta a Contasis según el codcia."""
        try:
            empresa = self.config_data['empresas'].get(codcia)
            if not empresa:
                logger.error(f"No se encontró configuración para codcia {codcia}")
                return False
            
            contasis_config = self.config_data['contasis']
            database = empresa['contasis_db']
            
            conn_str = f"postgresql://{contasis_config['username']}:{contasis_config['password']}@{contasis_config['host']}:{contasis_config['port']}/{database}"
            logger.info(f"Conectando a Contasis: {database}")
            self.contasis_conn = psycopg2.connect(conn_str)
            logger.info(f"Conectado a Contasis: {database}")
            return True
        except Exception as e:
            logger.error(f"Error conectando a Contasis: {e}")
            return False
    
    def get_planillas_cab(self, codcia, cper, cmes):
        """Obtiene cabeceras de planillas de SQL Server filtradas por año y mes."""
        try:
            cursor = self.sql_server_conn.cursor()
            query = """
                SELECT Id, NroPlanilla, FechaEmision, TotalGastado, CodAux, NomAux
                FROM FinPlanillaMovilidadCab
                WHERE CodCia = ?
                AND YEAR(FechaEmision) = ?
                AND MONTH(FechaEmision) = ?
                ORDER BY Id
            """
            cursor.execute(query, (codcia, int(cper), int(cmes)))
            columns = [column[0] for column in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            cursor.close()
            return results
        except Exception as e:
            logger.error(f"Error obteniendo cabeceras: {e}")
            return []
    
    def get_planilla_detalles(self, planilla_id):
        """Obtiene detalles de una planilla."""
        try:
            cursor = self.sql_server_conn.cursor()
            query = """
                SELECT Monto, Motivo, Fecha
                FROM FinPlanillaMovilidadDet
                WHERE PlanillaId = ?
                ORDER BY Id
            """
            cursor.execute(query, (planilla_id,))
            columns = [column[0] for column in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            cursor.close()
            return results
        except Exception as e:
            logger.error(f"Error obteniendo detalles: {e}")
            return []
    
    def create_control_table(self):
        """Crea tabla de control de migración si no existe."""
        try:
            cursor = self.sql_server_conn.cursor()
            query = f"""
                IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = '{self.control_table}')
                BEGIN
                    CREATE TABLE {self.control_table} (
                        Id INT IDENTITY(1,1) PRIMARY KEY,
                        CodCia VARCHAR(3),
                        PlanillaId INT,
                        NroPlanilla VARCHAR(50),
                        Cper VARCHAR(4),
                        Cmes VARCHAR(2),
                        Nasiento INT,
                        Estado VARCHAR(20),
                        FechaMigracion DATETIME,
                        MensajeError VARCHAR(500)
                    )
                END
            """
            cursor.execute(query)
            self.sql_server_conn.commit()
            cursor.close()
            logger.info(f"Tabla de control {self.control_table} verificada/creada")
            return True
        except Exception as e:
            logger.error(f"Error creando tabla de control: {e}")
            return False
    
    def is_planilla_migrada(self, planilla_id, codcia, cper, cmes):
        """Verifica si una planilla ya fue migrada."""
        try:
            cursor = self.sql_server_conn.cursor()
            query = f"""
                SELECT COUNT(*) FROM {self.control_table}
                WHERE PlanillaId = ? AND CodCia = ? AND Cper = ? AND Cmes = ? AND Estado = 'MIGRADO'
            """
            cursor.execute(query, (planilla_id, codcia, cper, cmes))
            count = cursor.fetchone()[0]
            cursor.close()
            return count > 0
        except Exception as e:
            logger.error(f"Error verificando migración: {e}")
            return False
    
    def register_migration(self, planilla_id, codcia, nro_planilla, cper, cmes, nasiento, estado, error_msg=''):
        """Registra el estado de migración de una planilla."""
        try:
            cursor = self.sql_server_conn.cursor()
            query = f"""
                INSERT INTO {self.control_table}
                (CodCia, PlanillaId, NroPlanilla, Cper, Cmes, Nasiento, Estado, FechaMigracion, MensajeError)
                VALUES (?, ?, ?, ?, ?, ?, ?, GETDATE(), ?)
            """
            cursor.execute(query, (codcia, planilla_id, nro_planilla, cper, cmes, nasiento, estado, error_msg[:500] if error_msg else None))
            self.sql_server_conn.commit()
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Error registrando migración: {e}")
            return False
    
    def generate_nasiento(self, cursor, cper, cmes, ccodori):
        """Genera número de asiento único por periodo."""
        try:
            if self.current_nasiento is None:
                query = f"SELECT COALESCE(MAX(nasiento), 0) + 1 FROM cf_diario WHERE cper = '{cper}' AND cmes = '{cmes}' AND ccodori = '{ccodori}'"
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
    
    def insert_detalle_line(self, cursor, nasiento, nidlin, ccodcue, ndebe, nhaber, cglosa, cserie, cnumero, cper, cmes, ccodori, ccodruc='', ccoddoc='00', ffechadoc=None, ffechaven=None, ccodmon='S'):
        """Inserta una línea de detalle."""
        try:
            # Truncar cglosa a 80 caracteres
            cglosa = cglosa[:80] if len(cglosa) > 80 else cglosa
            
            query = """
                INSERT INTO cf_diariol 
                (nasiento, nidlin, ccodcue, ndebe, nhaber, cglosa, cserie, cnumero, cper, cmes, ccodori, ccodruc, ccoddoc, ffechadoc, ffechaven, ccodmon)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (nasiento, nidlin, ccodcue, ndebe, nhaber, cglosa, cserie, cnumero, str(cper), str(cmes), str(ccodori), str(ccodruc)[:15], ccoddoc, ffechadoc, ffechaven, ccodmon))
        except Exception as e:
            logger.error(f"Error insertando línea de detalle: {e}")
            raise
    
    def migrate_planilla(self, cabecera, codcia, cper, cmes):
        """Migra una planilla completa a Contasis."""
        try:
            if not self.contasis_conn:
                return False
            
            cursor = self.contasis_conn.cursor()
            
            # Configuración de migración
            migracion = self.config_data['migracion']
            empresa = self.config_data['empresas'][codcia]
            
            ccodori = migracion['ccodori']
            
            # Generar nasiento
            nasiento = self.generate_nasiento(cursor, cper, cmes, ccodori)
            
            # Preparar cabecera
            nro_planilla = cabecera.get('NroPlanilla', '')
            fecha_emision = cabecera.get('FechaEmision')
            total_gastado = cabecera.get('TotalGastado', 0)
            cod_aux = cabecera.get('CodAux', '')
            nom_aux = cabecera.get('NomAux', '')
            
            # Extraer cserie (3 primeros chars) y cnumero (últimos 9 dígitos)
            # Ejemplo: PGM-71941916-2026-0001 -> cserie=PGM, cnumero=2026-0001
            partes = nro_planilla.split('-')
            cserie = partes[0][:3] if len(partes) > 0 else ''
            cnumero = '-'.join(partes[-2:]) if len(partes) >= 2 else nro_planilla[-9:]
            
            # Truncar glosa con PLANILLA MOVILIDAD y nombre
            glosa_cab = f"PLANILLA MOVILIDAD {nom_aux}: {nro_planilla}"[:80]
            
            # Insertar cabecera
            query_cab = """
                INSERT INTO cf_diario 
                (nasiento, cper, cmes, ccodori, cmoneda, cglosa_2, ccodusu, ccodsu, ntcblo, ccodbas, nidreg, nidlin, chknotc, ffecasi)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            logger.info(f"Insertando cabecera: nasiento={nasiento}, cper={cper}, cmes={cmes}, ccodori={ccodori}")
            cursor.execute(query_cab, (
                nasiento, str(cper), str(cmes), str(ccodori), str(migracion['cmoneda']), glosa_cab,
                '1', '1', str(migracion['ntc']), '1', 1, 1, 0, fecha_emision
            ))
            logger.info("Cabecera insertada exitosamente")
            
            # Obtener detalles
            detalles = self.get_planilla_detalles(cabecera['Id'])
            
            # Calcular fechas menor y mayor de los detalles
            ffechadoc = None
            ffechaven = None
            if detalles:
                fechas = [d.get('Fecha') for d in detalles if d.get('Fecha')]
                if fechas:
                    ffechadoc = min(fechas)
                    ffechaven = max(fechas)
            
            if not detalles:
                logger.warning(f"No hay detalles para planilla {cabecera['Id']}, omitiendo asiento")
                # Rollback para no crear asiento vacío
                self.contasis_conn.rollback()
                return None
            else:
                # Insertar líneas de débito
                nidlin = 1
                total_debito = 0
                
                for detalle in detalles:
                    monto = detalle.get('Monto', 0)
                    motivo = detalle.get('Motivo', 'GASTOS')
                    fecha_detalle = detalle.get('Fecha', fecha_emision)
                    glosa_det = f"{glosa_cab}: {motivo}"[:80]
                    
                    self.insert_detalle_line(cursor, nasiento, nidlin, empresa['cuentas']['DEBITO'], monto, 0, glosa_det, cserie, cnumero, cper, cmes, ccodori, cod_aux, '00', fecha_detalle, fecha_detalle, 'S')
                    total_debito += monto
                    nidlin += 1
                
                # Insertar línea de crédito consolidada
                self.insert_detalle_line(cursor, nasiento, nidlin, empresa['cuentas']['CREDITO'], 0, total_debito, glosa_cab, cserie, cnumero, cper, cmes, ccodori, cod_aux, '00', ffechadoc, ffechaven, 'S')
                
                logger.info(f"Insertadas {len(detalles)} líneas de débito y 1 línea de crédito para asiento {nasiento}")
            
            self.contasis_conn.commit()
            cursor.close()
            return nasiento
        except Exception as e:
            logger.error(f"Error migrando planilla: {e}")
            self.contasis_conn.rollback()
            return False
    
    def migrate_empresa(self, codcia, cper, cmes):
        """Migra todas las planillas de una empresa."""
        try:
            logger.info(f"Iniciando migración para codcia {codcia}, periodo {cper}-{cmes}")
            
            # Obtener ccodori de la configuración
            migracion = self.config_data['migracion']
            ccodori = migracion['ccodori']
            
            if not self.connect_sql_server():
                return False
            
            # Crear tabla de control
            if not self.create_control_table():
                return False
            
            if not self.connect_contasis(codcia):
                return False
            
            # Obtener cabeceras
            cabeceras = self.get_planillas_cab(codcia, cper, cmes)
            
            if not cabeceras:
                logger.info(f"No hay planillas para codcia {codcia}")
                return True
            
            logger.info(f"Encontradas {len(cabeceras)} planillas para migrar")
            
            # Migrar cada planilla
            exitos = 0
            omitidas = 0
            errores = 0
            total_asientos = 0
            total_registros = 0
            
            for cabecera in cabeceras:
                planilla_id = cabecera['Id']
                nro_planilla = cabecera.get('NroPlanilla', '')
                
                # Verificar si ya fue migrada
                if self.is_planilla_migrada(planilla_id, codcia, cper, cmes):
                    logger.info(f"Planilla {planilla_id} ya migrada, omitiendo")
                    omitidas += 1
                    continue
                
                # Migrar planilla
                try:
                    result = self.migrate_planilla(cabecera, codcia, cper, cmes)
                    if result:
                        nasiento = result
                        exitos += 1
                        total_asientos += 1
                        # Contar registros de este asiento
                        registros = self.contar_registros_asiento(nasiento, cper, cmes, ccodori)
                        total_registros += registros
                        self.register_migration(planilla_id, codcia, nro_planilla, cper, cmes, nasiento, 'MIGRADO')
                        logger.info(f"Planilla {planilla_id} migrada como asiento {nasiento} ({registros} registros)")
                    else:
                        # Result es None cuando no hay detalles
                        omitidas += 1
                        self.register_migration(planilla_id, codcia, nro_planilla, cper, cmes, None, 'OMITIDA', 'Sin detalles')
                        logger.info(f"Planilla {planilla_id} omitida (sin detalles)")
                except Exception as e:
                    errores += 1
                    self.register_migration(planilla_id, codcia, nro_planilla, cper, cmes, None, 'ERROR', str(e))
                    logger.error(f"Error migrando planilla {planilla_id}: {e}")
            
            logger.info(f"Migración completada: {exitos} exitosas, {omitidas} omitidas, {errores} errores")
            logger.info(f"Total: {total_asientos} asientos, {total_registros} registros de detalle")
            return errores == 0
        except Exception as e:
            logger.error(f"Error en migración de empresa: {e}")
            return False
        finally:
            self.close_connections()
    
    def contar_registros_asiento(self, nasiento, cper, cmes, ccodori):
        """Cuenta los registros de detalle de un asiento."""
        try:
            if not self.contasis_conn:
                return 0
            
            cursor = self.contasis_conn.cursor()
            query = """
                SELECT COUNT(*) 
                FROM cf_diariol 
                WHERE nasiento = %s AND cper = %s AND cmes = %s AND ccodori = %s
            """
            cursor.execute(query, (nasiento, str(cper), str(cmes), str(ccodori)))
            count = cursor.fetchone()[0]
            cursor.close()
            return count
        except Exception as e:
            logger.error(f"Error contando registros del asiento {nasiento}: {e}")
            return 0
    
    def close_connections(self):
        """Cierra todas las conexiones."""
        try:
            if self.sql_server_conn:
                self.sql_server_conn.close()
                self.sql_server_conn = None
            if self.contasis_conn:
                self.contasis_conn.close()
                self.contasis_conn = None
            logger.info("Conexiones cerradas")
        except Exception as e:
            logger.error(f"Error cerrando conexiones: {e}")

def main():
    if len(sys.argv) < 4:
        print("Uso: python subdiario209_migrator.py <codcia> <año> <mes>")
        print("Ejemplo: python subdiario209_migrator.py 007 2026 07")
        sys.exit(1)
    
    codcia = sys.argv[1]
    cper = sys.argv[2]
    cmes = sys.argv[3]
    config_file = '/app/MCon/209/subdiario209_config.json'
    
    migrator = Subdiario209Migrator(config_file)
    
    if not migrator.load_config():
        sys.exit(1)
    
    success = migrator.migrate_empresa(codcia, cper, cmes)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
