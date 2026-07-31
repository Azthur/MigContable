#!/usr/bin/env python3
"""Script para ejecutar SQL en PostgreSQL (MigConta) para crear tablas del Libro 209."""

import sys
import os
sys.path.insert(0, '/app')

import logging
logging.disable(logging.CRITICAL)

from backend.app.core.database import get_dest_db
from sqlalchemy import text

def create_tables_postgresql():
    """Crea las tablas de configuración en PostgreSQL (MigConta)."""
    
    db = next(get_dest_db())
    
    try:
        print("Conectado a PostgreSQL (MigConta)")
        
        # SQL para crear tablas en PostgreSQL
        sql_statements = """
-- Tabla de control para seguimiento de migración del libro 209
CREATE TABLE IF NOT EXISTS libro209_controlmigracion (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    subcategoria_id INTEGER NOT NULL,
    idcontrol_origen VARCHAR(50) NOT NULL,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_migracion TIMESTAMP NULL,
    estado VARCHAR(20) DEFAULT 'PENDIENTE',
    asiento_generado VARCHAR(50) NULL,
    error_mensaje TEXT NULL,
    intentos INTEGER DEFAULT 0,
    fecha_ultimo_intento TIMESTAMP NULL,
    CONSTRAINT uk_libro209_control UNIQUE (empresa_id, subcategoria_id, idcontrol_origen)
);

CREATE INDEX IF NOT EXISTS ix_libro209_control_empresa ON libro209_controlmigracion(empresa_id);
CREATE INDEX IF NOT EXISTS ix_libro209_control_estado ON libro209_controlmigracion(estado);
CREATE INDEX IF NOT EXISTS ix_libro209_control_fechamigracion ON libro209_controlmigracion(fecha_migracion);

-- Tabla de configuración de campos
CREATE TABLE IF NOT EXISTS libro209_configcampos (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    subcategoria_id INTEGER NOT NULL,
    campo_origen VARCHAR(100) NOT NULL,
    campo_destino VARCHAR(100) NOT NULL,
    tipo_dato VARCHAR(20) NOT NULL,
    valor_fijo VARCHAR(500) NULL,
    formula_transformacion TEXT NULL,
    es_requerido BOOLEAN DEFAULT FALSE,
    orden INTEGER DEFAULT 0,
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_libro209_config UNIQUE (empresa_id, subcategoria_id, campo_origen, campo_destino)
);

CREATE INDEX IF NOT EXISTS ix_libro209_config_empresa ON libro209_configcampos(empresa_id);
CREATE INDEX IF NOT EXISTS ix_libro209_config_subcategoria ON libro209_configcampos(subcategoria_id);
CREATE INDEX IF NOT EXISTS ix_libro209_config_activo ON libro209_configcampos(activo);

-- Tabla de configuración de cuentas
CREATE TABLE IF NOT EXISTS libro209_configcuentas (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    subcategoria_id INTEGER NOT NULL,
    tipo_linea VARCHAR(20) NOT NULL,
    cuenta_contable VARCHAR(20) NOT NULL,
    descripcion VARCHAR(200) NULL,
    orden INTEGER DEFAULT 0,
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_libro209_cuentas UNIQUE (empresa_id, subcategoria_id, tipo_linea)
);

CREATE INDEX IF NOT EXISTS ix_libro209_cuentas_empresa ON libro209_configcuentas(empresa_id);
CREATE INDEX IF NOT EXISTS ix_libro209_cuentas_subcategoria ON libro209_configcuentas(subcategoria_id);

-- Tabla de relación empresa - Contasis
CREATE TABLE IF NOT EXISTS libro209_empresacontasis (
    id SERIAL PRIMARY KEY,
    codcia VARCHAR(20) NOT NULL,
    empresa_id INTEGER NOT NULL,
    contasis_host VARCHAR(255) NOT NULL,
    contasis_port INTEGER DEFAULT 5432,
    contasis_database VARCHAR(100) NOT NULL,
    contasis_username VARCHAR(100) NOT NULL,
    contasis_password VARCHAR(255) NOT NULL,
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_libro209_empresacontasis UNIQUE (codcia, empresa_id)
);

CREATE INDEX IF NOT EXISTS ix_libro209_empresacontasis_codcia ON libro209_empresacontasis(codcia);
CREATE INDEX IF NOT EXISTS ix_libro209_empresacontasis_empresaid ON libro209_empresacontasis(empresa_id);
CREATE INDEX IF NOT EXISTS ix_libro209_empresacontasis_activo ON libro209_empresacontasis(activo);
"""
        
        # Ejecutar SQL
        print("Ejecutando SQL para crear tablas en PostgreSQL...")
        db.execute(text(sql_statements))
        db.commit()
        
        print("SQL ejecutado exitosamente")
        
        # Verificar tablas creadas
        result = db.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name LIKE 'libro209_%'
            ORDER BY table_name
        """))
        tables = result.fetchall()
        
        print("\nTablas creadas/verificadas en PostgreSQL:")
        for table in tables:
            print(f"  - {table[0]}")
        
        db.close()
        
        print("\n=== PROCESO COMPLETADO EXITOSAMENTE ===")
        return True
        
    except Exception as e:
        print(f"Error ejecutando SQL: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        db.close()
        return False

if __name__ == "__main__":
    success = create_tables_postgresql()
    sys.exit(0 if success else 1)
