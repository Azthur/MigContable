# Libro 209 Migrator - Sistema de Migración Específico

Sistema de migración dedicado para el Libro 209 que utiliza SQL Server como fuente de control y configuración, e inyecta datos directamente a Contasis (PostgreSQL).

## Arquitectura

```
SQL Server (Origen)          PostgreSQL (Contasis)
├── Libro209_ControlMigracion    ├── cf_diario (cabeceras)
├── Libro209_ConfigCampos        └── cf_diariol (detalles)
└── Libro209_ConfigCuentas
```

## Componentes

### 1. Tablas en SQL Server

#### Libro209_ControlMigracion
Tabla de control para seguimiento de migración:
- `id`: Identificador único
- `empresa_id`: ID de la empresa
- `subcategoria_id`: ID de la subcategoría
- `idcontrol_origen`: ID del registro origen
- `fecha_registro`: Fecha de registro
- `fecha_migracion`: Fecha de migración
- `estado`: PENDIENTE, MIGRADO, ERROR
- `asiento_generado`: Número de asiento generado
- `error_mensaje`: Mensaje de error si falló
- `intentos`: Número de intentos de migración
- `fecha_ultimo_intento`: Fecha del último intento

#### Libro209_ConfigCampos
Tabla de configuración de campos para mapeo dinámico:
- `campo_origen`: Nombre del campo en tabla origen
- `campo_destino`: Nombre del campo en Contasis
- `tipo_dato`: STRING, NUMERIC, DATE, BOOLEAN
- `valor_fijo`: Valor fijo si aplica
- `formula_transformacion`: Fórmula de transformación (opcional)
- `es_requerido`: Indica si el campo es requerido
- `orden`: Orden de procesamiento

#### Libro209_ConfigCuentas
Tabla de configuración de cuentas contables:
- `tipo_linea`: DEBITO, CREDITO
- `cuenta_contable`: Código de cuenta contable
- `descripcion`: Descripción de la cuenta
- `orden`: Orden de procesamiento

### 2. Script Python (libro209_migrator.py)

Script principal que:
- Lee configuración desde SQL Server
- Obtiene registros pendientes de migración
- Transforma datos según configuración
- Inyecta directamente a Contasis
- Actualiza tabla de control

## Instalación

### Paso 1: Crear tablas en SQL Server

Ejecutar el script SQL generado por `create_sql_server_tables.py`:

```bash
python create_sql_server_tables.py > create_tables.sql
```

Luego ejecutar el SQL generado en SQL Server Management Studio o vía script.

### Paso 2: Instalar dependencias Python

```bash
pip install pyodbc psycopg2-binary
```

### Paso 3: Configurar variables de entorno

Copiar el archivo de configuración de ejemplo:

```bash
cp libro209_config.env /etc/libro209/config.env
```

Editar el archivo con las credenciales correctas:
- SQL Server: host, database, username, password
- Contasis: host, port, database, username, password
- Empresa ID

### Paso 4: Configurar Cron

Agregar al crontab:

```bash
crontab -e
```

Agregar una de las líneas del archivo `libro209_cron.example`:

```bash
# Ejecutar cada hora
0 * * * * /usr/bin/python3 /path/to/libro209_migrator.py >> /var/log/libro209_cron.log 2>&1
```

## Configuración

### Agregar Nueva Empresa

1. Insertar configuración de cuentas en `Libro209_ConfigCuentas`:

```sql
INSERT INTO Libro209_ConfigCuentas (empresa_id, subcategoria_id, tipo_linea, cuenta_contable, descripcion, orden)
VALUES 
(10, 80, 'DEBITO', '6599004', 'GASTOS DE MOVILIDAD DEL PERSONAL', 1),
(10, 80, 'CREDITO', '469901', 'CUENTA CREDITO', 2);
```

2. Insertar configuración de campos en `Libro209_ConfigCampos`:

```sql
INSERT INTO Libro209_ConfigCampos (empresa_id, subcategoria_id, campo_origen, campo_destino, tipo_dato, valor_fijo, es_requerido, orden)
VALUES 
(10, 80, 'Fecha', 'cper', 'STRING', NULL, 1, 1),
(10, 80, 'Fecha', 'cmes', 'STRING', NULL, 1, 2),
(10, 80, 'FIXED', 'ccodori', 'STRING', '209', 1, 3);
```

### Modificar Mapeo de Campos

Actualizar registros en `Libro209_ConfigCampos`:

```sql
UPDATE Libro209_ConfigCampos
SET campo_origen = 'NuevoCampoOrigen',
    formula_transformacion = 'UPPER(NuevoCampoOrigen)'
WHERE empresa_id = 5 AND subcategoria_id = 81 AND campo_destino = 'cglosa';
```

### Cambiar Cuentas Contables

Actualizar registros en `Libro209_ConfigCuentas`:

```sql
UPDATE Libro209_ConfigCuentas
SET cuenta_contable = 'NuevaCuenta'
WHERE empresa_id = 5 AND subcategoria_id = 81 AND tipo_linea = 'DEBITO';
```

## Uso

### Ejecución Manual

```bash
# Con variables de entorno
export SQL_SERVER_HOST=localhost
export SQL_SERVER_DATABASE=YLV
export EMPRESA_ID=5
python libro209_migrator.py

# Con archivo de configuración
source /etc/libro209/config.env
python libro209_migrator.py
```

### Ejecución Automática (Cron)

El script se ejecutará automáticamente según la configuración del cron.

### Monitoreo

Ver logs:

```bash
tail -f /var/log/libro209_migrator.log
```

Ver registros de control en SQL Server:

```sql
-- Ver registros pendientes
SELECT * FROM Libro209_ControlMigracion 
WHERE estado = 'PENDIENTE' AND empresa_id = 5;

-- Ver errores
SELECT * FROM Libro209_ControlMigracion 
WHERE estado = 'ERROR' AND empresa_id = 5;

-- Ver migrados hoy
SELECT * FROM Libro209_ControlMigracion 
WHERE estado = 'MIGRADO' 
  AND empresa_id = 5 
  AND CAST(fecha_migracion AS DATE) = CAST(GETDATE() AS DATE);
```

## Ventajas

1. **Control Centralizado**: Todo el control de migración está en SQL Server
2. **Configuración Dinámica**: Cambios en mapeo sin modificar código
3. **Multi-Empresa**: Soporta múltiples empresas con configuración independiente
4. **Resiliente**: Reintentos automáticos y registro de errores
5. **Auditable**: Historial completo de migraciones
6. **Escalable**: Procesamiento por lotes configurable
7. **Independiente**: No depende del sistema ETL principal

## Troubleshooting

### Error: "No module named 'pyodbc'"

```bash
pip install pyodbc
```

### Error: "No module named 'psycopg2'"

```bash
pip install psycopg2-binary
```

### Error: "Table does not exist"

Verificar que las tablas se crearon correctamente en SQL Server:

```sql
SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_NAME IN ('Libro209_ControlMigracion', 'Libro209_ConfigCampos', 'Libro209_ConfigCuentas');
```

### Error: "Connection refused"

Verificar que:
- SQL Server esté accesible desde el servidor donde corre el script
- Contasis esté accesible desde el servidor donde corre el script
- Las credenciales sean correctas
- Los firewalls permitan las conexiones

## Soporte

Para problemas o preguntas, revisar:
- Logs en `/var/log/libro209_migrator.log`
- Tabla de control en SQL Server para ver errores específicos
- Configuración de campos y cuentas en SQL Server
