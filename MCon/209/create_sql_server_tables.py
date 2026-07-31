#!/usr/bin/env python3
"""Script para crear tablas de control y configuración en SQL Server para el libro 209."""

# SQL para crear tabla de control de migración
CREATE_CONTROL_TABLE = """
-- Tabla de control para seguimiento de migración del libro 209
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Libro209_ControlMigracion')
BEGIN
    CREATE TABLE Libro209_ControlMigracion (
        id INT IDENTITY(1,1) PRIMARY KEY,
        empresa_id INT NOT NULL,
        subcategoria_id INT NOT NULL,
        idcontrol_origen VARCHAR(50) NOT NULL,
        fecha_registro DATETIME DEFAULT GETDATE(),
        fecha_migracion DATETIME NULL,
        estado VARCHAR(20) DEFAULT 'PENDIENTE', -- PENDIENTE, MIGRADO, ERROR
        asiento_generado VARCHAR(50) NULL,
        error_mensaje VARCHAR(MAX) NULL,
        intentos INT DEFAULT 0,
        fecha_ultimo_intento DATETIME NULL,
        CONSTRAINT UK_Libro209_Control UNIQUE (empresa_id, subcategoria_id, idcontrol_origen)
    )
    
    CREATE INDEX IX_Libro209_Control_Empresa ON Libro209_ControlMigracion(empresa_id)
    CREATE INDEX IX_Libro209_Control_Estado ON Libro209_ControlMigracion(estado)
    CREATE INDEX IX_Libro209_Control_FechaMigracion ON Libro209_ControlMigracion(fecha_migracion)
    
    PRINT 'Tabla Libro209_ControlMigracion creada exitosamente'
END
ELSE
BEGIN
    PRINT 'Tabla Libro209_ControlMigracion ya existe'
END
"""

# SQL para crear tabla de configuración de campos
CREATE_CONFIG_TABLE = """
-- Tabla de configuración de campos para mapeo dinámico
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Libro209_ConfigCampos')
BEGIN
    CREATE TABLE Libro209_ConfigCampos (
        id INT IDENTITY(1,1) PRIMARY KEY,
        empresa_id INT NOT NULL,
        subcategoria_id INT NOT NULL,
        campo_origen VARCHAR(100) NOT NULL,
        campo_destino VARCHAR(100) NOT NULL,
        tipo_dato VARCHAR(20) NOT NULL, -- STRING, NUMERIC, DATE, BOOLEAN
        valor_fijo VARCHAR(500) NULL,
        formula_transformacion VARCHAR(MAX) NULL,
        es_requerido BIT DEFAULT 0,
        orden INT DEFAULT 0,
        activo BIT DEFAULT 1,
        fecha_creacion DATETIME DEFAULT GETDATE(),
        fecha_actualizacion DATETIME DEFAULT GETDATE(),
        CONSTRAINT UK_Libro209_Config UNIQUE (empresa_id, subcategoria_id, campo_origen, campo_destino)
    )
    
    CREATE INDEX IX_Libro209_Config_Empresa ON Libro209_ConfigCampos(empresa_id)
    CREATE INDEX IX_Libro209_Config_Subcategoria ON Libro209_ConfigCampos(subcategoria_id)
    CREATE INDEX IX_Libro209_Config_Activo ON Libro209_ConfigCampos(activo)
    
    PRINT 'Tabla Libro209_ConfigCampos creada exitosamente'
END
ELSE
BEGIN
    PRINT 'Tabla Libro209_ConfigCampos ya existe'
END
"""

# SQL para crear tabla de configuración de cuentas contables
CREATE_ACCOUNTS_TABLE = """
-- Tabla de configuración de cuentas contables por subcategoría
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Libro209_ConfigCuentas')
BEGIN
    CREATE TABLE Libro209_ConfigCuentas (
        id INT IDENTITY(1,1) PRIMARY KEY,
        empresa_id INT NOT NULL,
        subcategoria_id INT NOT NULL,
        tipo_linea VARCHAR(20) NOT NULL, -- DEBITO, CREDITO
        cuenta_contable VARCHAR(20) NOT NULL,
        descripcion VARCHAR(200) NULL,
        orden INT DEFAULT 0,
        activo BIT DEFAULT 1,
        fecha_creacion DATETIME DEFAULT GETDATE(),
        fecha_actualizacion DATETIME DEFAULT GETDATE(),
        CONSTRAINT UK_Libro209_Cuentas UNIQUE (empresa_id, subcategoria_id, tipo_linea)
    )
    
    CREATE INDEX IX_Libro209_Cuentas_Empresa ON Libro209_ConfigCuentas(empresa_id)
    CREATE INDEX IX_Libro209_Cuentas_Subcategoria ON Libro209_ConfigCuentas(subcategoria_id)
    
    PRINT 'Tabla Libro209_ConfigCuentas creada exitosamente'
END
ELSE
BEGIN
    PRINT 'Tabla Libro209_ConfigCuentas ya existe'
END
"""

# SQL para crear tabla de relación empresa - Contasis
CREATE_EMPRESA_CONTASIS_TABLE = """
-- Tabla de relación entre empresas y sus bases de datos Contasis
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Libro209_EmpresaContasis')
BEGIN
    CREATE TABLE Libro209_EmpresaContasis (
        id INT IDENTITY(1,1) PRIMARY KEY,
        codcia VARCHAR(20) NOT NULL,  -- Código de empresa en SQL Server
        empresa_id INT NOT NULL,       -- ID de empresa en sistema MigConta
        contasis_host VARCHAR(255) NOT NULL,
        contasis_port INT DEFAULT 5432,
        contasis_database VARCHAR(100) NOT NULL,
        contasis_username VARCHAR(100) NOT NULL,
        contasis_password VARCHAR(255) NOT NULL,
        activo BIT DEFAULT 1,
        fecha_creacion DATETIME DEFAULT GETDATE(),
        fecha_actualizacion DATETIME DEFAULT GETDATE(),
        CONSTRAINT UK_Libro209_EmpresaContasis UNIQUE (codcia, empresa_id)
    )
    
    CREATE INDEX IX_Libro209_EmpresaContasis_Codcia ON Libro209_EmpresaContasis(codcia)
    CREATE INDEX IX_Libro209_EmpresaContasis_EmpresaID ON Libro209_EmpresaContasis(empresa_id)
    CREATE INDEX IX_Libro209_EmpresaContasis_Activo ON Libro209_EmpresaContasis(activo)
    
    PRINT 'Tabla Libro209_EmpresaContasis creada exitosamente'
END
ELSE
BEGIN
    PRINT 'Tabla Libro209_EmpresaContasis ya existe'
END
"""

# SQL para insertar configuración inicial
INSERT_INITIAL_CONFIG = """
-- Insertar configuración de cuentas para YLV Nature (empresa_id = 5)
IF NOT EXISTS (SELECT * FROM Libro209_ConfigCuentas WHERE empresa_id = 5)
BEGIN
    INSERT INTO Libro209_ConfigCuentas (empresa_id, subcategoria_id, tipo_linea, cuenta_contable, descripcion, orden)
    VALUES 
    (5, 80, 'DEBITO', '6599004', 'GASTOS DE MOVILIDAD DEL PERSONAL', 1),
    (5, 80, 'CREDITO', '469901', 'CUENTA CREDITO', 2),
    (5, 81, 'DEBITO', '6599004', 'GASTOS DE MOVILIDAD DEL PERSONAL', 1),
    (5, 81, 'CREDITO', '469901', 'CUENTA CREDITO', 2),
    (5, 82, 'DEBITO', '6599004', 'GASTOS DE MOVILIDAD DEL PERSONAL', 1),
    (5, 82, 'CREDITO', '469901', 'CUENTA CREDITO', 2),
    (5, 83, 'DEBITO', '6599004', 'GASTOS DE MOVILIDAD DEL PERSONAL', 1),
    (5, 83, 'CREDITO', '469901', 'CUENTA CREDITO', 2),
    (5, 116, 'DEBITO', '6599004', 'GASTOS DE MOVILIDAD DEL PERSONAL', 1),
    (5, 116, 'CREDITO', '469901', 'CUENTA CREDITO', 2)
    
    PRINT 'Configuración de cuentas inicial insertada para YLV Nature'
END

-- Insertar relación empresa - Contasis para YLV Nature (codcia = '05', empresa_id = 5)
IF NOT EXISTS (SELECT * FROM Libro209_EmpresaContasis WHERE codcia = '05' AND empresa_id = 5)
BEGIN
    INSERT INTO Libro209_EmpresaContasis 
    (codcia, empresa_id, contasis_host, contasis_port, contasis_database, contasis_username, contasis_password)
    VALUES 
    ('05', 5, 'localhost', 5432, 'contasis', 'postgres', 'your_password_here')
    
    PRINT 'Relación empresa - Contasis insertada para YLV Nature'
END

-- Insertar configuración de campos para subcategoría 81 (YLV Nature)
IF NOT EXISTS (SELECT * FROM Libro209_ConfigCampos WHERE empresa_id = 5 AND subcategoria_id = 81)
BEGIN
    INSERT INTO Libro209_ConfigCampos (empresa_id, subcategoria_id, campo_origen, campo_destino, tipo_dato, valor_fijo, es_requerido, orden)
    VALUES 
    (5, 81, 'Fecha', 'cper', 'STRING', NULL, 1, 1),
    (5, 81, 'Fecha', 'cmes', 'STRING', NULL, 1, 2),
    (5, 81, 'Fecha', 'ffechadoc', 'DATE', NULL, 1, 3),
    (5, 81, 'C_tipocambiosunat', 'ntc', 'NUMERIC', NULL, 1, 4),
    (5, 81, 'C_tipomoneda', 'ccodmon', 'STRING', NULL, 1, 5),
    (5, 81, 'Importe', 'ndebe', 'NUMERIC', NULL, 1, 6),
    (5, 81, 'Importe', 'nhaber', 'NUMERIC', NULL, 1, 7),
    (5, 81, 'C_descripcion', 'cglosa', 'STRING', NULL, 1, 8),
    (5, 81, 'C_tipodoc', 'ccoddoc', 'STRING', NULL, 1, 9),
    (5, 81, 'C_serie', 'cserie', 'STRING', NULL, 0, 10),
    (5, 81, 'C_numero', 'cnumero', 'STRING', NULL, 0, 11),
    (5, 81, 'C_ruc', 'ccodruc', 'STRING', NULL, 0, 12),
    (5, 81, 'C_razon_social', 'cdes', 'STRING', NULL, 0, 13),
    (5, 81, 'FIXED', 'ccodori', 'STRING', '209', 1, 14),
    (5, 81, 'FIXED', 'cdoc_dc', 'STRING', '00', 1, 15),
    (5, 81, 'FIXED', 'ccodenti', 'STRING', '01', 1, 16),
    (5, 81, 'FIXED', 'clecvmes', 'STRING', '07', 1, 17),
    (5, 81, 'FIXED', 'cledmcmes', 'STRING', '07', 1, 18),
    (5, 81, 'FIXED', 'clecvesta', 'STRING', '1', 1, 19),
    (5, 81, 'FIXED', 'cledmcesta', 'STRING', '1', 1, 20)
    
    PRINT 'Configuración de campos inicial insertada para subcategoría 81'
END
"""

def print_sql_statements():
    """Imprime los statements SQL para crear las tablas."""
    print("=== SQL PARA CREAR TABLAS EN SQL SERVER ===\n")
    print("-- 1. Tabla de control de migración")
    print(CREATE_CONTROL_TABLE)
    print("\n-- 2. Tabla de configuración de campos")
    print(CREATE_CONFIG_TABLE)
    print("\n-- 3. Tabla de configuración de cuentas")
    print(CREATE_ACCOUNTS_TABLE)
    print("\n-- 4. Tabla de relación empresa - Contasis")
    print(CREATE_EMPRESA_CONTASIS_TABLE)
    print("\n-- 5. Configuración inicial")
    print(INSERT_INITIAL_CONFIG)

if __name__ == "__main__":
    print_sql_statements()
