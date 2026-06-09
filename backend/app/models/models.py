from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Numeric, Date, ForeignKey, BigInteger, SmallInteger, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.app.core.database import DestBase

# ─── Usuarios ────────────────────────────────────────────────────────────────

class User(DestBase):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    role = Column(String(50), default="operator")  # admin, operator
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# ─── Empresas ────────────────────────────────────────────────────────────────

class Company(DestBase):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    ruc = Column(String(20), nullable=True, unique=True)
    description = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones
    source_connections = relationship("SourceConnection", back_populates="company", cascade="all, delete-orphan")
    dest_connections = relationship("DestinationConnection", back_populates="company", cascade="all, delete-orphan")
    final_dest_connections = relationship("FinalDestConnection", back_populates="company", cascade="all, delete-orphan")
    table_selections = relationship("TableSelection", back_populates="company", cascade="all, delete-orphan")
    final_table_selections = relationship("FinalTableSelection", back_populates="company", cascade="all, delete-orphan")
    account_mappings = relationship("AccountMapping", back_populates="company", cascade="all, delete-orphan")
    document_mappings = relationship("DocumentTypeMapping", back_populates="company", cascade="all, delete-orphan")
    mapeo_categorias = relationship("MapeoCategoria", back_populates="company", cascade="all, delete-orphan")
    migration_controls = relationship("MigrationControl", back_populates="company", cascade="all, delete-orphan")
    user_catalogs = relationship("UserCatalog", back_populates="company", cascade="all, delete-orphan")


class SourceConnection(DestBase):
    __tablename__ = "source_connections"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    db_type = Column(String(20), default="MSSQL")
    host = Column(String(200), nullable=False)
    port = Column(Integer, default=1433)
    database_name = Column(String(200), nullable=False)
    username = Column(String(100), nullable=False)
    password = Column(String(500), nullable=False)
    driver = Column(String(100), default="ODBC Driver 17 for SQL Server")
    extra_params = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    last_tested_at = Column(DateTime(timezone=True), nullable=True)
    last_test_status = Column(String(20), nullable=True)
    last_test_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    company = relationship("Company", back_populates="source_connections")
    table_selections = relationship("TableSelection", back_populates="source_connection", cascade="all, delete-orphan")


class DestinationConnection(DestBase):
    __tablename__ = "destination_connections"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    host = Column(String(200), nullable=False, default="localhost")
    port = Column(Integer, default=5433)
    database_name = Column(String(200), nullable=False)
    username = Column(String(100), nullable=False, default="postgres")
    password = Column(String(500), nullable=False)
    is_active = Column(Boolean, default=True)
    last_tested_at = Column(DateTime(timezone=True), nullable=True)
    last_test_status = Column(String(20), nullable=True)
    last_test_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    company = relationship("Company", back_populates="dest_connections")


class FinalDestConnection(DestBase):
    """Conexión al destino final de contabilidad (ej: contasis_001 en PostgreSQL 9)"""
    __tablename__ = "final_dest_connections"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    db_type = Column(String(20), default="POSTGRESQL")
    host = Column(String(200), nullable=False, default="localhost")
    port = Column(Integer, default=5432)
    database_name = Column(String(200), nullable=False)
    username = Column(String(100), nullable=False, default="postgres")
    password = Column(String(500), nullable=False)
    target_table = Column(String(200), nullable=True)
    target_schema = Column(String(100), default="public")
    is_active = Column(Boolean, default=True)
    last_tested_at = Column(DateTime(timezone=True), nullable=True)
    last_test_status = Column(String(20), nullable=True)
    last_test_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    company = relationship("Company", back_populates="final_dest_connections")
    final_table_selections = relationship("FinalTableSelection", back_populates="final_dest_connection", cascade="all, delete-orphan")


class FinalTableSelection(DestBase):
    __tablename__ = "final_table_selections"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    final_dest_connection_id = Column(Integer, ForeignKey("final_dest_connections.id"), nullable=False, index=True)
    table_schema = Column(String(100), default="public")
    table_name = Column(String(200), nullable=False)
    is_selected = Column(Boolean, default=False)
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    company = relationship("Company", back_populates="final_table_selections")
    final_dest_connection = relationship("FinalDestConnection", back_populates="final_table_selections")


class TableSelection(DestBase):
    __tablename__ = "table_selections"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    source_connection_id = Column(Integer, ForeignKey("source_connections.id"), nullable=False, index=True)
    table_schema = Column(String(100), default="dbo")
    table_name = Column(String(200), nullable=False)
    is_selected = Column(Boolean, default=False)
    extraction_order = Column(Integer, default=0)
    custom_query = Column(Text, nullable=True)
    date_column = Column(String(100), nullable=True)
    # Control incremental
    control_column = Column(String(100), nullable=True)   # Columna para detectar nuevos registros (ej: ID, FechaEmision)
    control_column_type = Column(String(20), default="DATE")  # DATE, INTEGER, DATETIME
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    company = relationship("Company", back_populates="table_selections")
    source_connection = relationship("SourceConnection", back_populates="table_selections")
    column_filters = relationship("ColumnFilter", back_populates="table_selection", cascade="all, delete-orphan")
    computed_column_rules = relationship("ComputedColumnRule", back_populates="table_selection", cascade="all, delete-orphan")


# ─── Filtros por Columna ──────────────────────────────────────────────────────

class ColumnFilter(DestBase):
    """Filtros aplicados a columnas específicas de una tabla seleccionada para la extracción"""
    __tablename__ = "column_filters"

    id = Column(Integer, primary_key=True, index=True)
    table_selection_id = Column(Integer, ForeignKey("table_selections.id"), nullable=False, index=True)
    column_name = Column(String(200), nullable=False)
    operator = Column(String(20), nullable=False)  # =, >, <, >=, <=, LIKE, IN, BETWEEN, IS NULL, IS NOT NULL
    filter_value = Column(String(500), nullable=True)    # Valor principal del filtro
    filter_value2 = Column(String(500), nullable=True)   # Segundo valor (para BETWEEN)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    table_selection = relationship("TableSelection", back_populates="column_filters")


# ─── Columnas Calculadas (Condicionales tipo Excel) ──────────────────────────

class ComputedColumnRule(DestBase):
    """Reglas condicionales para crear columnas calculadas durante la extracción ETL.
    Equivale a IF(source_column = condition_value, result_value, default_value)"""
    __tablename__ = "computed_column_rules"

    id = Column(Integer, primary_key=True, index=True)
    table_selection_id = Column(Integer, ForeignKey("table_selections.id"), nullable=False, index=True)
    new_column_name = Column(String(200), nullable=False)       # Nombre de la nueva columna (ej: "tipo_doc")
    source_column = Column(String(200), nullable=False)         # Columna origen a evaluar (ej: "coddoc")
    condition_value = Column(String(500), nullable=False)       # Valor a comparar (ej: "BOLE")
    result_value = Column(String(500), nullable=False)          # Resultado si cumple (ej: "03")
    default_value = Column(String(500), nullable=True)          # Valor por defecto si no hay match
    priority = Column(Integer, default=0)                       # Orden de evaluación
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    table_selection = relationship("TableSelection", back_populates="computed_column_rules")


# ─── Tipo de Cambio (SUNAT) ──────────────────────────────────────────────────

class TipoCambio(DestBase):
    """Tipo de cambio diario SUNAT (compra y venta)"""
    __tablename__ = "tipo_cambio"

    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(Date, nullable=False, unique=True, index=True)
    compra = Column(Numeric(10, 6), nullable=False)
    venta = Column(Numeric(10, 6), nullable=False)
    source = Column(String(50), default="api.org.pe")
    created_at = Column(DateTime(timezone=True), server_default=func.now())



class MigrationControl(DestBase):
    """Controla qué registros ya fueron migrados para hacer migraciones incrementales"""
    __tablename__ = "migration_controls"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    source_table = Column(String(200), nullable=False, index=True)
    control_column = Column(String(100), nullable=True)       # Columna usada para control
    last_migrated_value = Column(String(500), nullable=True)  # Último valor migrado (fecha o ID)
    total_migrated = Column(BigInteger, default=0)
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    last_run_status = Column(String(20), nullable=True)       # OK, ERROR
    last_run_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    company = relationship("Company", back_populates="migration_controls")


# ─── Catálogos Contables ──────────────────────────────────────────────────────

class CatCuentaContable(DestBase):
    """Plan de cuentas contables para mapeo"""
    __tablename__ = "cat_cuentas_contables"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True, index=True)
    codigo = Column(String(20), nullable=False, index=True)
    descripcion = Column(String(300), nullable=False)
    tipo = Column(String(50), nullable=True)   # ACTIVO, PASIVO, INGRESO, GASTO, etc.
    nivel = Column(Integer, default=1)
    moneda = Column(String(10), default="MN")  # MN=Soles, ME=Dólares, AM=Ambas
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CatCuentaPresupuesto(DestBase):
    """Cuentas presupuestales"""
    __tablename__ = "cat_cuentas_presupuesto"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True, index=True)
    codigo = Column(String(20), nullable=False, index=True)
    descripcion = Column(String(300), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CatCentroCosto(DestBase):
    """Centros de costo"""
    __tablename__ = "cat_centros_costo"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True, index=True)
    codigo = Column(String(20), nullable=False, index=True)
    descripcion = Column(String(300), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CatTipoAnalitica(DestBase):
    """Tipos de analítica contable"""
    __tablename__ = "cat_tipo_analitica"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True, index=True)
    codigo = Column(String(20), nullable=False, index=True)
    descripcion = Column(String(300), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CatProducto(DestBase):
    """Catálogo de productos"""
    __tablename__ = "cat_productos"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True, index=True)
    codigo = Column(String(50), nullable=False, index=True)
    descripcion = Column(String(300), nullable=False)
    unidad = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CatTipoMovimiento(DestBase):
    """Tipos de movimiento contable (ej: 03-BOLETA DE VENTA)"""
    __tablename__ = "cat_tipo_movimiento"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True, index=True)
    codigo = Column(String(10), nullable=False, index=True)
    descripcion = Column(String(200), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ─── Mapeo Contable ───────────────────────────────────────────────────────────

class MapeoCategoria(DestBase):
    """Categoría principal de mapeo (ej: 'Migración Majestic → Contasis')"""
    __tablename__ = "mapeo_categorias"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    nombre = Column(String(300), nullable=False)
    descripcion = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    company = relationship("Company", back_populates="mapeo_categorias")
    subcategorias = relationship("MapeoSubcategoria", back_populates="categoria", cascade="all, delete-orphan")


class MapeoSubcategoria(DestBase):
    """Sub-categoría de mapeo (ej: 'Migración Registro de Ventas')"""
    __tablename__ = "mapeo_subcategorias"

    id = Column(Integer, primary_key=True, index=True)
    categoria_id = Column(Integer, ForeignKey("mapeo_categorias.id"), nullable=False, index=True)
    nombre = Column(String(300), nullable=False)
    descripcion = Column(Text, nullable=True)
    # Tabla origen en BD intermedia de donde se toman los datos
    tabla_origen = Column(String(200), nullable=True)
    # Código de origen del asiento (ej: 002)
    codigo_origen = Column(String(10), nullable=True)
    # Claves de agrupación para generar nasiento (ej: coddoc,cserie,cnumero)
    clave_asiento = Column(String(500), nullable=True)
    # Fórmulas/columnas para armar los campos de la cabecera (cf_diario)
    mapeo_cabecera = Column(JSON, nullable=True)
    # Tabla del destino final para líneas de detalle (ej: cf_diariol)
    tabla_destino_detalle = Column(String(200), nullable=True)
    # Tabla del destino final para cabecera de asiento (ej: cf_diario)
    tabla_destino_cabecera = Column(String(200), nullable=True)
    # Columnas específicas de destino global (para correlativos)
    col_destino_nasiento = Column(String(100), nullable=True) 
    col_destino_nidlin = Column(String(100), nullable=True)
    schema_destino = Column(String(100), nullable=True, default="public")
    # Configuración para Ajustes de Redondeo
    col_destino_debe = Column(String(100), nullable=True)
    col_destino_haber = Column(String(100), nullable=True)
    pares_redondeo = Column(JSON, nullable=True)
    # Controlar qué se genera por subcategoría
    generate_headers = Column(Boolean, default=True)
    generate_details = Column(Boolean, default=True)
    # Número de asiento inicial configurable (opcional)
    asiento_inicial = Column(Integer, nullable=True)
    # Control Incremental para generación — columna en tabla_origen que rastrea documentos migrados
    control_column_origen = Column(String(200), nullable=True)
    # Último valor de control migrado exitosamente al destino final
    last_generated_control_value = Column(String(500), nullable=True)
    # Columnas origen personalizadas para periodo y mes
    col_origen_periodo = Column(String(100), nullable=True)
    col_origen_mes = Column(String(100), nullable=True)
    # Filtros de periodo/fecha por subcategoría (JSON array)
    # Formato: [{"column": "anos", "operator": "=", "value": "2026"},
    #           {"column": "C_mes", "operator": ">=", "value": "02"}]
    # Si está vacío o null, se procesan todos los registros sin filtro de periodo.
    filter_rules = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    categoria = relationship("MapeoCategoria", back_populates="subcategorias")
    lineas_asiento = relationship("MapeoLineaAsiento", back_populates="subcategoria", cascade="all, delete-orphan")


class MapeoLineaAsiento(DestBase):
    """
    Define una línea del asiento contable.
    Cada línea representa una cuenta (ej: 121201 al Debe, 70221701 al Haber).
    """
    __tablename__ = "mapeo_lineas_asiento"

    id = Column(Integer, primary_key=True, index=True)
    subcategoria_id = Column(Integer, ForeignKey("mapeo_subcategorias.id"), nullable=False, index=True)
    orden = Column(Integer, default=0)
    nombre_linea = Column(String(200), nullable=True)   # Descripción de la línea (ej: "Ventas - Ingresos")

    # Diccionario JSON con las fórmulas/columnas para mapear la línea en cf_diariol
    # Ej: {"ccodcue": "121201", "ndebe": "impnet", "cglosa": "CONCAT('Vtas', fchdoc)"}
    mapeo_detalle = Column(JSON, nullable=True)

    # Condición de Excel/AST opcional para decidir si se evalúa y genera esta fila
    # Ej: "ccoddoc = '07'"
    condicion_aplicacion = Column(String(500), nullable=True)

    # Indica si esta línea absorberá la diferencia de ceros/redondeos
    aplica_ajuste_redondeo = Column(Boolean, default=False)

    # Nivel de agrupación al generar (CABECERA o DETALLE)
    nivel = Column(String(20), default="DETALLE")

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    subcategoria = relationship("MapeoSubcategoria", back_populates="lineas_asiento")


# ─── Asientos Contables Generados ────────────────────────────────────────────

class AsientoContableGenerado(DestBase):
    """
    Asientos contables generados en el formato exacto del CSV de Contasis.
    Estos son los registros listos para importar al sistema de contabilidad.
    """
    __tablename__ = "asientos_contables_generados"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    subcategoria_id = Column(Integer, ForeignKey("mapeo_subcategorias.id"), nullable=True, index=True)

    # ── Campos del CSV de Contasis ──
    cper = Column(String(10), nullable=True)        # Período (año)
    cmes = Column(String(5), nullable=True)         # Mes
    ccodori = Column(String(10), nullable=True)     # Código de origen
    nasiento = Column(Integer, nullable=True)       # Número de asiento
    nidlin = Column(Integer, nullable=True)         # Número de línea
    ntc = Column(Numeric(10, 6), nullable=True)     # Tipo de cambio
    ccodcue = Column(String(20), nullable=True, index=True)  # Cuenta contable
    ndebe = Column(Numeric(18, 4), default=0)       # Debe
    nhaber = Column(Numeric(18, 4), default=0)      # Haber
    cglosa = Column(String(500), nullable=True)     # Glosa
    ndebes = Column(Numeric(18, 4), default=0)      # Debe soles
    nhabers = Column(Numeric(18, 4), default=0)     # Haber soles
    ndebed = Column(Numeric(18, 4), default=0)      # Debe dólares
    nhaberd = Column(Numeric(18, 4), default=0)     # Haber dólares
    ccoddoc = Column(String(5), nullable=True)      # Tipo documento (03=Boleta)
    cserie = Column(String(20), nullable=True)      # Serie
    cnumero = Column(String(20), nullable=True)     # Número
    cnumfin = Column(String(20), nullable=True)     # Número final
    ffechadoc = Column(String(20), nullable=True)   # Fecha documento
    ccodruc = Column(String(20), nullable=True)     # RUC
    ccodenti = Column(String(20), nullable=True)    # Código entidad
    ffechaven = Column(String(20), nullable=True)   # Fecha vencimiento
    nbase1 = Column(Numeric(18, 4), default=0)      # Base imponible 1
    nigv1 = Column(Numeric(18, 4), default=0)       # IGV 1
    nbase2 = Column(Numeric(18, 4), default=0)
    nigv2 = Column(Numeric(18, 4), default=0)
    ntot = Column(Numeric(18, 4), default=0)        # Total
    nbase1s = Column(Numeric(18, 4), default=0)
    nigv1s = Column(Numeric(18, 4), default=0)
    ntots = Column(Numeric(18, 4), default=0)
    nbase1d = Column(Numeric(18, 4), default=0)
    nigv1d = Column(Numeric(18, 4), default=0)
    ntotd = Column(Numeric(18, 4), default=0)
    ccodcos = Column(String(20), nullable=True)     # Centro de costo 1
    ccodcos2 = Column(String(20), nullable=True)    # Centro de costo 2
    ccodpresu = Column(String(20), nullable=True)   # Cuenta presupuestal
    ccodmon = Column(String(5), nullable=True)      # Moneda (14=Soles, 02=Dólares)
    cregis = Column(String(5), nullable=True)       # Registro (V=Ventas)
    ncomp = Column(Integer, default=0)              # Número de comprobante
    cdes = Column(String(10), nullable=True)
    cdestino = Column(String(10), nullable=True)
    nina = Column(Numeric(18, 4), default=0)
    nexo = Column(Numeric(18, 4), default=0)
    nisc = Column(Numeric(18, 4), default=0)

    # ── Control ──
    estado = Column(String(20), default="PENDIENTE")  # PENDIENTE, EXPORTADO, ERROR
    lote_id = Column(String(50), nullable=True, index=True)  # ID del lote de generación
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ─── Configuración (ahora por empresa) ───────────────────────────────────────

class AccountMapping(DestBase):
    __tablename__ = "config_account_mapping"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True, index=True)
    source_account_code = Column(String(50), nullable=False, index=True)
    source_account_name = Column(String(200))
    dest_account_code = Column(String(50), nullable=False)
    dest_cost_center = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    company = relationship("Company", back_populates="account_mappings")


class DocumentTypeMapping(DestBase):
    __tablename__ = "config_document_mapping"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True, index=True)
    source_doc_type = Column(String(20), nullable=False)
    dest_doc_type = Column(String(20), nullable=False)
    description = Column(String(100))
    is_active = Column(Boolean, default=True)

    company = relationship("Company", back_populates="document_mappings")


class TransformationRule(DestBase):
    __tablename__ = "config_transformation_rules"

    id = Column(Integer, primary_key=True, index=True)
    rule_name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    rule_type = Column(String(50))
    rule_content = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)


class IntegLog(DestBase):
    __tablename__ = "integ_logs"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True, index=True)
    process_name = Column(String(100))
    status = Column(String(20))  # 'SUCCESS', 'ERROR', 'WARNING', 'RUNNING'
    message = Column(Text)
    details = Column(Text)
    records_processed = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AccountingEntry(DestBase):
    __tablename__ = "accounting_entries"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True, index=True)
    date = Column(Date, nullable=False, index=True)
    account_code = Column(String(50), nullable=False, index=True)
    debit = Column(Numeric(18, 2), default=0)
    credit = Column(Numeric(18, 2), default=0)
    description = Column(String(500))
    document_ref = Column(String(100), index=True)
    source_table = Column(String(200), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ─── Tablas Contasis Finales (estructura idéntica al destino) ─────────────────

class CfDiariol(DestBase):
    """
    Líneas de asiento contable en formato exacto de la tabla cf_diariol de Contasis.
    Se usa como staging en migconta_db antes de insertar en el destino final.
    """
    __tablename__ = "cf_diariol"

    id = Column(Integer, primary_key=True, index=True)

    # ── Control interno (no existe en Contasis) ──
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True, index=True)
    subcategoria_id = Column(Integer, ForeignKey("mapeo_subcategorias.id"), nullable=True, index=True)
    lote_id = Column(String(50), nullable=True, index=True)
    estado = Column(String(20), default="PENDIENTE", index=True)  # PENDIENTE, MIGRADO, ERROR
    idcontrol = Column(String(200), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # ── Campos de Contasis cf_diariol (en orden del CSV) ──
    cper = Column(String(10), nullable=True, index=True)
    cmes = Column(String(5), nullable=True, index=True)
    ccodori = Column(String(10), nullable=True)
    nasiento = Column(Integer, nullable=True)
    nidlin = Column(Integer, nullable=True)
    ntc = Column(Numeric(10, 6), nullable=True, default=0)
    ccodcue = Column(String(20), nullable=True, index=True)
    ndebe = Column(Numeric(18, 4), default=0)
    nhaber = Column(Numeric(18, 4), default=0)
    cglosa = Column(String(500), nullable=True)
    ndebes = Column(Numeric(18, 4), default=0)
    nhabers = Column(Numeric(18, 4), default=0)
    ndebed = Column(Numeric(18, 4), default=0)
    nhaberd = Column(Numeric(18, 4), default=0)
    cdes = Column(String(10), nullable=True)
    cdestino = Column(String(10), nullable=True)
    ndifauto = Column(Numeric(18, 4), default=0)
    najusauto = Column(Numeric(18, 4), default=0)
    cregis = Column(String(5), nullable=True)
    ncomp = Column(Integer, default=0)
    ccoddoc = Column(String(5), nullable=True)
    cserie = Column(String(20), nullable=True)
    cnumero = Column(String(20), nullable=True)
    cnumfin = Column(String(20), nullable=True)
    ffechadoc = Column(String(20), nullable=True)
    ccodruc = Column(String(20), nullable=True)
    ccodenti = Column(String(20), nullable=True)
    ffechaven = Column(String(20), nullable=True)
    nbase1 = Column(Numeric(18, 4), default=0)
    nigv1 = Column(Numeric(18, 4), default=0)
    nbase2 = Column(Numeric(18, 4), default=0)
    nigv2 = Column(Numeric(18, 4), default=0)
    nbase3 = Column(Numeric(18, 4), default=0)
    nigv3 = Column(Numeric(18, 4), default=0)
    nina = Column(Numeric(18, 4), default=0)
    nexo = Column(Numeric(18, 4), default=0)
    nisc = Column(Numeric(18, 4), default=0)
    nivabase = Column(Numeric(18, 4), default=0)
    nivaimp = Column(Numeric(18, 4), default=0)
    ntot = Column(Numeric(18, 4), default=0)
    nbase1s = Column(Numeric(18, 4), default=0)
    nigv1s = Column(Numeric(18, 4), default=0)
    nbase2s = Column(Numeric(18, 4), default=0)
    nigv2s = Column(Numeric(18, 4), default=0)
    nbase3s = Column(Numeric(18, 4), default=0)
    nigv3s = Column(Numeric(18, 4), default=0)
    ninas = Column(Numeric(18, 4), default=0)
    nexos = Column(Numeric(18, 4), default=0)
    niscs = Column(Numeric(18, 4), default=0)
    nivabases = Column(Numeric(18, 4), default=0)
    nivaimps = Column(Numeric(18, 4), default=0)
    ntots = Column(Numeric(18, 4), default=0)
    nbase1d = Column(Numeric(18, 4), default=0)
    nigv1d = Column(Numeric(18, 4), default=0)
    nbase2d = Column(Numeric(18, 4), default=0)
    nigv2d = Column(Numeric(18, 4), default=0)
    nbase3d = Column(Numeric(18, 4), default=0)
    nigv3d = Column(Numeric(18, 4), default=0)
    ninad = Column(Numeric(18, 4), default=0)
    nexod = Column(Numeric(18, 4), default=0)
    niscd = Column(Numeric(18, 4), default=0)
    nivabased = Column(Numeric(18, 4), default=0)
    nivaimpd = Column(Numeric(18, 4), default=0)
    ntotd = Column(Numeric(18, 4), default=0)
    ccodclas = Column(String(10), nullable=True)
    ccodflu = Column(String(10), nullable=True)
    ccodpago = Column(String(10), nullable=True)
    ccodcos = Column(String(20), nullable=True)
    ccodcos2 = Column(String(20), nullable=True)
    ccodpresu = Column(String(20), nullable=True)
    ccodcam = Column(String(10), nullable=True)
    ccodcam2 = Column(String(10), nullable=True)
    ccodecpntribcol = Column(String(10), nullable=True)
    ccodecpnniifcol = Column(String(10), nullable=True)
    cglosa2 = Column(String(500), nullable=True)
    cmesc = Column(String(5), nullable=True)
    cmreg = Column(String(5), nullable=True)
    ccodocon = Column(String(10), nullable=True)
    ndiferido = Column(Numeric(18, 4), default=0)
    ffechadif = Column(String(20), nullable=True)
    nresp = Column(Numeric(18, 4), default=0)
    ccodpps = Column(String(10), nullable=True)
    ccodpds = Column(String(10), nullable=True)
    cregisre = Column(String(5), nullable=True)
    nperdenre = Column(Numeric(18, 4), default=0)
    nporre = Column(Numeric(18, 4), default=0)
    ffecre = Column(String(20), nullable=True)
    cserre = Column(String(20), nullable=True)
    cnumre = Column(String(20), nullable=True)
    cnumdere = Column(String(20), nullable=True)
    ntcre = Column(Numeric(10, 6), nullable=True, default=0)
    nbaseres = Column(Numeric(18, 4), default=0)
    nbasered = Column(Numeric(18, 4), default=0)
    nimpres = Column(Numeric(18, 4), default=0)
    nimpred = Column(Numeric(18, 4), default=0)
    cpdbdetcod = Column(String(20), nullable=True)
    ccodretran = Column(String(10), nullable=True)
    ccodtopdet = Column(String(10), nullable=True)
    npagdetra = Column(Numeric(18, 4), default=0)
    cdocnodom = Column(String(5), nullable=True)
    ccodtipren = Column(String(10), nullable=True)
    crefdoc = Column(String(20), nullable=True)
    freffec = Column(String(20), nullable=True)
    crefser = Column(String(20), nullable=True)
    crefnum = Column(String(20), nullable=True)
    ccoddas = Column(String(10), nullable=True)
    cyeardas = Column(String(10), nullable=True)
    ccorrdas = Column(String(10), nullable=True)
    ffembdas = Column(String(20), nullable=True)
    ffregdas = Column(String(20), nullable=True)
    nfobdas = Column(Numeric(18, 4), default=0)
    nfobdad = Column(Numeric(18, 4), default=0)
    nlecorre = Column(Numeric(18, 4), default=0)
    clecvesta = Column(String(5), nullable=True)
    clecvmes = Column(String(5), nullable=True)
    clecvper = Column(String(10), nullable=True)
    cledmcesta = Column(String(5), nullable=True)
    cledmcmes = Column(String(5), nullable=True)
    cledmcper = Column(String(10), nullable=True)
    nlecorrere = Column(Numeric(18, 4), default=0)
    nautamo = Column(Numeric(18, 4), default=0)
    ffec_dc = Column(String(20), nullable=True)
    cdoc_dc = Column(String(5), nullable=True)
    cser_dc = Column(String(20), nullable=True)
    cnum_dc = Column(String(20), nullable=True)
    cdoc_nd = Column(String(5), nullable=True)
    cser_nd = Column(String(20), nullable=True)
    cnum_nd = Column(String(20), nullable=True)
    nrenbru_nd = Column(Numeric(18, 4), default=0)
    nrennet_nd = Column(Numeric(18, 4), default=0)
    nimpret_nd = Column(Numeric(18, 4), default=0)
    ndedcos_nd = Column(Numeric(18, 4), default=0)
    ntasret_nd = Column(Numeric(18, 4), default=0)
    ccodmon = Column(String(5), nullable=True)
    ntc_nd = Column(Numeric(10, 6), nullable=True, default=0)
    nintext = Column(Numeric(18, 4), default=0)
    nicbper = Column(Numeric(18, 4), default=0)
    nicbpers = Column(Numeric(18, 4), default=0)
    nicbperd = Column(Numeric(18, 4), default=0)
    nigvxacre = Column(Numeric(18, 4), default=0)
    ccodsu = Column(String(10), nullable=True)
    ffecasi = Column(String(20), nullable=True)
    idxacre = Column(Numeric(18, 4), default=0)
    cmonxacre = Column(String(5), nullable=True)
    nidreglin = Column(Numeric(18, 4), default=0)
    crvieap = Column(String(5), nullable=True)
    valida_sunat = Column(String(5), nullable=True)
    nflgigvrec = Column(SmallInteger, default=0)
    nflgprorrateo = Column(SmallInteger, default=0)
    cctapro = Column(String(20), nullable=True)
    npigv = Column(Numeric(18, 4), default=0)
    nadopcion = Column(SmallInteger, default=0)
    nporceparti = Column(Numeric(10, 6), default=0)
    nimpbenefley = Column(Numeric(18, 4), default=0)
    nbasetg = Column(Numeric(18, 4), default=0)
    nbasetgs = Column(Numeric(18, 4), default=0)
    nbasetgd = Column(Numeric(18, 4), default=0)
    nigvtg = Column(Numeric(18, 4), default=0)
    nigvtgs = Column(Numeric(18, 4), default=0)
    nigvtgd = Column(Numeric(18, 4), default=0)
    ninatg = Column(Numeric(18, 4), default=0)
    ninatgs = Column(Numeric(18, 4), default=0)
    ninatgd = Column(Numeric(18, 4), default=0)
    nexotg = Column(Numeric(18, 4), default=0)
    nexotgs = Column(Numeric(18, 4), default=0)
    nexotgd = Column(Numeric(18, 4), default=0)
    nexptg = Column(Numeric(18, 4), default=0)
    nexptgs = Column(Numeric(18, 4), default=0)
    nexptgd = Column(Numeric(18, 4), default=0)
    idparti = Column(Numeric(18, 4), default=0)
    ctipoparti = Column(String(5), nullable=True)
    extra_data = Column(JSON, nullable=True)


class CfDiario(DestBase):
    """
    Cabecera de asiento contable — tabla cf_diario de Contasis.
    Agrupa las líneas de cf_diariol por número de asiento.
    """
    __tablename__ = "cf_diario"

    id = Column(Integer, primary_key=True, index=True)

    # ── Control interno ──
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True, index=True)
    lote_id = Column(String(50), nullable=True, index=True)
    estado = Column(String(20), default="PENDIENTE", index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # ── Campos de Contasis cf_diario ──
    cper = Column(String(10), nullable=True, index=True)
    cmes = Column(String(5), nullable=True, index=True)
    ccodori = Column(String(10), nullable=True)
    nasiento = Column(Integer, nullable=True)
    ntc = Column(Numeric(10, 6), nullable=True, default=0)
    cglosa = Column(String(500), nullable=True)
    ccodmon = Column(String(5), nullable=True)
    cregis = Column(String(5), nullable=True)
    ncomp = Column(Integer, default=0)
    ccoddoc = Column(String(5), nullable=True)
    cserie = Column(String(20), nullable=True)
    cnumero = Column(String(20), nullable=True)
    ffechadoc = Column(String(20), nullable=True)
    ccodruc = Column(String(20), nullable=True)
    ccodenti = Column(String(20), nullable=True)
    ntot = Column(Numeric(18, 4), default=0)
    extra_data = Column(JSON, nullable=True)


class UserCatalog(DestBase):
    """
    Catálogos definidos por el usuario (ej: Plan de Cuentas, Centros de Costo).
    """
    __tablename__ = "user_catalogs"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)  # Nombre único per company?
    description = Column(String(255), nullable=True)
    columns = Column(JSON, nullable=False)  # Lista de nombres de columnas: ["Cuenta", "Descripcion"]
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    company = relationship("Company", back_populates="user_catalogs")
    items = relationship("UserCatalogItem", back_populates="catalog", cascade="all, delete-orphan")


class UserCatalogItem(DestBase):
    """
    Items de los catálogos de usuario.
    """
    __tablename__ = "user_catalog_items"

    id = Column(Integer, primary_key=True, index=True)
    catalog_id = Column(Integer, ForeignKey("user_catalogs.id"), nullable=False, index=True)
    data = Column(JSON, nullable=False)  # {"Cuenta": "101", "Descripcion": "Caja"}
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    catalog = relationship("UserCatalog", back_populates="items")


class ScheduledTask(DestBase):
    __tablename__ = "scheduled_tasks"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    task_type = Column(String(50), nullable=False) # 'TC_SUNAT', 'ETL_FULL'
    schedule_type = Column(String(20), nullable=False) # 'DAILY', 'WEEKLY', 'MONTHLY'
    time_str = Column(String(10), nullable=False) # '02:00'
    day_of_week = Column(String(20), nullable=True) # 'mon,wed,fri'
    day_of_month = Column(Integer, nullable=True) # 1, 15, 31
    params = Column(JSON, nullable=True) # {"subcategorias": [1,2], "clear_previous": true}
    is_active = Column(Boolean, default=True)
    last_run = Column(DateTime(timezone=True), nullable=True)
    next_run = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    company = relationship("Company", foreign_keys=[company_id])
    logs = relationship("TaskLog", back_populates="task", cascade="all, delete-orphan")


class TaskLog(DestBase):
    __tablename__ = "task_logs"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("scheduled_tasks.id"), nullable=False)
    status = Column(String(20), nullable=False) # 'SUCCESS', 'ERROR', 'RUNNING'
    message = Column(String, nullable=True)
    details = Column(JSON, nullable=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)

    task = relationship("ScheduledTask", back_populates="logs")


# ─── Correlativos de Asiento por Periodo ──────────────────────────────────────

class AsientoCorrelativo(DestBase):
    __tablename__ = "asiento_correlativos"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    subcategoria_id = Column(Integer, ForeignKey("mapeo_subcategorias.id"), nullable=False, index=True)
    periodo = Column(String(10), nullable=False, index=True)
    mes = Column(String(5), nullable=False, index=True)
    asiento_inicial = Column(Integer, nullable=False, default=1)
    asiento_actual = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    company = relationship("Company")



# ─── Logs de ETL en Tiempo Real ───────────────────────────────────────────────

class EtlRealtimeLog(DestBase):
    __tablename__ = "etl_realtime_logs"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    run_date = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(20), nullable=False)  # 'SUCCESS', 'WARNING', 'ERROR'
    message = Column(Text, nullable=True)
    records_extracted = Column(Integer, default=0)
    records_generated = Column(Integer, default=0)
    records_migrated = Column(Integer, default=0)
    errors = Column(JSON, nullable=True)

    company = relationship("Company")

